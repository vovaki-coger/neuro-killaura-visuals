"""
Математические утилиты
"""
import math


def wrap_angle(angle: float) -> float:
    while angle > 180.0:
        angle -= 360.0
    while angle < -180.0:
        angle += 360.0
    return angle


def distance_3d(a: tuple, b: tuple) -> float:
    dx, dy, dz = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def distance_2d(ax: float, ay: float, bx: float, by: float) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def fov_between(yaw1: float, pitch1: float, yaw2: float, pitch2: float) -> float:
    dy = wrap_angle(yaw2 - yaw1)
    dp = wrap_angle(pitch2 - pitch1)
    return math.sqrt(dy * dy + dp * dp)


def yaw_pitch_to(ox: float, oy: float, oz: float, tx: float, ty: float, tz: float) -> tuple[float, float]:
    dx = tx - ox
    dy = ty - oy
    dz = tz - oz
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(math.atan2(-dy, math.sqrt(dx * dx + dz * dz)))
    return yaw, pitch


def smoothstep(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
