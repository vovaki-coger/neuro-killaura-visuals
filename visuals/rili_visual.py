"""
Rili Visuals — Box ESP, Tracers, Health/Armor Bars, Name ESP, Radar, Crosshair
"""
import pygame
import math
from typing import Tuple, Optional, List


def draw_corner_box(
    surface: pygame.Surface,
    x: int, y: int, w: int, h: int,
    color: Tuple[int, int, int],
    thickness: int = 2,
    corner_len: int = 10,
) -> None:
    """ESP бокс в стиле 'уголки'."""
    c = color
    t = thickness
    cl = corner_len

    pygame.draw.line(surface, c, (x, y), (x + cl, y), t)
    pygame.draw.line(surface, c, (x, y), (x, y + cl), t)
    pygame.draw.line(surface, c, (x + w, y), (x + w - cl, y), t)
    pygame.draw.line(surface, c, (x + w, y), (x + w, y + cl), t)
    pygame.draw.line(surface, c, (x, y + h), (x + cl, y + h), t)
    pygame.draw.line(surface, c, (x, y + h), (x, y + h - cl), t)
    pygame.draw.line(surface, c, (x + w, y + h), (x + w - cl, y + h), t)
    pygame.draw.line(surface, c, (x + w, y + h), (x + w, y + h - cl), t)


def draw_full_box(
    surface: pygame.Surface,
    x: int, y: int, w: int, h: int,
    color: Tuple[int, int, int],
    thickness: int = 2,
) -> None:
    pygame.draw.rect(surface, color, (x, y, w, h), thickness)


def draw_health_bar(
    surface: pygame.Surface,
    x: int, y: int, h: int,
    hp: float, max_hp: float = 20.0,
    show_text: bool = True,
    font: Optional[pygame.font.Font] = None,
) -> None:
    ratio = max(0.0, min(1.0, hp / max_hp))
    bar_w = 4
    bar_h = h

    pygame.draw.rect(surface, (30, 30, 30), (x - bar_w - 2, y, bar_w, bar_h))

    filled_h = int(bar_h * ratio)
    if ratio > 0.6:
        bar_color = (0, 220, 50)
    elif ratio > 0.3:
        bar_color = (255, 180, 0)
    else:
        bar_color = (220, 30, 30)

    pygame.draw.rect(surface, bar_color, (x - bar_w - 2, y + bar_h - filled_h, bar_w, filled_h))

    if show_text and font and int(hp) < max_hp:
        txt = font.render(str(int(hp)), True, (255, 255, 255))
        surface.blit(txt, (x - bar_w - 2 - txt.get_width() - 1, y + bar_h // 2 - txt.get_height() // 2))


def draw_armor_bar(
    surface: pygame.Surface,
    x: int, y: int, w: int,
    armor: float, max_armor: float = 20.0,
) -> None:
    ratio = max(0.0, min(1.0, armor / max_armor))
    bar_h = 3
    pygame.draw.rect(surface, (30, 30, 30), (x, y + 2, w, bar_h))
    filled_w = int(w * ratio)
    pygame.draw.rect(surface, (100, 160, 255), (x, y + 2, filled_w, bar_h))


def draw_tracer(
    surface: pygame.Surface,
    from_pos: Tuple[int, int],
    to_pos: Tuple[int, int],
    color: Tuple[int, int, int] = (255, 255, 255),
    thickness: int = 1,
) -> None:
    pygame.draw.line(surface, color, from_pos, to_pos, thickness)


def draw_name_esp(
    surface: pygame.Surface,
    x: int, y: int,
    name: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int] = (255, 255, 255),
) -> None:
    txt = font.render(name, True, color)
    surface.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() - 2))


def draw_radar(
    surface: pygame.Surface,
    center_x: int, center_y: int,
    radius: int,
    entities: List[dict],
    player_yaw: float = 0.0,
) -> None:
    bg_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(bg_surf, (0, 0, 0, 140), (radius, radius), radius)
    pygame.draw.circle(bg_surf, (255, 255, 255, 60), (radius, radius), radius, 1)
    pygame.draw.line(bg_surf, (255, 255, 255, 40), (radius, 0), (radius, radius * 2), 1)
    pygame.draw.line(bg_surf, (255, 255, 255, 40), (0, radius), (radius * 2, radius), 1)
    surface.blit(bg_surf, (center_x - radius, center_y - radius))

    pygame.draw.circle(surface, (0, 200, 0), (center_x, center_y), 4)

    for e in entities:
        rx = e.get("rel_x", 0.0)
        rz = e.get("rel_z", 0.0)
        dist = math.sqrt(rx * rx + rz * rz)
        if dist > 1e-9:
            scale = min(dist / 50.0, 1.0) * (radius - 6)
            angle = math.atan2(rx, rz) - math.radians(player_yaw)
            dot_x = center_x + int(math.sin(angle) * scale)
            dot_y = center_y - int(math.cos(angle) * scale)
            color = e.get("color", (255, 50, 50))
            pygame.draw.circle(surface, color, (dot_x, dot_y), 3)


def draw_crosshair(
    surface: pygame.Surface,
    cx: int, cy: int,
    dynamic: bool = True,
    spread: int = 0,
    color: Tuple[int, int, int] = (255, 255, 255),
    gap: int = 4,
    length: int = 8,
    thickness: int = 2,
) -> None:
    g = gap + spread
    pygame.draw.line(surface, color, (cx - g - length, cy), (cx - g, cy), thickness)
    pygame.draw.line(surface, color, (cx + g, cy), (cx + g + length, cy), thickness)
    pygame.draw.line(surface, color, (cx, cy - g - length), (cx, cy - g), thickness)
    pygame.draw.line(surface, color, (cx, cy + g), (cx, cy + g + length), thickness)
    pygame.draw.circle(surface, color, (cx, cy), 2)


class RiliVisual:
    def __init__(self):
        self.config = {
            "box_enabled": True,
            "box_color": (255, 50, 50),
            "box_style": "Corners",
            "box_thickness": 2,
            "tracers_enabled": True,
            "tracers_color": (255, 255, 255),
            "health_bar_enabled": True,
            "health_text": True,
            "armor_bar_enabled": True,
            "name_esp_enabled": True,
            "radar_enabled": True,
            "radar_size": 120,
            "crosshair_enabled": True,
            "crosshair_dynamic": True,
        }
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", 11, bold=True)
        return self._font

    def _get_small_font(self) -> pygame.font.Font:
        if self._small_font is None:
            self._small_font = pygame.font.SysFont("Arial", 9)
        return self._small_font

    def draw_entity(
        self,
        surface: pygame.Surface,
        screen_x: int, screen_y: int,
        screen_w: int, screen_h: int,
        entity: dict,
        from_pos: Tuple[int, int] = (0, 0),
    ) -> None:
        hp = entity.get("hp", 20.0)
        armor = entity.get("armor", 0.0)
        name = entity.get("name", "Entity")

        if self.config["box_enabled"]:
            col = self.config["box_color"]
            t = self.config["box_thickness"]
            if self.config["box_style"] == "Corners":
                draw_corner_box(surface, screen_x, screen_y, screen_w, screen_h, col, t)
            else:
                draw_full_box(surface, screen_x, screen_y, screen_w, screen_h, col, t)

        if self.config["health_bar_enabled"]:
            draw_health_bar(
                surface, screen_x, screen_y, screen_h, hp,
                show_text=self.config["health_text"],
                font=self._get_small_font(),
            )

        if self.config["armor_bar_enabled"] and armor > 0:
            draw_armor_bar(surface, screen_x, screen_y + screen_h + 2, screen_w, armor)

        if self.config["name_esp_enabled"]:
            draw_name_esp(surface, screen_x + screen_w // 2, screen_y, name, self._get_font())

        if self.config["tracers_enabled"]:
            target_center = (screen_x + screen_w // 2, screen_y + screen_h // 2)
            draw_tracer(surface, from_pos, target_center, self.config["tracers_color"])

    def draw_crosshair_on(self, surface: pygame.Surface, cx: int, cy: int, spread: int = 0) -> None:
        if self.config["crosshair_enabled"]:
            draw_crosshair(surface, cx, cy, self.config["crosshair_dynamic"], spread)

    def draw_radar_on(self, surface: pygame.Surface, sw: int, sh: int, entities: List[dict], player_yaw: float) -> None:
        if self.config["radar_enabled"]:
            size = self.config["radar_size"]
            draw_radar(surface, sw - size - 10, 10 + size, size, entities, player_yaw)
