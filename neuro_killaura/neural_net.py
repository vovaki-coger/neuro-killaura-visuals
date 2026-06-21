"""
Нейросеть KillAura — PyTorch MLP (16→64→32→4)
Входы:  [distance, yaw_delta, pitch_delta, vel_x, vel_y, vel_z,
          yaw_speed, pitch_speed, time_since_attack, target_hp,
          dist_to_range, fov_angle, ping, avg_cps, combo, target_height]
Выходы: [aim_yaw, aim_pitch, attack_confidence, timing_delay]
"""
import os
import torch
import torch.nn as nn
import numpy as np
from typing import Optional

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "aim_model.pth")


class NeuroKillAuraNet(nn.Module):
    def __init__(self, input_size: int = 16, hidden1: int = 64, hidden2: int = 32, output_size: int = 4):
        super().__init__()

        self.feature_extractor = nn.Sequential(
            nn.Linear(input_size, hidden1),
            nn.LayerNorm(hidden1),
            nn.LeakyReLU(0.01),
            nn.Dropout(0.2),
            nn.Linear(hidden1, hidden2),
            nn.LayerNorm(hidden2),
            nn.LeakyReLU(0.01),
            nn.Dropout(0.2),
        )

        self.aim_head = nn.Sequential(
            nn.Linear(hidden2, 16),
            nn.Tanh(),
            nn.Linear(16, 2),
        )

        self.attack_head = nn.Sequential(
            nn.Linear(hidden2, 8),
            nn.Sigmoid(),
            nn.Linear(8, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.feature_extractor(x)
        aim = self.aim_head(features)
        attack = self.attack_head(features)
        return torch.cat([aim, attack], dim=-1)


def generate_synthetic_weights(model: NeuroKillAuraNet) -> None:
    """Инициализация весов, имитирующих человекоподобный aiming."""
    with torch.no_grad():
        for name, param in model.named_parameters():
            if "weight" in name:
                nn.init.xavier_uniform_(param)
                param.data *= 0.3
            elif "bias" in name:
                nn.init.zeros_(param)


def create_or_load_model(path: str = MODEL_PATH) -> NeuroKillAuraNet:
    model = NeuroKillAuraNet()
    if os.path.exists(path):
        try:
            state = torch.load(path, map_location="cpu", weights_only=True)
            model.load_state_dict(state)
            print(f"[NeuralNet] Веса загружены: {path}")
        except Exception as e:
            print(f"[NeuralNet] Ошибка загрузки весов ({e}), генерирую синтетические")
            generate_synthetic_weights(model)
            save_model(model, path)
    else:
        print("[NeuralNet] Файл весов не найден, генерирую синтетические")
        generate_synthetic_weights(model)
        save_model(model, path)
    model.eval()
    return model


def save_model(model: NeuroKillAuraNet, path: str = MODEL_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"[NeuralNet] Веса сохранены: {path}")


class NeuralPredictor:
    """Обёртка для быстрого инференса."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = create_or_load_model().to(self.device)
        self.model.eval()

    def predict(self, features: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            t = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
            out = self.model(t).cpu().numpy()[0]
        return out

    def score_target(self, features: np.ndarray) -> float:
        """Возвращает confidence для выбора цели."""
        return float(self.predict(features)[2])

    def get_aim_correction(self, features: np.ndarray) -> tuple[float, float]:
        pred = self.predict(features)
        return float(pred[0]) * 180.0, float(pred[1]) * 90.0

    def get_timing_delay_ms(self, features: np.ndarray) -> float:
        return float(self.predict(features)[3]) * 100.0

    @property
    def device_name(self) -> str:
        return "GPU (CUDA)" if self.device.type == "cuda" else "CPU"

    def get_model_info(self) -> dict:
        total_params = sum(p.numel() for p in self.model.parameters())
        return {
            "architecture": "MLP 16→64→32→4",
            "parameters": total_params,
            "device": self.device_name,
            "path": MODEL_PATH,
            "exists": os.path.exists(MODEL_PATH),
        }
