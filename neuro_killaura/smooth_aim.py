"""
Плавный Human-like aim — ease-in-out, overshoot, hand shake
"""
import math
import time
import random
from typing import Tuple


def wrap_angle(angle: float) -> float:
    while angle > 180.0:
        angle -= 360.0
    while angle < -180.0:
        angle += 360.0
    return angle


def ease_in_out(t: float) -> float:
    """Smoothstep curve: плавный старт и конец движения."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smooth_aim(
    current_yaw: float,
    current_pitch: float,
    target_yaw: float,
    target_pitch: float,
    speed: float,
    overshoot_factor: float = 0.3,
    shake_factor: float = 0.25,
) -> Tuple[float, float]:
    """
    Рассчитывает новую позицию прицела с human-like движением.

    Args:
        current_yaw/pitch: текущий угол
        target_yaw/pitch: целевой угол
        speed: скорость движения [0..1]
        overshoot_factor: величина промаха (реализм)
        shake_factor: дрожание руки
    """
    yaw_diff = wrap_angle(target_yaw - current_yaw)
    pitch_diff = wrap_angle(target_pitch - current_pitch)

    progress = ease_in_out(speed)

    t_ms = time.time() * 1000.0
    shake_yaw = math.sin(t_ms / 50.0) * shake_factor
    shake_pitch = math.cos(t_ms / 70.0) * (shake_factor * 0.6)

    overshoot_yaw = (random.random() - 0.5) * overshoot_factor * abs(yaw_diff)
    overshoot_pitch = (random.random() - 0.5) * overshoot_factor * abs(pitch_diff) * 0.5

    new_yaw = current_yaw + yaw_diff * progress + overshoot_yaw + shake_yaw
    new_pitch = current_pitch + pitch_diff * progress + overshoot_pitch + shake_pitch
    new_pitch = max(-90.0, min(90.0, new_pitch))

    return new_yaw, new_pitch


def yaw_pitch_to_target(
    player_x: float, player_y: float, player_z: float,
    target_x: float, target_y: float, target_z: float,
) -> Tuple[float, float]:
    """Вычисляет нужный угол поворота к цели."""
    dx = target_x - player_x
    dy = target_y - player_y
    dz = target_z - player_z
    dist_xz = math.sqrt(dx * dx + dz * dz)
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(math.atan2(-dy, dist_xz))
    return yaw, pitch
