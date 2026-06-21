"""
HUD — информация о цели, CPS-график, combo-анимация, watermark, keybinds
"""
import pygame
import time
import math
from typing import Optional, List, Tuple, Dict


class HUD:
    def __init__(self):
        self.config = {
            "enabled": True,
            "target_info": True,
            "cps_graph": True,
            "combo": True,
            "watermark": True,
            "keybinds": True,
        }
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        self._big_font: Optional[pygame.font.Font] = None
        self._cps_history: List[float] = []
        self._combo_anim_t: float = 0.0
        self._last_combo: int = 0

    def _f(self) -> pygame.font.Font:
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", 13, bold=True)
        return self._font

    def _sf(self) -> pygame.font.Font:
        if not self._small_font:
            self._small_font = pygame.font.SysFont("Consolas", 11)
        return self._small_font

    def _bf(self) -> pygame.font.Font:
        if not self._big_font:
            self._big_font = pygame.font.SysFont("Consolas", 22, bold=True)
        return self._big_font

    def update(self, cps: float, combo: int) -> None:
        self._cps_history.append(cps)
        if len(self._cps_history) > 60:
            self._cps_history.pop(0)
        if combo != self._last_combo and combo > 0:
            self._combo_anim_t = time.time()
        self._last_combo = combo

    def draw(
        self,
        surface: pygame.Surface,
        sw: int, sh: int,
        target_name: Optional[str] = None,
        target_hp: float = 0.0,
        target_dist: float = 0.0,
        confidence: float = 0.0,
        cps: float = 0.0,
        combo: int = 0,
        keybinds: Optional[Dict[str, str]] = None,
    ) -> None:
        if not self.config["enabled"]:
            return

        if self.config["watermark"]:
            self._draw_watermark(surface)

        if self.config["target_info"] and target_name:
            self._draw_target_info(surface, target_name, target_hp, target_dist, confidence)

        if self.config["cps_graph"]:
            self._draw_cps_graph(surface, sw, sh, cps)

        if self.config["combo"] and combo > 0:
            self._draw_combo(surface, sw, sh, combo)

        if self.config["keybinds"] and keybinds:
            self._draw_keybinds(surface, sh, keybinds)

    def _draw_watermark(self, surface: pygame.Surface) -> None:
        t = time.time()
        pulse = 0.7 + 0.3 * math.sin(t * 2.0)
        r = int(229 * pulse)
        g = int(57 * pulse)
        b = int(53 * pulse)
        wm = self._f().render("⚡ Neuro KillAura v2.0", True, (r, g, b))
        surface.blit(wm, (8, 8))
        sub = self._sf().render("github.com/vovaki-coger/neuro-killaura-visuals", True, (100, 100, 100))
        surface.blit(sub, (8, 26))

    def _draw_target_info(
        self,
        surface: pygame.Surface,
        name: str, hp: float, dist: float, conf: float,
    ) -> None:
        x, y = 8, 50
        bg = pygame.Surface((200, 70), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (x - 4, y - 4))

        lines = [
            (f"Target: {name}", (255, 255, 255)),
            (f"HP:     {hp:.1f}/20", (0, 220, 60) if hp > 10 else (255, 80, 80)),
            (f"Dist:   {dist:.1f}m", (180, 180, 255)),
            (f"Conf:   {conf * 100:.0f}%", (255, 200, 50)),
        ]
        for i, (text, color) in enumerate(lines):
            surf = self._sf().render(text, True, color)
            surface.blit(surf, (x, y + i * 16))

    def _draw_cps_graph(self, surface: pygame.Surface, sw: int, sh: int, cps: float) -> None:
        gw, gh = 120, 40
        gx = sw - gw - 8
        gy = sh - gh - 40

        bg = pygame.Surface((gw, gh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (gx, gy))

        label = self._sf().render(f"CPS: {cps:.1f}", True, (200, 200, 200))
        surface.blit(label, (gx, gy - 14))

        if len(self._cps_history) > 1:
            max_cps = max(self._cps_history + [14.0])
            pts = []
            for i, v in enumerate(self._cps_history):
                px = gx + int(i / max(len(self._cps_history) - 1, 1) * gw)
                py = gy + gh - int(v / max_cps * gh)
                pts.append((px, py))
            if len(pts) > 1:
                pygame.draw.lines(surface, (229, 57, 53), False, pts, 2)

    def _draw_combo(self, surface: pygame.Surface, sw: int, sh: int, combo: int) -> None:
        t = time.time()
        elapsed = t - self._combo_anim_t
        scale = max(1.0, 1.5 - elapsed * 2.0)

        alpha = min(255, int(255 * (1.0 - max(0.0, elapsed - 2.0))))
        if alpha <= 0:
            return

        cx = sw // 2
        cy = sh // 2 - 60

        glow = self._bf().render(f"x{combo}", True, (229, 57, 53))
        surface.blit(glow, (cx - glow.get_width() // 2, cy))
        label = self._sf().render("COMBO", True, (255, 200, 50))
        surface.blit(label, (cx - label.get_width() // 2, cy + 28))

    def _draw_keybinds(self, surface: pygame.Surface, sh: int, keybinds: Dict[str, str]) -> None:
        x, y = 8, sh - 80
        for action, key in keybinds.items():
            line = self._sf().render(f"[{key.upper()}] {action}", True, (120, 120, 120))
            surface.blit(line, (x, y))
            y += 14
