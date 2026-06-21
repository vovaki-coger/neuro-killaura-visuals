"""
Выбор цели — score-based сортировка через нейросеть
"""
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from neuro_killaura.aimbot import Entity
    from neuro_killaura.neural_net import NeuralPredictor
    from neuro_killaura.feature_extractor import FeatureExtractor

from utils.math_utils import distance_3d, fov_between
from neuro_killaura.smooth_aim import yaw_pitch_to_target


class TargetSelector:
    def __init__(
        self,
        predictor: "NeuralPredictor",
        extractor: "FeatureExtractor",
        range_limit: float = 3.5,
        fov_limit: float = 120.0,
    ):
        self.predictor = predictor
        self.extractor = extractor
        self.range = range_limit
        self.fov = fov_limit

    def select(
        self,
        entities: "List[Entity]",
        player_pos: tuple,
        player_yaw: float,
        player_pitch: float,
        ping_ms: float,
        min_cps: float,
        max_cps: float,
        combo: int,
        last_attack_ms: float,
    ) -> Optional["Entity"]:
        candidates = []
        for e in entities:
            if e.hp <= 0:
                continue
            dist = distance_3d(player_pos, e.pos)
            if dist > self.range:
                continue
            ty, tp = yaw_pitch_to_target(*player_pos, *e.pos)
            fov_angle = fov_between(player_yaw, player_pitch, ty, tp)
            if fov_angle > self.fov / 2.0:
                continue

            features = self.extractor.extract(
                player_pos=player_pos,
                current_yaw=player_yaw,
                current_pitch=player_pitch,
                target_pos=e.pos,
                target_vel=e.velocity,
                target_hp=e.hp,
                target_height=e.height,
                range_limit=self.range,
                fov_limit=self.fov,
                ping_ms=ping_ms,
                min_cps=min_cps,
                max_cps=max_cps,
                combo_count=combo,
                last_attack_time=last_attack_ms,
            )
            score = self.predictor.score_target(features)
            candidates.append((e, score, dist))

        if not candidates:
            return None

        candidates.sort(key=lambda x: (x[1], -x[2]), reverse=True)
        return candidates[0][0]
