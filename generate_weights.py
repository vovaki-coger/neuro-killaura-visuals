"""
Скрипт генерации синтетических весов нейросети.
Запускается в GitHub Actions перед PyInstaller.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from neuro_killaura.neural_net import NeuroKillAuraNet, generate_synthetic_weights

print("Generating synthetic model weights...")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

model = NeuroKillAuraNet()
generate_synthetic_weights(model)

os.makedirs("models", exist_ok=True)
torch.save(model.state_dict(), "models/aim_model.pth")

size_kb = os.path.getsize("models/aim_model.pth") / 1024
print(f"Weights saved: models/aim_model.pth ({size_kb:.1f} KB)")

# Verify the weights load correctly
model2 = NeuroKillAuraNet()
model2.load_state_dict(torch.load("models/aim_model.pth", map_location="cpu", weights_only=True))
model2.eval()

import numpy as np
test_input = torch.zeros(1, 16)
with torch.no_grad():
    out = model2(test_input)
print(f"Test inference OK: output shape {out.shape}, values: {out.numpy()[0].round(4)}")
print("All done!")
