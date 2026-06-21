"""
Анти-детект — случайные паузы, reset combo, humanization
"""
import time
import random
import threading


class AntiDetect:
    def __init__(self):
        self._misclick_chance = 0.02
        self._pause_chance = 0.005
        self._pause_duration = (0.05, 0.25)
        self._active = True
        self._pausing = False

    def should_misclick(self) -> bool:
        return self._active and random.random() < self._misclick_chance

    def maybe_pause(self) -> None:
        if self._active and not self._pausing and random.random() < self._pause_chance:
            duration = random.uniform(*self._pause_duration)
            self._pausing = True
            t = threading.Thread(target=self._do_pause, args=(duration,), daemon=True)
            t.start()

    def _do_pause(self, duration: float) -> None:
        time.sleep(duration)
        self._pausing = False

    def is_pausing(self) -> bool:
        return self._pausing

    def randomize_rotation_noise(self, yaw: float, pitch: float) -> tuple[float, float]:
        if not self._active:
            return yaw, pitch
        noise_yaw = random.gauss(0, 0.05)
        noise_pitch = random.gauss(0, 0.03)
        return yaw + noise_yaw, pitch + noise_pitch
