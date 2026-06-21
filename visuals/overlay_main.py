"""
Pygame-оверлей — отдельный процесс поверх экрана
Запускается лаунчером через subprocess, читает config.json
"""
import sys
import os
import json
import time
import math
import random
import threading

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

try:
    import pygame
except ImportError:
    print("[Overlay] pygame не установлен. pip install pygame")
    sys.exit(1)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "user.json")
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "default.json")

from visuals.pulse_visual import PulseVisual, Particle
from visuals.rili_visual import RiliVisual, draw_crosshair
from visuals.hud import HUD


def load_config() -> dict:
    for path in [CONFIG_PATH, DEFAULT_CONFIG_PATH]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


class DemoOverlay:
    """
    Демо-оверлей с анимированными сущностями и визуальными эффектами.
    В реальной сборке подключается к памяти Minecraft.
    """

    def __init__(self):
        pygame.init()

        info = pygame.display.Info()
        self.sw, self.sh = info.current_w, info.current_h

        self.screen = pygame.display.set_mode(
            (self.sw, self.sh),
            pygame.NOFRAME | pygame.SRCALPHA,
        )
        pygame.display.set_caption("Neuro KillAura Overlay")

        self.clock = pygame.Clock()
        self.cfg = load_config()
        self.cfg_mtime = 0.0

        self.pulse = PulseVisual()
        self.rili = RiliVisual()
        self.hud = HUD()

        self._apply_config()

        self.entities = self._make_demo_entities()
        self.cps = 10.0
        self.combo = 0
        self.confidence = 0.85
        self.running = True
        self._cfg_thread = threading.Thread(target=self._config_watcher, daemon=True)
        self._cfg_thread.start()

    def _apply_config(self) -> None:
        v = self.cfg.get("visuals", {})
        h = self.cfg.get("hud", {})

        self.pulse.config["enabled"] = v.get("pulse_enabled", True)
        self.pulse.config["color"] = tuple(v.get("pulse_color", [255, 50, 50]))
        self.pulse.config["speed"] = v.get("pulse_speed", 1.5)
        self.pulse.config["size"] = v.get("pulse_size", 40)
        self.pulse.config["opacity"] = v.get("pulse_opacity", 180)

        self.rili.config["box_enabled"] = v.get("box_enabled", True)
        self.rili.config["box_color"] = tuple(v.get("box_color", [255, 50, 50]))
        self.rili.config["box_style"] = v.get("box_style", "Corners")
        self.rili.config["box_thickness"] = v.get("box_thickness", 2)
        self.rili.config["tracers_enabled"] = v.get("tracers_enabled", True)
        self.rili.config["health_bar_enabled"] = v.get("health_bar_enabled", True)
        self.rili.config["name_esp_enabled"] = v.get("name_esp_enabled", True)
        self.rili.config["radar_enabled"] = v.get("radar_enabled", True)
        self.rili.config["radar_size"] = v.get("radar_size", 120)
        self.rili.config["crosshair_enabled"] = v.get("crosshair_enabled", True)

        self.hud.config["enabled"] = h.get("enabled", True)
        self.hud.config["target_info"] = h.get("target_info", True)
        self.hud.config["cps_graph"] = h.get("cps_graph", True)
        self.hud.config["combo"] = h.get("combo", True)
        self.hud.config["watermark"] = h.get("watermark", True)
        self.hud.config["keybinds"] = h.get("keybinds", True)

    def _config_watcher(self) -> None:
        while self.running:
            for path in [CONFIG_PATH, DEFAULT_CONFIG_PATH]:
                if os.path.exists(path):
                    try:
                        mtime = os.path.getmtime(path)
                        if mtime != self.cfg_mtime:
                            self.cfg_mtime = mtime
                            with open(path) as f:
                                self.cfg = json.load(f)
                            self._apply_config()
                    except Exception:
                        pass
                    break
            time.sleep(0.5)

    def _make_demo_entities(self) -> list:
        entities = []
        for i in range(3):
            entities.append({
                "name": f"Player{i + 1}",
                "hp": random.uniform(8.0, 20.0),
                "armor": random.uniform(0, 20.0),
                "x": random.uniform(0.2, 0.8),
                "y": random.uniform(0.2, 0.7),
                "w": 0.04,
                "h": 0.12,
                "vx": random.uniform(-0.001, 0.001),
                "vy": random.uniform(-0.0005, 0.0005),
                "rel_x": random.uniform(-20, 20),
                "rel_z": random.uniform(-20, 20),
            })
        return entities

    def _update_entities(self) -> None:
        for e in self.entities:
            e["x"] = max(0.1, min(0.9, e["x"] + e["vx"]))
            e["y"] = max(0.1, min(0.8, e["y"] + e["vy"]))
            if random.random() < 0.005:
                e["vx"] *= -1
            if random.random() < 0.005:
                e["vy"] *= -1
            e["hp"] = max(1.0, e["hp"] - random.uniform(0, 0.05))
            if random.random() < 0.01:
                ex = int(e["x"] * self.sw)
                ey = int(e["y"] * self.sh)
                self.pulse.on_hit(ex, ey)
                self.combo = min(self.combo + 1, 20)

    def run(self) -> None:
        try:
            pynput = __import__("pynput.keyboard", fromlist=["Key", "Listener"])
            def on_press(key):
                try:
                    if hasattr(key, "char") and key.char == "g":
                        enabled = not self.rili.config["box_enabled"]
                        self.rili.config["box_enabled"] = enabled
                        self.pulse.config["enabled"] = enabled
                except Exception:
                    pass
                try:
                    from pynput.keyboard import Key
                    if key == Key.esc:
                        self.running = False
                except Exception:
                    pass
            listener = pynput.Listener(on_press=on_press)
            listener.start()
        except Exception:
            pass

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.screen.fill((0, 0, 0, 0))

            self._update_entities()
            self.pulse.update()

            from_pos = (self.sw // 2, self.sh)
            for e in self.entities:
                sx = int(e["x"] * self.sw)
                sy = int(e["y"] * self.sh)
                sw_e = int(e["w"] * self.sw)
                sh_e = int(e["h"] * self.sh)
                self.rili.draw_entity(self.screen, sx, sy, sw_e, sh_e, e, from_pos)
                self.pulse.draw(self.screen, (sx + sw_e // 2, sy + sh_e // 2), self.confidence)

            self.rili.draw_radar_on(self.screen, self.sw, self.sh, self.entities, 0.0)
            self.rili.draw_crosshair_on(self.screen, self.sw // 2, self.sh // 2)

            target = self.entities[0] if self.entities else None
            self.hud.update(self.cps, self.combo)
            self.hud.draw(
                self.screen, self.sw, self.sh,
                target_name=target["name"] if target else None,
                target_hp=target["hp"] if target else 0.0,
                target_dist=3.2,
                confidence=self.confidence,
                cps=self.cps,
                combo=self.combo,
                keybinds={"KillAura": "R", "Visuals": "G", "HUD": "H", "Menu": "INSERT"},
            )

            pygame.display.flip()
            self.clock.tick(240)

        pygame.quit()


if __name__ == "__main__":
    overlay = DemoOverlay()
    overlay.run()
