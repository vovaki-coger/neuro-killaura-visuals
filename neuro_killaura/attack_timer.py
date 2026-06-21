"""
Адаптивный таймер атак — CPS с рандомизацией
"""
import time
import random
from typing import Optional


class AttackTimer:
    def __init__(self, min_cps: float = 8.0, max_cps: float = 14.0):
        self.min_cps = min_cps
        self.max_cps = max_cps
        self.last_attack_ms: float = 0.0
        self.next_interval_ms: float = 0.0
        self._schedule_next(confidence=0.5)

    def _schedule_next(self, confidence: float) -> None:
        cps = self.min_cps + (self.max_cps - self.min_cps) * max(0.0, min(1.0, confidence))
        base_interval = 1000.0 / max(cps, 0.1)
        jitter = random.uniform(-base_interval * 0.08, base_interval * 0.08)
        self.next_interval_ms = base_interval + jitter

    def should_attack(
        self,
        confidence: float,
        timing_delay_ms: float = 0.0,
        threshold: float = 0.6,
    ) -> bool:
        if confidence < threshold:
            return False
        now = time.time() * 1000.0
        elapsed = now - self.last_attack_ms
        if elapsed >= self.next_interval_ms + timing_delay_ms:
            self.last_attack_ms = now
            self._schedule_next(confidence)
            return True
        return False

    def current_cps(self, confidence: float) -> float:
        return self.min_cps + (self.max_cps - self.min_cps) * max(0.0, min(1.0, confidence))

    @property
    def time_since_last_ms(self) -> float:
        return time.time() * 1000.0 - self.last_attack_ms
