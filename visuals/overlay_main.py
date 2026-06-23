"""
Прозрачный pygame-оверлей поверх Minecraft.
- Использует Windows API (ctypes) для прозрачности и always-on-top
- Чёрный цвет = прозрачный (colorkey)
- Клики проходят насквозь (WS_EX_TRANSPARENT)
- Запускается лаунчером вместе с Minecraft
"""
import sys
import os
import json
import time
import math
import random
import threading
import ctypes

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

try:
    import pygame
except ImportError:
    print("[Overlay] pygame не установлен")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

CONFIG_PATH = os.path.join(BASE_DIR, "configs", "user.json")
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "configs", "default.json")

from visuals.pulse_visual import PulseVisual
from visuals.rili_visual import RiliVisual
from visuals.hud import HUD

# ─── Windows прозрачность ─────────────────────────────────────────────────────

def _setup_transparent_window(hwnd: int) -> None:
    """Делает pygame-окно прозрачным и always-on-top через Windows API."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        GWL_EXSTYLE       = -20
        WS_EX_LAYERED     = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW  = 0x00000080
        WS_EX_TOPMOST     = 0x00000008
        LWA_COLORKEY      = 0x00000001
        HWND_TOPMOST      = -1
        SWP_NOMOVE        = 0x0002
        SWP_NOSIZE        = 0x0001
        SWP_NOACTIVATE    = 0x0010

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW,
        )
        # Чёрный (0x000000) = полностью прозрачный
        user32.SetLayeredWindowAttributes(hwnd, 0x000000, 0, LWA_COLORKEY)
        # Всегда поверх всех окон
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        print("[Overlay] Прозрачность установлена (Windows API)")
    except Exception as e:
        print(f"[Overlay] Ошибка установки прозрачности: {e}")


# ─── Конфиг ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    for path in [CONFIG_PATH, DEFAULT_CONFIG_PATH]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


# ─── Shared state (IPC с killaura_worker через файл) ─────────────────────────

STATE_PATH = os.path.join(BASE_DIR, "configs", "runtime_state.json")

def read_runtime_state() -> dict:
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "killaura_enabled": False,
        "visuals_enabled": True,
        "hud_enabled": True,
        "cps": 0.0,
        "combo": 0,
        "target": None,
    }


# ─── Главный оверлей ─────────────────────────────────────────────────────────

class TransparentOverlay:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        info = pygame.display.Info()
        self.sw, self.sh = info.current_w, info.current_h

        # NOFRAME — без рамки; не указываем SRCALPHA (colorkey справится)
        self.screen = pygame.display.set_mode(
            (self.sw, self.sh),
            pygame.NOFRAME | pygame.HWSURFACE | pygame.DOUBLEBUF,
        )
        pygame.display.set_caption("NK Overlay")

        # Установить прозрачность через Windows API
        wm = pygame.display.get_wm_info()
        hwnd = wm.get("window", 0)
        if hwnd:
            _setup_transparent_window(hwnd)

        self.clock = pygame.time.Clock()
        self.cfg = load_config()

        self.pulse = PulseVisual()
        self.rili  = RiliVisual()
        self.hud   = HUD()
        self._apply_config()

        # Демо-сущности (в реальной версии заменяются данными из memory/IPC)
        self.entities = self._make_demo_entities()

        self.running        = True
        self._visuals_on    = True
        self._hud_on        = True
        self._cps           = 0.0
        self._combo         = 0
        self._confidence    = 0.87

        # Поток: слушаем runtime_state от killaura_worker
        self._state_thread = threading.Thread(target=self._state_watcher, daemon=True)
        self._state_thread.start()

        # Поток: перечитываем конфиг при изменении
        self._cfg_mtime = 0.0
        self._cfg_thread = threading.Thread(target=self._config_watcher, daemon=True)
        self._cfg_thread.start()

        # Глобальные хоткеи через pynput
        self._setup_hotkeys()

    # ── Конфиг ────────────────────────────────────────────────────────────────

    def _apply_config(self) -> None:
        v = self.cfg.get("visuals", {})
        h = self.cfg.get("hud", {})

        self.pulse.config.update({
            "enabled":  v.get("pulse_enabled", True),
            "color":    tuple(v.get("pulse_color", [255, 50, 50])),
            "speed":    v.get("pulse_speed", 1.5),
            "size":     v.get("pulse_size", 40),
            "opacity":  v.get("pulse_opacity", 180),
        })
        self.rili.config.update({
            "box_enabled":        v.get("box_enabled", True),
            "box_color":          tuple(v.get("box_color", [255, 50, 50])),
            "box_style":          v.get("box_style", "Corners"),
            "box_thickness":      v.get("box_thickness", 2),
            "tracers_enabled":    v.get("tracers_enabled", True),
            "health_bar_enabled": v.get("health_bar_enabled", True),
            "name_esp_enabled":   v.get("name_esp_enabled", True),
            "radar_enabled":      v.get("radar_enabled", True),
            "radar_size":         v.get("radar_size", 120),
            "crosshair_enabled":  v.get("crosshair_enabled", True),
        })
        self.hud.config.update({
            "enabled":      h.get("enabled", True),
            "target_info":  h.get("target_info", True),
            "cps_graph":    h.get("cps_graph", True),
            "combo":        h.get("combo", True),
            "watermark":    h.get("watermark", True),
            "keybinds":     h.get("keybinds", True),
        })

    def _config_watcher(self) -> None:
        while self.running:
            for path in [CONFIG_PATH, DEFAULT_CONFIG_PATH]:
                if os.path.exists(path):
                    try:
                        mtime = os.path.getmtime(path)
                        if mtime != self._cfg_mtime:
                            self._cfg_mtime = mtime
                            with open(path) as f:
                                self.cfg = json.load(f)
                            self._apply_config()
                    except Exception:
                        pass
                    break
            time.sleep(1.0)

    # ── State watcher (данные от killaura_worker) ─────────────────────────────

    def _state_watcher(self) -> None:
        while self.running:
            state = read_runtime_state()
            self._visuals_on  = state.get("visuals_enabled", True)
            self._hud_on      = state.get("hud_enabled", True)
            self._cps         = float(state.get("cps", 0.0))
            self._combo       = int(state.get("combo", 0))
            self._confidence  = float(state.get("confidence", 0.87))
            time.sleep(0.1)

    # ── Хоткеи ────────────────────────────────────────────────────────────────

    def _setup_hotkeys(self) -> None:
        try:
            from pynput.keyboard import Key, Listener
            def on_press(key):
                try:
                    ch = getattr(key, "char", None)
                    if ch == "g":
                        self._visuals_on = not self._visuals_on
                    elif ch == "h":
                        self._hud_on = not self._hud_on
                    elif key == Key.esc:
                        self.running = False
                except Exception:
                    pass
            listener = Listener(on_press=on_press)
            listener.daemon = True
            listener.start()
        except Exception as e:
            print(f"[Overlay] Хоткеи недоступны: {e}")

    # ── Демо-сущности ─────────────────────────────────────────────────────────

    def _make_demo_entities(self) -> list:
        entities = []
        for i in range(3):
            entities.append({
                "name":  f"Player{i + 1}",
                "hp":    random.uniform(8.0, 20.0),
                "armor": random.uniform(0, 20.0),
                "x":     random.uniform(0.25, 0.75),
                "y":     random.uniform(0.20, 0.65),
                "w":     0.04,
                "h":     0.12,
                "vx":    random.uniform(-0.0008, 0.0008),
                "vy":    random.uniform(-0.0004, 0.0004),
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
            e["hp"] = max(1.0, e["hp"] - random.uniform(0, 0.03))
            if random.random() < 0.015:
                sx = int(e["x"] * self.sw)
                sy = int(e["y"] * self.sh)
                self.pulse.on_hit(sx, sy)
                self._combo = min(self._combo + 1, 20)

    # ── Главный цикл ──────────────────────────────────────────────────────────

    def run(self) -> None:
        BLACK = (0, 0, 0)   # прозрачный цвет (colorkey)
        from_pos = (self.sw // 2, self.sh)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_g:
                        self._visuals_on = not self._visuals_on
                    elif event.key == pygame.K_h:
                        self._hud_on = not self._hud_on

            # Заливаем чёрным (= прозрачный через colorkey)
            self.screen.fill(BLACK)

            if self._visuals_on:
                self._update_entities()
                self.pulse.update()

                for e in self.entities:
                    sx = int(e["x"] * self.sw)
                    sy = int(e["y"] * self.sh)
                    sw_e = int(e["w"] * self.sw)
                    sh_e = int(e["h"] * self.sh)
                    self.rili.draw_entity(self.screen, sx, sy, sw_e, sh_e, e, from_pos)
                    self.pulse.draw(self.screen, (sx + sw_e // 2, sy + sh_e // 2),
                                    self._confidence)

                self.rili.draw_radar_on(self.screen, self.sw, self.sh, self.entities, 0.0)
                self.rili.draw_crosshair_on(self.screen, self.sw // 2, self.sh // 2)

            if self._hud_on:
                target = self.entities[0] if self.entities else None
                self.hud.update(self._cps, self._combo)
                self.hud.draw(
                    self.screen, self.sw, self.sh,
                    target_name=target["name"] if target else None,
                    target_hp=target["hp"] if target else 0.0,
                    target_dist=3.2,
                    confidence=self._confidence,
                    cps=self._cps,
                    combo=self._combo,
                    keybinds={"KillAura": "R", "Visuals": "G", "HUD": "H", "Menu": "INSERT"},
                )

            pygame.display.flip()
            self.clock.tick(240)

        pygame.quit()


if __name__ == "__main__":
    overlay = TransparentOverlay()
    overlay.run()
