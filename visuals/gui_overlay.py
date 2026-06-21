"""
GUI Overlay — ImGui-style окна поверх игры
Используется вместе с pygame оверлеем
"""
import pygame
import time
from typing import Optional, Tuple, Callable


class ImGui:
    """Минимальный ImGui-style renderer на pygame."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self._font = pygame.font.SysFont("Consolas", 13, bold=True)
        self._small = pygame.font.SysFont("Consolas", 11)
        self._cursor_x = 0
        self._cursor_y = 0
        self._window_x = 0
        self._window_y = 0
        self._window_w = 0
        self._padding = 10

    def begin_window(self, title: str, x: int, y: int, w: int = 260, alpha: int = 210) -> None:
        self._window_x = x
        self._window_y = y
        self._window_w = w
        self._cursor_x = x + self._padding
        self._cursor_y = y + 30

        bg = pygame.Surface((w, 500), pygame.SRCALPHA)
        bg.fill((15, 15, 20, alpha))
        self.surface.blit(bg, (x, y))

        pygame.draw.rect(self.surface, (229, 57, 53), (x, y, w, 24), 0, border_radius=4)
        title_surf = self._font.render(f"  {title}", True, (255, 255, 255))
        self.surface.blit(title_surf, (x + 4, y + 4))
        pygame.draw.rect(self.surface, (40, 40, 50), (x, y + 24, w, 1))

    def checkbox(self, label: str, value: bool) -> bool:
        x, y = self._cursor_x, self._cursor_y
        box_size = 14
        color = (229, 57, 53) if value else (60, 60, 70)
        pygame.draw.rect(self.surface, color, (x, y, box_size, box_size), border_radius=2)
        if value:
            pygame.draw.line(self.surface, (255, 255, 255), (x + 2, y + 7), (x + 6, y + 11), 2)
            pygame.draw.line(self.surface, (255, 255, 255), (x + 6, y + 11), (x + 12, y + 3), 2)
        lbl = self._small.render(label, True, (200, 200, 200))
        self.surface.blit(lbl, (x + box_size + 6, y + 1))
        self._cursor_y += 20
        return value

    def slider(self, label: str, value: float, min_val: float, max_val: float, w: int = 140) -> float:
        x, y = self._cursor_x, self._cursor_y
        lbl = self._small.render(label, True, (160, 160, 160))
        self.surface.blit(lbl, (x, y))
        bar_y = y + 16
        pygame.draw.rect(self.surface, (40, 40, 50), (x, bar_y, w, 6), border_radius=3)
        ratio = (value - min_val) / max(max_val - min_val, 1e-9)
        filled = int(w * ratio)
        pygame.draw.rect(self.surface, (229, 57, 53), (x, bar_y, filled, 6), border_radius=3)
        knob_x = x + filled
        pygame.draw.circle(self.surface, (255, 255, 255), (knob_x, bar_y + 3), 5)
        val_lbl = self._small.render(f"{value:.2f}", True, (180, 180, 180))
        self.surface.blit(val_lbl, (x + w + 6, bar_y - 2))
        self._cursor_y += 32
        return value

    def label(self, text: str, color: Tuple[int, int, int] = (200, 200, 200)) -> None:
        lbl = self._small.render(text, True, color)
        self.surface.blit(lbl, (self._cursor_x, self._cursor_y))
        self._cursor_y += 18

    def separator(self) -> None:
        pygame.draw.line(
            self.surface, (40, 40, 50),
            (self._window_x, self._cursor_y),
            (self._window_x + self._window_w, self._cursor_y), 1
        )
        self._cursor_y += 8

    def end_window(self) -> None:
        h = self._cursor_y - self._window_y + self._padding
        pygame.draw.rect(self.surface, (229, 57, 53),
                         (self._window_x, self._window_y, self._window_w, h), 1, border_radius=4)
