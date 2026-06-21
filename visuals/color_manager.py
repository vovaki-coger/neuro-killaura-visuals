"""
Менеджер цветов — конвертация, пресеты
"""
from typing import Tuple

PRESETS = {
    "red":    (229, 57, 53),
    "blue":   (33, 150, 243),
    "green":  (76, 175, 80),
    "yellow": (255, 193, 7),
    "purple": (156, 39, 176),
    "cyan":   (0, 188, 212),
    "white":  (255, 255, 255),
    "orange": (255, 152, 0),
}


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def blend(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def health_color(hp: float, max_hp: float = 20.0) -> Tuple[int, int, int]:
    ratio = max(0.0, min(1.0, hp / max_hp))
    if ratio > 0.6:
        return blend((255, 200, 0), (0, 220, 50), (ratio - 0.6) / 0.4)
    else:
        return blend((220, 30, 30), (255, 200, 0), ratio / 0.6)
