# ⚡ Neuro KillAura + Visuals

> Кастомный лаунчер Minecraft с нейросетевым KillAura (PyTorch MLP), Pulse Visuals, Rili ESP и полным GUI на CustomTkinter.

[![Build & Release](https://github.com/vovaki-coger/neuro-killaura-visuals/actions/workflows/build-release.yml/badge.svg)](https://github.com/vovaki-coger/neuro-killaura-visuals/actions/workflows/build-release.yml)

---

## 📥 Скачать

👉 **[Releases](https://github.com/vovaki-coger/neuro-killaura-visuals/releases/latest)** — скачай `NeuroKillAura-Windows-x64.zip`, распакуй и запусти `NeuroKillAura.exe`.

---

## 🧠 Архитектура нейросети

```
Input (16 features)
    ↓
Linear(16→64) + LayerNorm + LeakyReLU + Dropout(0.2)
    ↓
Linear(64→32) + LayerNorm + LeakyReLU + Dropout(0.2)
    ↓
    ├── Aim Head: Linear(32→16) → Tanh → Linear(16→2)
    │   [aim_yaw, aim_pitch]
    └── Attack Head: Linear(32→8) → Sigmoid → Linear(8→2)
        [attack_confidence, timing_delay]
```

### 16 входных признаков
| # | Признак | Нормализация |
|---|---------|-------------|
| 0 | Дистанция до цели | / 6.0 |
| 1 | Разница по Yaw | / 180° |
| 2 | Разница по Pitch | / 90° |
| 3-5 | Скорость цели (X,Y,Z) | / 10.0 |
| 6-7 | Скорость поворота игрока | / 180°, 90° |
| 8 | Время с последней атаки | / 1000ms |
| 9 | HP цели | / 20 |
| 10 | Дистанция / Range limit | — |
| 11 | FOV угол | / FOV limit |
| 12 | Пинг | / 500ms |
| 13 | Средний CPS | / 20 |
| 14 | Combo count | / 10 |
| 15 | Высота цели | / 2.0 |

---

## 🎮 Лаунчер

| Вкладка | Описание |
|---------|---------|
| **Играть** | Выбор версии (1.8.9/1.12.2/1.16.5/1.20.1), Loader, RAM, запуск |
| **Аккаунт** | Microsoft OAuth, Mojang Legacy, Оффлайн |
| **Нейросеть** | Статус модели, live confidence, управление весами |
| **Визуалы** | Pulse Visuals, Rili ESP, превью в реальном времени |
| **Настройки** | KillAura параметры, темы, Java args |
| **Консоль** | Логи, отладка |

---

## 🎨 Визуалы

### Pulse Visuals
- Пульсирующие круги с ease-in-out анимацией
- Частицы при ударе
- Волны (hit waves) от каждой атаки
- Glow-эффект на цели

### Rili Visuals (ESP)
- **Box ESP** — full box или уголки, настраиваемая толщина
- **Tracers** — линии от игрока к цели
- **Health Bar** — боковая полоса с цветом по HP
- **Armor Bar** — синяя полоса брони
- **Name ESP** — никнейм над боксом
- **Radar** — 2D мини-карта с точками
- **Crosshair** — динамический прицел со спредом

### HUD
- Информация о цели (HP, дистанция, confidence)
- CPS-график (60-кадровая история)
- Combo-анимация
- Watermark с пульсацией
- Привязки горячих клавиш

---

## ⌨️ Горячие клавиши

| Клавиша | Действие |
|---------|---------|
| `INSERT` | Открыть/закрыть меню |
| `R` | Вкл/выкл KillAura |
| `G` | Вкл/выкл визуалы |
| `H` | Вкл/выкл HUD |
| `ESC` | Выход |

---

## 🛠️ Сборка из исходников

```bash
git clone https://github.com/vovaki-coger/neuro-killaura-visuals.git
cd neuro-killaura-visuals
pip install -r requirements.txt
python main.py
```

### Сборка .exe (PyInstaller)
```bash
pip install pyinstaller
pyinstaller neuro_killaura.spec --noconfirm --clean
# Результат: dist/NeuroKillAura/NeuroKillAura.exe
```

---

## 📦 Зависимости

```
customtkinter>=5.2.2   # Modern dark GUI
Pillow>=10.0.0         # Image processing
torch>=2.0.0           # Neural network (MLP)
numpy>=1.24.0          # Feature extraction
pygame>=2.5.0          # Overlay rendering
requests>=2.31.0       # HTTP (auth, updates)
pynput>=1.7.6          # Hotkeys
psutil>=5.9.0          # Process management
```

---

## 📁 Структура проекта

```
neuro-killaura/
├── main.py                        # Точка входа
├── launcher/
│   ├── gui.py                     # Главный GUI (CustomTkinter)
│   ├── auth.py                    # Microsoft OAuth / Mojang / Offline
│   ├── config.py                  # Загрузка/сохранение конфига
│   ├── updater.py                 # Автообновление с GitHub Releases
│   └── themes.py                  # Dark / Light / Purple темы
├── neuro_killaura/
│   ├── neural_net.py              # PyTorch MLP (16→64→32→4)
│   ├── aimbot.py                  # Главный модуль KillAura
│   ├── target_selector.py         # Score-based выбор цели
│   ├── smooth_aim.py              # Human-like aim (ease-in-out, shake)
│   ├── attack_timer.py            # Адаптивный CPS таймер
│   ├── feature_extractor.py       # 16 признаков для нейросети
│   ├── anti_detect.py             # Рандомизация, паузы
│   └── memory_reader.py           # Заглушка чтения памяти
├── visuals/
│   ├── pulse_visual.py            # Pulse кольца, частицы, волны
│   ├── rili_visual.py             # Box ESP, Tracers, Radar, Crosshair
│   ├── hud.py                     # HUD, CPS граф, Combo, Watermark
│   ├── gui_overlay.py             # ImGui-style окна на pygame
│   ├── overlay_main.py            # Главный процесс оверлея
│   └── color_manager.py           # Конвертация цветов, пресеты
├── utils/
│   ├── math_utils.py              # wrap_angle, lerp, fov_between
│   └── input_simulator.py         # Клики, движение мыши
├── models/
│   └── aim_model.pth              # Веса нейросети
├── configs/
│   ├── default.json               # Настройки по умолчанию
│   └── user.json                  # Пользовательские настройки
├── .github/workflows/
│   └── build-release.yml          # GitHub Actions → .exe релиз
├── neuro_killaura.spec            # PyInstaller конфигурация
└── requirements.txt
```

---

*Проект создан для образовательных целей.*
