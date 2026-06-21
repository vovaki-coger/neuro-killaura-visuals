"""
Основной модуль KillAura — координирует нейросеть, aim, атаки и визуалы
"""
import time
import threading
import math
import random
import numpy as np
from typing import Optional, List, Callable

from neuro_killaura.neural_net import NeuralPredictor
from neuro_killaura.smooth_aim import smooth_aim, yaw_pitch_to_target, wrap_angle
from neuro_killaura.feature_extractor import FeatureExtractor
from neuro_killaura.attack_timer import AttackTimer
from neuro_killaura.anti_detect import AntiDetect
from utils.input_simulator import click_left, move_mouse
from utils.math_utils import fov_between, distance_3d


class Entity:
    """Представление игрока/моба из памяти/API игры."""

    def __init__(self, name: str, x: float, y: float, z: float,
                 hp: float = 20.0, armor: float = 0.0, height: float = 1.8):
        self.name = name
        self.x, self.y, self.z = x, y, z
        self.hp = hp
        self.armor = armor
        self.height = height
        self.vel_x = self.vel_y = self.vel_z = 0.0
        self.screen_x = self.screen_y = 0
        self.screen_w = self.screen_h = 0

    @property
    def pos(self) -> tuple:
        return (self.x, self.y, self.z)

    @property
    def velocity(self) -> tuple:
        return (self.vel_x, self.vel_y, self.vel_z)

    @property
    def screen_pos(self) -> tuple:
        return (self.screen_x, self.screen_y)


class NeuroKillAura:
    def __init__(
        self,
        config: dict,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.cfg = config.get("killaura", {})
        self.log = log_callback or print

        self.range = self.cfg.get("range", 3.5)
        self.fov = self.cfg.get("fov", 120.0)
        self.min_cps = self.cfg.get("min_cps", 8.0)
        self.max_cps = self.cfg.get("max_cps", 14.0)
        self.smooth = self.cfg.get("smooth", 0.15)

        self.enabled = False
        self.target: Optional[Entity] = None
        self.combo = 0
        self.current_cps = 0.0
        self.confidence = 0.0

        self.player_pos = (0.0, 0.0, 0.0)
        self.player_yaw = 0.0
        self.player_pitch = 0.0
        self.ping_ms = 20.0

        self._predictor = NeuralPredictor()
        self._extractor = FeatureExtractor()
        self._timer = AttackTimer(self.min_cps, self.max_cps)
        self._anti_detect = AntiDetect()

        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.log(f"[KillAura] Инициализирован. Устройство: {self._predictor.device_name}")

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log("[KillAura] Запущен")

    def stop(self) -> None:
        self._running = False
        self.target = None
        self.log("[KillAura] Остановлен")

    def update_entities(self, entities: List[Entity]) -> None:
        with self._lock:
            self._entities = entities

    def update_player(self, pos: tuple, yaw: float, pitch: float, ping: float = 20.0) -> None:
        self.player_pos = pos
        self.player_yaw = yaw
        self.player_pitch = pitch
        self.ping_ms = ping

    def _loop(self) -> None:
        while self._running:
            if self.enabled:
                try:
                    with self._lock:
                        entities = list(getattr(self, "_entities", []))
                    self._tick(entities)
                except Exception as e:
                    self.log(f"[KillAura] Ошибка: {e}")
            time.sleep(1.0 / 240.0)

    def _tick(self, entities: List[Entity]) -> None:
        target = self._select_target(entities)
        self.target = target

        if target is None:
            self.combo = 0
            return

        features = self._extractor.extract(
            player_pos=self.player_pos,
            current_yaw=self.player_yaw,
            current_pitch=self.player_pitch,
            target_pos=target.pos,
            target_vel=target.velocity,
            target_hp=target.hp,
            target_height=target.height,
            range_limit=self.range,
            fov_limit=self.fov,
            ping_ms=self.ping_ms,
            min_cps=self.min_cps,
            max_cps=self.max_cps,
            combo_count=self.combo,
            last_attack_time=self._timer.last_attack_ms,
        )

        yaw_corr, pitch_corr = self._predictor.get_aim_correction(features)
        self.confidence = self._predictor.score_target(features)
        timing_delay = self._predictor.get_timing_delay_ms(features)

        if self._anti_detect.is_pausing():
            return

        target_yaw = self.player_yaw + yaw_corr
        target_pitch = self.player_pitch + pitch_corr

        new_yaw, new_pitch = smooth_aim(
            self.player_yaw, self.player_pitch,
            target_yaw, target_pitch,
            self.smooth,
        )
        new_yaw, new_pitch = self._anti_detect.randomize_rotation_noise(new_yaw, new_pitch)

        dy = int((new_yaw - self.player_yaw) * 8.0)
        dp = int((new_pitch - self.player_pitch) * 8.0)
        if abs(dy) > 0 or abs(dp) > 0:
            move_mouse(dy, dp)

        self.player_yaw = new_yaw
        self.player_pitch = new_pitch

        self.current_cps = self._timer.current_cps(self.confidence)

        if self._timer.should_attack(self.confidence, timing_delay):
            if not self._anti_detect.should_misclick():
                click_left()
                self.combo += 1

        self._anti_detect.maybe_pause()

    def _select_target(self, entities: List[Entity]) -> Optional[Entity]:
        candidates = []
        for e in entities:
            dist = distance_3d(self.player_pos, e.pos)
            if dist > self.range:
                continue
            if e.hp <= 0:
                continue
            target_yaw, target_pitch = yaw_pitch_to_target(
                *self.player_pos, *e.pos
            )
            fov_angle = fov_between(self.player_yaw, self.player_pitch, target_yaw, target_pitch)
            if fov_angle > self.fov / 2.0:
                continue

            features = self._extractor.extract(
                player_pos=self.player_pos,
                current_yaw=self.player_yaw,
                current_pitch=self.player_pitch,
                target_pos=e.pos,
                target_vel=e.velocity,
                target_hp=e.hp,
                target_height=e.height,
                range_limit=self.range,
                fov_limit=self.fov,
                ping_ms=self.ping_ms,
                min_cps=self.min_cps,
                max_cps=self.max_cps,
                combo_count=self.combo,
                last_attack_time=self._timer.last_attack_ms,
            )
            score = self._predictor.score_target(features)
            candidates.append((e, score))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def get_status(self) -> dict:
        info = self._predictor.get_model_info()
        return {
            "enabled": self.enabled,
            "target": self.target.name if self.target else None,
            "confidence": self.confidence,
            "cps": self.current_cps,
            "combo": self.combo,
            "device": info["device"],
            "model_arch": info["architecture"],
            "model_params": info["parameters"],
        }
