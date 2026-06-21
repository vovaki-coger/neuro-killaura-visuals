"""
Извлечение 16 признаков для нейросети из состояния игры
"""
import math
import time
import numpy as np
from typing import Optional


class FeatureExtractor:
    def __init__(self):
        self.last_yaw: float = 0.0
        self.last_pitch: float = 0.0
        self.last_extract_time: float = 0.0

    def extract(
        self,
        player_pos: tuple,
        current_yaw: float,
        current_pitch: float,
        target_pos: tuple,
        target_vel: tuple,
        target_hp: float,
        target_height: float,
        range_limit: float,
        fov_limit: float,
        ping_ms: float,
        min_cps: float,
        max_cps: float,
        combo_count: int,
        last_attack_time: float,
    ) -> np.ndarray:
        px, py, pz = player_pos
        tx, ty, tz = target_pos
        vx, vy, vz = target_vel

        dx = tx - px
        dy = ty - py
        dz = tz - pz
        distance = math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-9

        yaw_to_target = math.degrees(math.atan2(-dx, dz))
        pitch_to_target = math.degrees(math.atan2(-dy, math.sqrt(dx * dx + dz * dz)))

        yaw_delta = self._wrap_angle(yaw_to_target - current_yaw)
        pitch_delta = self._wrap_angle(pitch_to_target - current_pitch)

        yaw_speed = self._wrap_angle(current_yaw - self.last_yaw)
        pitch_speed = self._wrap_angle(current_pitch - self.last_pitch)

        now = time.time() * 1000.0
        time_since_attack = (now - last_attack_time) / 1000.0

        fov_angle = abs(math.sqrt(yaw_delta ** 2 + pitch_delta ** 2))

        features = np.array([
            distance / 6.0,
            yaw_delta / 180.0,
            pitch_delta / 90.0,
            vx / 10.0,
            vy / 10.0,
            vz / 10.0,
            yaw_speed / 180.0,
            pitch_speed / 90.0,
            min(time_since_attack, 2.0) / 2.0,
            target_hp / 20.0,
            distance / max(range_limit, 0.01),
            min(fov_angle, fov_limit) / max(fov_limit, 1.0),
            min(ping_ms, 500.0) / 500.0,
            (min_cps + max_cps) / 2.0 / 20.0,
            min(combo_count, 10) / 10.0,
            target_height / 2.0,
        ], dtype=np.float32)

        self.last_yaw = current_yaw
        self.last_pitch = current_pitch
        self.last_extract_time = now

        return features

    @staticmethod
    def _wrap_angle(a: float) -> float:
        while a > 180.0:
            a -= 360.0
        while a < -180.0:
            a += 360.0
        return a
