"""
Менеджер конфигурации — загрузка/сохранение config.json
"""
import json
import os
import copy

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "default.json")
USER_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "user.json")


def _load_defaults() -> dict:
    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> dict:
    defaults = _load_defaults()
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                user = json.load(f)
            _deep_merge(defaults, user)
        except Exception:
            pass
    return defaults


def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
    with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
