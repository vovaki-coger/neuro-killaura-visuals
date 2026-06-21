"""
Pulse Visuals — пульсирующие круги, частицы, glow-эффекты
Рисует поверх pygame surface (оверлей поверх экрана)
"""
import pygame
import math
import time
import random
from typing import List, Tuple, Optional


class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.0, 3.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.03, 0.07)
        self.size = random.randint(2, 5)
        self.color = color

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int(self.life * 255)
        r, g, b = self.color
        size = max(1, int(self.size * self.life))
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), size)


class HitWave:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.radius = 5.0
        self.max_radius = 60.0
        self.life = 1.0
        self.decay = 0.05
        self.color = color

    def update(self) -> bool:
        self.radius += 3.5
        self.life -= self.decay
        return self.life > 0 and self.radius < self.max_radius

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, int(self.life * 180))
        r, g, b = self.color
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), int(self.radius), 2)


class PulseVisual:
    def __init__(self):
        self.particles: List[Particle] = []
        self.waves: List[HitWave] = []
        self.config = {
            "enabled": True,
            "color": (255, 50, 50),
            "speed": 1.5,
            "size": 40,
            "opacity": 180,
        }

    def on_hit(self, screen_x: float, screen_y: float) -> None:
        """Вызывается при нанесении удара."""
        color = self.config["color"]
        for _ in range(12):
            self.particles.append(Particle(screen_x, screen_y, color))
        self.waves.append(HitWave(screen_x, screen_y, color))

    def update(self) -> None:
        self.particles = [p for p in self.particles if p.update()]
        self.waves = [w for w in self.waves if w.update()]

    def draw(
        self,
        surface: pygame.Surface,
        target_screen_pos: Optional[Tuple[float, float]],
        confidence: float = 1.0,
    ) -> None:
        if not self.config["enabled"]:
            return

        if target_screen_pos:
            self._draw_pulse_ring(surface, target_screen_pos, confidence)

        for wave in self.waves:
            wave.draw(surface)

        for particle in self.particles:
            particle.draw(surface)

    def _draw_pulse_ring(
        self,
        surface: pygame.Surface,
        pos: Tuple[float, float],
        confidence: float,
    ) -> None:
        t = time.time()
        speed = self.config["speed"]
        base_size = self.config["size"]
        color = self.config["color"]
        opacity = self.config["opacity"]

        for i in range(3):
            phase = (t * speed + i * 0.4) % 1.0
            radius = int(base_size * (0.5 + phase * 0.8))
            alpha = int(opacity * (1.0 - phase) * confidence)
            if alpha < 5:
                continue
            try:
                ring_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                r, g, b = color
                pygame.draw.circle(ring_surf, (r, g, b, alpha), (radius + 2, radius + 2), radius, 2)
                surface.blit(ring_surf, (pos[0] - radius - 2, pos[1] - radius - 2))
            except Exception:
                pass

    def draw_preview(self, canvas: "tk.Canvas", cx: float, cy: float) -> None:
        """Рисует превью на tkinter Canvas (для GUI лаунчера)."""
        import tkinter as tk
        t = time.time()
        color = self.config["color"]
        speed = self.config["speed"]
        size = self.config["size"]

        hex_color = "#{:02x}{:02x}{:02x}".format(*color)

        for i in range(3):
            phase = (t * speed + i * 0.4) % 1.0
            r = size * (0.5 + phase * 0.8)
            alpha_frac = 1.0 - phase
            darker = tuple(int(c * alpha_frac * 0.8) for c in color)
            hex_d = "#{:02x}{:02x}{:02x}".format(*darker)
            try:
                canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    outline=hex_d, width=2
                )
            except Exception:
                pass

        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=hex_color, outline="")
