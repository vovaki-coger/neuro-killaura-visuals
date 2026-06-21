"""
Главный GUI лаунчера — CustomTkinter, тёмная тема, все вкладки
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, colorchooser
import threading
import time
import math
import os
import sys
import subprocess
import json
from typing import Optional

from launcher.config import load_config, save_config
from launcher.themes import get_theme, THEMES
from launcher.auth import AuthManager
from launcher.updater import Updater, CURRENT_VERSION

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

MC_VERSIONS = ["1.8.9", "1.12.2", "1.16.5", "1.20.1"]
MC_LOADERS = ["Vanilla", "Forge", "Fabric", "Quilt"]
RAM_OPTIONS = ["512 MB", "1 GB", "2 GB", "4 GB", "6 GB", "8 GB"]
RAM_VALUES = [512, 1024, 2048, 4096, 6144, 8192]


class LauncherApp:
    def __init__(self):
        self.cfg = load_config()
        self.theme = get_theme(self.cfg.get("theme", "dark"))
        self.auth = AuthManager(self._log)
        self.updater = Updater(self._log)
        self._overlay_proc: Optional[subprocess.Popen] = None
        self._nn_predictor = None
        self._nn_loaded = False

        self.root = ctk.CTk()
        self.root.title(f"⚡ Neuro KillAura Launcher  v{CURRENT_VERSION}")
        self.root.geometry("1100x720")
        self.root.resizable(False, False)
        self.root.configure(fg_color="#0d0d0f")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._profile: Optional[dict] = self.auth.restore_session()
        self._build_ui()
        self._update_profile_ui()
        self._start_nn_load()
        self.updater.check_async(self._on_update_check)
        self._animate()

    # ─── Build UI ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Left sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=190, fg_color="#141416", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="⚡ Neuro\nKillAura",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#e53935",
        )
        logo_label.pack(pady=(24, 4))

        ver_label = ctk.CTkLabel(
            self.sidebar, text=f"v{CURRENT_VERSION}",
            font=ctk.CTkFont(size=11), text_color="#555555",
        )
        ver_label.pack(pady=(0, 20))

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2a2a32").pack(fill="x", padx=16, pady=4)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("🎮  Играть", "play"),
            ("🔐  Аккаунт", "account"),
            ("🧠  Нейросеть", "neural"),
            ("🎨  Визуалы", "visuals"),
            ("⚙️   Настройки", "settings"),
            ("📋  Консоль", "console"),
        ]
        for label, key in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color="#2a2a32",
                text_color="#aaaaaa", anchor="w",
                command=lambda k=key: self._switch_tab(k),
                height=40, corner_radius=8,
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_footer.pack(side="bottom", fill="x", padx=10, pady=14)

        ctk.CTkButton(
            self.sidebar_footer, text="Выход",
            font=ctk.CTkFont(size=12), fg_color="#1e1e24",
            hover_color="#300000", text_color="#888888",
            command=self._on_close, height=32,
        ).pack(fill="x")

        # Main content area
        self.content = ctk.CTkFrame(self.root, fg_color="#0d0d0f", corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        self._frames: dict[str, ctk.CTkFrame] = {}
        for key in ["play", "account", "neural", "visuals", "settings", "console"]:
            frame = ctk.CTkFrame(self.content, fg_color="#0d0d0f", corner_radius=0)
            self._frames[key] = frame

        self._build_play_tab()
        self._build_account_tab()
        self._build_neural_tab()
        self._build_visuals_tab()
        self._build_settings_tab()
        self._build_console_tab()

        self._switch_tab("play")

    # ── Tab switcher ──────────────────────────────────────────────────────────

    def _switch_tab(self, key: str) -> None:
        for k, frame in self._frames.items():
            frame.pack_forget()
        self._frames[key].pack(fill="both", expand=True, padx=20, pady=20)

        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color="#1e1e24", text_color="#e53935")
            else:
                btn.configure(fg_color="transparent", text_color="#aaaaaa")

    # ── Play Tab ──────────────────────────────────────────────────────────────

    def _build_play_tab(self) -> None:
        f = self._frames["play"]
        ctk.CTkLabel(f, text="Запуск Minecraft", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", pady=(0, 16))

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))

        # Version selector
        ver_box = ctk.CTkFrame(row, fg_color="#141416", corner_radius=10)
        ver_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(ver_box, text="Версия", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", padx=14, pady=(12, 2))
        self.ver_var = ctk.StringVar(value=self.cfg["minecraft"]["version"])
        ctk.CTkOptionMenu(ver_box, values=MC_VERSIONS, variable=self.ver_var,
                          fg_color="#1e1e24", button_color="#2a2a32",
                          font=ctk.CTkFont(size=13)).pack(fill="x", padx=14, pady=(0, 12))

        # Loader selector
        loader_box = ctk.CTkFrame(row, fg_color="#141416", corner_radius=10)
        loader_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(loader_box, text="Loader", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", padx=14, pady=(12, 2))
        self.loader_var = ctk.StringVar(value=self.cfg["minecraft"]["loader"])
        ctk.CTkOptionMenu(loader_box, values=MC_LOADERS, variable=self.loader_var,
                          fg_color="#1e1e24", button_color="#2a2a32",
                          font=ctk.CTkFont(size=13)).pack(fill="x", padx=14, pady=(0, 12))

        # RAM selector
        ram_box = ctk.CTkFrame(row, fg_color="#141416", corner_radius=10)
        ram_box.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(ram_box, text="RAM", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", padx=14, pady=(12, 2))
        current_ram = self.cfg["minecraft"]["ram_mb"]
        ram_idx = RAM_VALUES.index(current_ram) if current_ram in RAM_VALUES else 2
        self.ram_var = ctk.StringVar(value=RAM_OPTIONS[ram_idx])
        ctk.CTkOptionMenu(ram_box, values=RAM_OPTIONS, variable=self.ram_var,
                          fg_color="#1e1e24", button_color="#2a2a32",
                          font=ctk.CTkFont(size=13)).pack(fill="x", padx=14, pady=(0, 12))

        # Killaura toggles
        ka_frame = ctk.CTkFrame(f, fg_color="#141416", corner_radius=10)
        ka_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(ka_frame, text="⚡ KillAura", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e53935").pack(anchor="w", padx=14, pady=(12, 6))
        trow = ctk.CTkFrame(ka_frame, fg_color="transparent")
        trow.pack(fill="x", padx=14, pady=(0, 12))

        self.ka_enabled_var = ctk.BooleanVar(value=self.cfg["killaura"]["enabled"])
        ctk.CTkSwitch(trow, text="KillAura [R]", variable=self.ka_enabled_var,
                      progress_color="#e53935", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 20))

        self.vis_enabled_var = ctk.BooleanVar(value=self.cfg["visuals"]["rili_enabled"])
        ctk.CTkSwitch(trow, text="Визуалы [G]", variable=self.vis_enabled_var,
                      progress_color="#9c27b0", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 20))

        self.hud_enabled_var = ctk.BooleanVar(value=self.cfg["hud"]["enabled"])
        ctk.CTkSwitch(trow, text="HUD [H]", variable=self.hud_enabled_var,
                      progress_color="#1976d2", font=ctk.CTkFont(size=13)).pack(side="left")

        # Launch buttons
        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 12))

        self.launch_btn = ctk.CTkButton(
            btn_row, text="▶  ЗАПУСТИТЬ", height=52,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#e53935", hover_color="#c62828",
            command=self._launch_minecraft,
        )
        self.launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="🎨  Оверлей (демо)", height=52,
            font=ctk.CTkFont(size=14),
            fg_color="#1e1e24", hover_color="#2a2a32",
            command=self._launch_overlay_demo,
        ).pack(side="left", padx=(0, 8))

        self.update_btn = ctk.CTkButton(
            btn_row, text="🔄  Обновить", height=52,
            font=ctk.CTkFont(size=14),
            fg_color="#1e1e24", hover_color="#2a2a32",
            command=self._check_update,
        )
        self.update_btn.pack(side="left")

        # Status bar
        self.status_bar = ctk.CTkLabel(
            f, text="Готово к запуску",
            font=ctk.CTkFont(size=12), text_color="#555555",
        )
        self.status_bar.pack(anchor="w", pady=(4, 0))

    # ── Account Tab ───────────────────────────────────────────────────────────

    def _build_account_tab(self) -> None:
        f = self._frames["account"]
        ctk.CTkLabel(f, text="Аккаунт", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", pady=(0, 16))

        self.auth_mode_var = ctk.StringVar(value=self.cfg["auth"]["mode"])

        # Profile display
        self.profile_card = ctk.CTkFrame(f, fg_color="#141416", corner_radius=10)
        self.profile_card.pack(fill="x", pady=(0, 12))
        self.profile_name_lbl = ctk.CTkLabel(
            self.profile_card, text="Не авторизован",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#888888",
        )
        self.profile_name_lbl.pack(padx=14, pady=(14, 2))
        self.profile_mode_lbl = ctk.CTkLabel(
            self.profile_card, text="",
            font=ctk.CTkFont(size=11), text_color="#555555",
        )
        self.profile_mode_lbl.pack(padx=14, pady=(0, 14))

        # Mode selector tabs
        mode_row = ctk.CTkFrame(f, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 12))
        for mode, label in [("offline", "Оффлайн"), ("mojang", "Mojang"), ("microsoft", "Microsoft")]:
            ctk.CTkRadioButton(
                mode_row, text=label, variable=self.auth_mode_var, value=mode,
                font=ctk.CTkFont(size=13),
                fg_color="#e53935", command=self._on_auth_mode_change,
            ).pack(side="left", padx=(0, 20))

        # Auth forms container
        self.auth_forms = ctk.CTkFrame(f, fg_color="transparent")
        self.auth_forms.pack(fill="x")

        # Offline form
        self.offline_frame = ctk.CTkFrame(self.auth_forms, fg_color="#141416", corner_radius=10)
        ctk.CTkLabel(self.offline_frame, text="Никнейм", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", padx=14, pady=(12, 2))
        self.offline_name_entry = ctk.CTkEntry(self.offline_frame, placeholder_text="YourNickname",
                                                fg_color="#16161a", border_color="#2a2a32")
        self.offline_name_entry.pack(fill="x", padx=14, pady=(0, 12))
        if self.cfg["auth"]["username"]:
            self.offline_name_entry.insert(0, self.cfg["auth"]["username"])
        ctk.CTkButton(self.offline_frame, text="Войти (оффлайн)", fg_color="#1976d2",
                      hover_color="#1565c0", command=self._offline_login).pack(padx=14, pady=(0, 12))

        # Mojang form
        self.mojang_frame = ctk.CTkFrame(self.auth_forms, fg_color="#141416", corner_radius=10)
        ctk.CTkLabel(self.mojang_frame, text="Email", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", padx=14, pady=(12, 2))
        self.mojang_email_entry = ctk.CTkEntry(self.mojang_frame, placeholder_text="your@email.com",
                                               fg_color="#16161a", border_color="#2a2a32")
        self.mojang_email_entry.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(self.mojang_frame, text="Пароль", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", padx=14)
        self.mojang_pass_entry = ctk.CTkEntry(self.mojang_frame, placeholder_text="Пароль",
                                              show="*", fg_color="#16161a", border_color="#2a2a32")
        self.mojang_pass_entry.pack(fill="x", padx=14, pady=(2, 8))
        ctk.CTkButton(self.mojang_frame, text="Войти (Mojang)", fg_color="#e53935",
                      hover_color="#c62828", command=self._mojang_login).pack(padx=14, pady=(0, 12))

        # Microsoft form
        self.ms_frame = ctk.CTkFrame(self.auth_forms, fg_color="#141416", corner_radius=10)
        ctk.CTkLabel(self.ms_frame,
                     text="Microsoft OAuth\nНажмите кнопку — откроется браузер",
                     font=ctk.CTkFont(size=12), text_color="#888888", justify="center").pack(padx=14, pady=(12, 8))
        ctk.CTkButton(self.ms_frame, text="🌐  Войти через Microsoft",
                      fg_color="#0078d4", hover_color="#005a9e",
                      command=self._ms_login_open).pack(padx=14, pady=(0, 8))
        ctk.CTkLabel(self.ms_frame, text="Код из URL после авторизации:", font=ctk.CTkFont(size=11), text_color="#666666").pack(anchor="w", padx=14)
        self.ms_code_entry = ctk.CTkEntry(self.ms_frame, placeholder_text="Вставьте code=...",
                                          fg_color="#16161a", border_color="#2a2a32")
        self.ms_code_entry.pack(fill="x", padx=14, pady=(2, 8))
        ctk.CTkButton(self.ms_frame, text="Подтвердить код", fg_color="#1976d2",
                      command=self._ms_login_finish).pack(padx=14, pady=(0, 12))

        ctk.CTkButton(f, text="Выйти из аккаунта", fg_color="transparent",
                      hover_color="#1a0000", text_color="#e53935",
                      border_color="#e53935", border_width=1,
                      command=self._logout).pack(anchor="w", pady=(12, 0))

        self._on_auth_mode_change()

    # ── Neural Tab ────────────────────────────────────────────────────────────

    def _build_neural_tab(self) -> None:
        f = self._frames["neural"]
        ctk.CTkLabel(f, text="Нейросеть KillAura", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", pady=(0, 16))

        # Status card
        status_card = ctk.CTkFrame(f, fg_color="#141416", corner_radius=10)
        status_card.pack(fill="x", pady=(0, 12))

        self.nn_status_lbl = ctk.CTkLabel(status_card, text="🔄 Загружаю нейросеть...",
                                          font=ctk.CTkFont(size=14, weight="bold"),
                                          text_color="#ffab00")
        self.nn_status_lbl.pack(padx=14, pady=(14, 4))

        self.nn_progress = ctk.CTkProgressBar(status_card, progress_color="#e53935", height=8)
        self.nn_progress.pack(fill="x", padx=14, pady=(0, 8))
        self.nn_progress.set(0)

        self.nn_arch_lbl = ctk.CTkLabel(status_card, text="Архитектура: MLP 16→64→32→4",
                                        font=ctk.CTkFont(size=12), text_color="#888888")
        self.nn_arch_lbl.pack(padx=14, pady=(0, 4))

        self.nn_device_lbl = ctk.CTkLabel(status_card, text="Устройство: CPU",
                                          font=ctk.CTkFont(size=12), text_color="#888888")
        self.nn_device_lbl.pack(padx=14, pady=(0, 14))

        # Confidence meter
        conf_card = ctk.CTkFrame(f, fg_color="#141416", corner_radius=10)
        conf_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(conf_card, text="Live Confidence", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#aaaaaa").pack(padx=14, pady=(12, 4))
        self.conf_bar = ctk.CTkProgressBar(conf_card, progress_color="#00c853", height=16)
        self.conf_bar.pack(fill="x", padx=14, pady=(0, 4))
        self.conf_bar.set(0)
        self.conf_lbl = ctk.CTkLabel(conf_card, text="0%", font=ctk.CTkFont(size=14, weight="bold"),
                                     text_color="#00c853")
        self.conf_lbl.pack(padx=14, pady=(0, 14))

        # Actions
        act_row = ctk.CTkFrame(f, fg_color="transparent")
        act_row.pack(fill="x")
        ctk.CTkButton(act_row, text="🔄  Перезагрузить веса", fg_color="#1e1e24",
                      hover_color="#2a2a32", command=self._reload_model).pack(side="left", padx=(0, 8))
        ctk.CTkButton(act_row, text="💾  Сохранить веса", fg_color="#1e1e24",
                      hover_color="#2a2a32", command=self._save_model).pack(side="left")

    # ── Visuals Tab ───────────────────────────────────────────────────────────

    def _build_visuals_tab(self) -> None:
        f = self._frames["visuals"]
        ctk.CTkLabel(f, text="Визуалы", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent", label_text="")
        scroll.pack(fill="both", expand=True)

        # Pulse Visuals
        self._vis_section(scroll, "⚡ Pulse Visuals", [
            ("pulse_enabled", "Включить Pulse Visuals"),
        ])
        self._color_row(scroll, "Цвет пульса", "pulse_color")
        self._slider_row(scroll, "Скорость пульсации", "pulse_speed", 0.5, 5.0)
        self._slider_row(scroll, "Размер", "pulse_size", 10, 100)
        self._slider_row(scroll, "Прозрачность", "pulse_opacity", 30, 255, is_int=True)

        ctk.CTkFrame(scroll, height=1, fg_color="#2a2a32").pack(fill="x", pady=10)

        # Rili ESP
        self._vis_section(scroll, "📦 Rili ESP", [
            ("box_enabled", "Box ESP"),
            ("tracers_enabled", "Tracers"),
            ("health_bar_enabled", "Health Bar"),
            ("health_text", "Показывать HP текстом"),
            ("armor_bar_enabled", "Armor Bar"),
            ("name_esp_enabled", "Name ESP"),
        ])
        self._color_row(scroll, "Цвет бокса", "box_color")

        ctk.CTkFrame(scroll, height=1, fg_color="#2a2a32").pack(fill="x", pady=10)

        self._vis_section(scroll, "📡 Radar & HUD", [
            ("radar_enabled", "Radar (2D)"),
            ("crosshair_enabled", "Crosshair"),
            ("crosshair_dynamic", "Динамический Crosshair"),
        ])

        # Canvas preview
        ctk.CTkFrame(scroll, height=1, fg_color="#2a2a32").pack(fill="x", pady=10)
        ctk.CTkLabel(scroll, text="🖼  Превью (демо)", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#aaaaaa").pack(anchor="w", pady=(0, 6))
        preview_frame = ctk.CTkFrame(scroll, fg_color="#0a0a0c", corner_radius=8)
        preview_frame.pack(fill="x")
        self.preview_canvas = tk.Canvas(preview_frame, width=700, height=180,
                                        bg="#0a0a0c", highlightthickness=0)
        self.preview_canvas.pack(padx=4, pady=4)

        ctk.CTkButton(scroll, text="Применить и сохранить", fg_color="#e53935",
                      hover_color="#c62828", command=self._save_visuals).pack(pady=12)

        self._vis_vars: dict = {}

    def _vis_section(self, parent, title: str, toggles: list) -> None:
        ctk.CTkLabel(parent, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#aaaaaa").pack(anchor="w", pady=(8, 4))
        for key, label in toggles:
            var = ctk.BooleanVar(value=self.cfg["visuals"].get(key, True))
            ctk.CTkSwitch(parent, text=label, variable=var,
                          progress_color="#e53935", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)
            if not hasattr(self, "_vis_vars"):
                self._vis_vars = {}
            self._vis_vars[key] = var

    def _slider_row(self, parent, label: str, key: str, lo: float, hi: float, is_int: bool = False) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=180, anchor="w",
                     font=ctk.CTkFont(size=12), text_color="#888888").pack(side="left")
        val = self.cfg["visuals"].get(key, (lo + hi) / 2)
        var = ctk.DoubleVar(value=val)
        lbl = ctk.CTkLabel(row, text=f"{val:.1f}", width=40, font=ctk.CTkFont(size=12), text_color="#aaaaaa")
        lbl.pack(side="right")
        slider = ctk.CTkSlider(row, from_=lo, to=hi, variable=var, progress_color="#e53935",
                               command=lambda v, l=lbl, k=key: (l.configure(text=f"{float(v):.1f}"), self.cfg["visuals"].__setitem__(k, float(v))))
        slider.pack(side="left", fill="x", expand=True, padx=8)
        if not hasattr(self, "_vis_vars"):
            self._vis_vars = {}
        self._vis_vars[key] = var

    def _color_row(self, parent, label: str, key: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=180, anchor="w",
                     font=ctk.CTkFont(size=12), text_color="#888888").pack(side="left")
        color = self.cfg["visuals"].get(key, [255, 50, 50])
        hex_c = "#{:02x}{:02x}{:02x}".format(*color)
        btn = ctk.CTkButton(row, text="", width=32, height=24, fg_color=hex_c,
                            hover_color=hex_c,
                            command=lambda k=key: self._pick_color(k))
        btn.pack(side="left")
        if not hasattr(self, "_color_btns"):
            self._color_btns = {}
        self._color_btns[key] = btn

    def _pick_color(self, key: str) -> None:
        cur = self.cfg["visuals"].get(key, [255, 50, 50])
        init_color = "#{:02x}{:02x}{:02x}".format(*cur)
        result = colorchooser.askcolor(color=init_color, title="Выберите цвет")
        if result[0]:
            rgb = [int(c) for c in result[0]]
            self.cfg["visuals"][key] = rgb
            hex_c = "#{:02x}{:02x}{:02x}".format(*rgb)
            self._color_btns[key].configure(fg_color=hex_c, hover_color=hex_c)

    # ── Settings Tab ──────────────────────────────────────────────────────────

    def _build_settings_tab(self) -> None:
        f = self._frames["settings"]
        ctk.CTkLabel(f, text="Настройки", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", pady=(0, 16))

        # KillAura params
        ka_card = ctk.CTkFrame(f, fg_color="#141416", corner_radius=10)
        ka_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(ka_card, text="⚡ KillAura", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e53935").pack(anchor="w", padx=14, pady=(12, 6))

        params = [
            ("range", "Range (блоки)", 1.0, 6.0),
            ("fov", "FOV (градусы)", 30.0, 180.0),
            ("min_cps", "Min CPS", 4.0, 20.0),
            ("max_cps", "Max CPS", 4.0, 20.0),
            ("smooth", "Smooth (0=быстро)", 0.05, 0.5),
        ]
        self._ka_vars: dict = {}
        for key, label, lo, hi in params:
            row = ctk.CTkFrame(ka_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=label, width=200, anchor="w",
                         font=ctk.CTkFont(size=12), text_color="#888888").pack(side="left")
            val = self.cfg["killaura"].get(key, (lo + hi) / 2)
            var = ctk.DoubleVar(value=val)
            lbl = ctk.CTkLabel(row, text=f"{val:.2f}", width=50, font=ctk.CTkFont(size=12), text_color="#aaaaaa")
            lbl.pack(side="right")
            ctk.CTkSlider(row, from_=lo, to=hi, variable=var, progress_color="#e53935",
                          command=lambda v, l=lbl, k=key: (l.configure(text=f"{float(v):.2f}"),
                                                            self.cfg["killaura"].__setitem__(k, float(v)))).pack(side="left", fill="x", expand=True, padx=8)
            self._ka_vars[key] = var

        ctk.CTkFrame(ka_card, fg_color="transparent", height=8).pack()

        # Theme selector
        theme_card = ctk.CTkFrame(f, fg_color="#141416", corner_radius=10)
        theme_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(theme_card, text="🎨 Тема", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#aaaaaa").pack(anchor="w", padx=14, pady=(12, 6))
        self.theme_var = ctk.StringVar(value=self.cfg.get("theme", "dark"))
        theme_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_row.pack(padx=14, pady=(0, 12), fill="x")
        for t in THEMES.keys():
            ctk.CTkRadioButton(theme_row, text=t.capitalize(), variable=self.theme_var, value=t,
                               fg_color="#e53935", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 16))

        ctk.CTkButton(f, text="💾  Сохранить все настройки", fg_color="#e53935",
                      hover_color="#c62828", command=self._save_all).pack(pady=12)

    # ── Console Tab ───────────────────────────────────────────────────────────

    def _build_console_tab(self) -> None:
        f = self._frames["console"]
        ctk.CTkLabel(f, text="Консоль", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", pady=(0, 8))

        self.console_text = ctk.CTkTextbox(
            f, fg_color="#0a0a0c", text_color="#00ff41",
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled",
        )
        self.console_text.pack(fill="both", expand=True)

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(row, text="Очистить", fg_color="#1e1e24",
                      hover_color="#2a2a32", command=self._clear_console).pack(side="left")

    # ─── Logic ───────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        try:
            self.console_text.configure(state="normal")
            self.console_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.console_text.configure(state="disabled")
            self.console_text.see("end")
        except Exception:
            print(msg)

    def _clear_console(self) -> None:
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")

    def _update_profile_ui(self) -> None:
        if self._profile:
            name = self._profile.get("username", "Player")
            mode_map = {"offline": "Оффлайн режим", "mojang": "Mojang Premium", "microsoft": "Microsoft Premium"}
            mode = mode_map.get(self._profile.get("mode", "offline"), "")
            self.profile_name_lbl.configure(text=f"✓  {name}", text_color="#00c853")
            self.profile_mode_lbl.configure(text=mode)
            self._log(f"[GUI] Профиль: {name} ({mode})")
        else:
            self.profile_name_lbl.configure(text="Не авторизован", text_color="#888888")
            self.profile_mode_lbl.configure(text="")

    def _on_auth_mode_change(self) -> None:
        for frame in [self.offline_frame, self.mojang_frame, self.ms_frame]:
            frame.pack_forget()
        mode = self.auth_mode_var.get()
        frame_map = {"offline": self.offline_frame, "mojang": self.mojang_frame, "microsoft": self.ms_frame}
        frame_map[mode].pack(fill="x", pady=(0, 8))

    def _offline_login(self) -> None:
        name = self.offline_name_entry.get().strip()
        ok, profile = self.auth.offline_login(name)
        if ok:
            self._profile = profile
            self._update_profile_ui()
        else:
            messagebox.showerror("Ошибка", profile.get("error", "Неизвестная ошибка"))

    def _mojang_login(self) -> None:
        email = self.mojang_email_entry.get().strip()
        pwd = self.mojang_pass_entry.get()
        def _do():
            ok, profile = self.auth.mojang_login(email, pwd)
            self.root.after(0, lambda: self._on_login_result(ok, profile))
        threading.Thread(target=_do, daemon=True).start()

    def _ms_login_open(self) -> None:
        self.auth.microsoft_open_browser()

    def _ms_login_finish(self) -> None:
        code = self.ms_code_entry.get().strip()
        if "code=" in code:
            code = code.split("code=")[1].split("&")[0]
        def _do():
            ok, profile = self.auth.microsoft_finish_with_code(code)
            self.root.after(0, lambda: self._on_login_result(ok, profile))
        threading.Thread(target=_do, daemon=True).start()

    def _on_login_result(self, ok: bool, profile: dict) -> None:
        if ok:
            self._profile = profile
            self._update_profile_ui()
        else:
            messagebox.showerror("Ошибка авторизации", profile.get("error", "Ошибка"))

    def _logout(self) -> None:
        self.auth.logout()
        self._profile = None
        self._update_profile_ui()

    def _launch_minecraft(self) -> None:
        if not self._profile:
            messagebox.showwarning("Не авторизован", "Сначала войдите в аккаунт на вкладке Аккаунт")
            return

        ver = self.ver_var.get()
        loader = self.loader_var.get()
        ram_str = self.ram_var.get()
        ram = RAM_VALUES[RAM_OPTIONS.index(ram_str)]

        self._log(f"[Launcher] Запуск Minecraft {ver} ({loader}) RAM={ram_str}...")
        self.launch_btn.configure(state="disabled", text="⏳  Загрузка...")
        self.status_bar.configure(text=f"Подготовка Minecraft {ver}...")

        def _do_launch():
            try:
                import minecraft_launcher_lib as mll

                mc_dir = os.path.join(os.path.expanduser("~"), ".minecraft_neuro")
                os.makedirs(mc_dir, exist_ok=True)

                def _set_status(s):
                    self.root.after(0, lambda v=s: self.status_bar.configure(text=v))

                callback = {
                    "setStatus": _set_status,
                    "setMax": lambda _: None,
                    "setProgress": lambda _: None,
                }

                installed_ids = [v["id"] for v in mll.utils.get_installed_versions(mc_dir)]
                if ver not in installed_ids:
                    self._log(f"[Launcher] Скачиваю Minecraft {ver}... (может занять несколько минут)")
                    _set_status(f"Скачиваю Minecraft {ver}...")
                    mll.install.install_minecraft_version(ver, mc_dir, callback=callback)
                    self._log(f"[Launcher] Minecraft {ver} установлен.")

                profile = self._profile
                options = {
                    "username": profile.get("username", "Player"),
                    "uuid": profile.get("uuid", "00000000-0000-0000-0000-000000000000"),
                    "token": profile.get("token", "offline-token"),
                    "jvmArguments": [f"-Xmx{ram}m", "-Xms512m"],
                }

                command = mll.command.get_minecraft_command(ver, mc_dir, options)
                self._log(f"[Launcher] Запускаю (Java + Minecraft {ver})...")

                self.root.after(0, lambda: self.status_bar.configure(text=f"Minecraft {ver} запущен!"))
                self.root.after(0, lambda: self.launch_btn.configure(state="normal", text="▶  ЗАПУСТИТЬ"))

                proc = subprocess.Popen(command, cwd=mc_dir)
                self._log(f"[Launcher] ✅ Minecraft запущен (PID {proc.pid})")

            except ImportError:
                err = "minecraft-launcher-lib не найден.\nВ .exe он уже включён. При запуске из исходников: pip install minecraft-launcher-lib"
                self._log(f"[Launcher] ❌ {err}")
                self.root.after(0, lambda: messagebox.showerror("Ошибка зависимости", err))
                self.root.after(0, lambda: self.launch_btn.configure(state="normal", text="▶  ЗАПУСТИТЬ"))
                self.root.after(0, lambda: self.status_bar.configure(text="Ошибка зависимости"))

            except Exception as e:
                self._log(f"[Launcher] ❌ Ошибка запуска: {e}")
                self.root.after(0, lambda err=str(e): messagebox.showerror("Ошибка запуска", err))
                self.root.after(0, lambda: self.launch_btn.configure(state="normal", text="▶  ЗАПУСТИТЬ"))
                self.root.after(0, lambda err=str(e): self.status_bar.configure(text=f"Ошибка: {err}"))

        threading.Thread(target=_do_launch, daemon=True).start()

    def _launch_overlay_demo(self) -> None:
        self._log("[Overlay] Запуск демо-оверлея...")
        overlay_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "visuals", "overlay_main.py")
        try:
            self._overlay_proc = subprocess.Popen(
                [sys.executable, overlay_script],
                cwd=os.path.dirname(os.path.dirname(__file__)),
            )
            self._log(f"[Overlay] Запущен (PID {self._overlay_proc.pid}). ESC для закрытия.")
        except Exception as e:
            self._log(f"[Overlay] Ошибка запуска: {e}")

    def _check_update(self) -> None:
        self._log("[Updater] Проверяю обновления...")
        self.updater.check_async(self._on_update_check)

    def _on_update_check(self, has_update: bool, info: str) -> None:
        self._log(f"[Updater] {info}")
        if has_update and self.updater.download_url:
            self.update_btn.configure(text=f"⬇  {info}", fg_color="#e53935")

    def _start_nn_load(self) -> None:
        def _load():
            try:
                from neuro_killaura.neural_net import NeuralPredictor
                self._log("[NeuralNet] Загружаю модель...")
                self.root.after(0, lambda: self.nn_progress.set(0.3))
                pred = NeuralPredictor()
                self._nn_predictor = pred
                self._nn_loaded = True
                info = pred.get_model_info()
                self.root.after(0, lambda: self._on_nn_loaded(info))
            except Exception as e:
                self._log(f"[NeuralNet] Ошибка: {e}")
                self.root.after(0, lambda: self.nn_status_lbl.configure(
                    text=f"❌ Ошибка: {e}", text_color="#ff1744"))
        threading.Thread(target=_load, daemon=True).start()

    def _on_nn_loaded(self, info: dict) -> None:
        self.nn_progress.set(1.0)
        self.nn_status_lbl.configure(text="✅ Нейросеть готова", text_color="#00c853")
        self.nn_arch_lbl.configure(text=f"Архитектура: {info['architecture']}  |  Параметры: {info['parameters']:,}")
        self.nn_device_lbl.configure(text=f"Устройство: {info['device']}")
        self._log(f"[NeuralNet] Загружено. {info['architecture']}, {info['parameters']:,} параметров, {info['device']}")

    def _reload_model(self) -> None:
        self._nn_loaded = False
        self.nn_status_lbl.configure(text="🔄 Перезагрузка...", text_color="#ffab00")
        self.nn_progress.set(0)
        self._start_nn_load()

    def _save_model(self) -> None:
        if self._nn_predictor:
            from neuro_killaura.neural_net import save_model
            save_model(self._nn_predictor.model)
            self._log("[NeuralNet] Веса сохранены")

    def _save_visuals(self) -> None:
        if hasattr(self, "_vis_vars"):
            for k, var in self._vis_vars.items():
                self.cfg["visuals"][k] = var.get()
        save_config(self.cfg)
        self._log("[Config] Настройки визуалов сохранены")

    def _save_all(self) -> None:
        if hasattr(self, "_ka_vars"):
            for k, var in self._ka_vars.items():
                self.cfg["killaura"][k] = var.get()
        self.cfg["theme"] = self.theme_var.get()
        self.cfg["minecraft"]["version"] = self.ver_var.get()
        self.cfg["minecraft"]["loader"] = self.loader_var.get()
        ram_str = self.ram_var.get()
        self.cfg["minecraft"]["ram_mb"] = RAM_VALUES[RAM_OPTIONS.index(ram_str)]
        save_config(self.cfg)
        self._log("[Config] Все настройки сохранены")
        messagebox.showinfo("Сохранено", "Настройки успешно сохранены!")

    # ── Animation ─────────────────────────────────────────────────────────────

    def _animate(self) -> None:
        try:
            self._draw_preview()
            self._update_conf_meter()
        except Exception:
            pass
        self.root.after(50, self._animate)

    def _draw_preview(self) -> None:
        try:
            c = self.preview_canvas
            c.delete("all")
            W, H = 700, 180

            t = time.time()
            speed = self.cfg["visuals"].get("pulse_speed", 1.5)
            size = self.cfg["visuals"].get("pulse_size", 40)
            color = self.cfg["visuals"].get("pulse_color", [255, 50, 50])
            hex_c = "#{:02x}{:02x}{:02x}".format(*color)

            cx1, cy1 = 160, H // 2
            for i in range(3):
                phase = (t * speed + i * 0.4) % 1.0
                r = size * (0.5 + phase * 0.8)
                alpha_frac = 1.0 - phase
                darker = tuple(max(0, int(v * alpha_frac * 0.9)) for v in color)
                hex_d = "#{:02x}{:02x}{:02x}".format(*darker)
                c.create_oval(cx1 - r, cy1 - r, cx1 + r, cy1 + r, outline=hex_d, width=2)
            c.create_oval(cx1 - 6, cy1 - 6, cx1 + 6, cy1 + 6, fill=hex_c, outline="")

            box_color = self.cfg["visuals"].get("box_color", [255, 50, 50])
            bx = "#{:02x}{:02x}{:02x}".format(*box_color)
            bx1, by1, bw, bh = 300, 30, 60, 120
            cl = 12
            for pts in [
                [(bx1, by1), (bx1 + cl, by1)],
                [(bx1, by1), (bx1, by1 + cl)],
                [(bx1 + bw, by1), (bx1 + bw - cl, by1)],
                [(bx1 + bw, by1), (bx1 + bw, by1 + cl)],
                [(bx1, by1 + bh), (bx1 + cl, by1 + bh)],
                [(bx1, by1 + bh), (bx1, by1 + bh - cl)],
                [(bx1 + bw, by1 + bh), (bx1 + bw - cl, by1 + bh)],
                [(bx1 + bw, by1 + bh), (bx1 + bw, by1 + bh - cl)],
            ]:
                c.create_line(*pts[0], *pts[1], fill=bx, width=2)

            hp_pct = 0.6 + 0.2 * math.sin(t * 0.7)
            hp_color = "#00dc32" if hp_pct > 0.5 else "#ff5252"
            c.create_rectangle(bx1 - 8, by1, bx1 - 4, by1 + bh, fill="#1a1a1a", outline="")
            filled = int(bh * hp_pct)
            c.create_rectangle(bx1 - 8, by1 + bh - filled, bx1 - 4, by1 + bh, fill=hp_color, outline="")

            c.create_line(W // 2, H, bx1 + bw // 2, by1 + bh // 2, fill="white", width=1)
            c.create_text(bx1 + bw // 2, by1 - 12, text="Player1", fill="white", font=("Consolas", 10, "bold"))

            ra_cx, ra_cy, ra_r = 560, H // 2, 55
            c.create_oval(ra_cx - ra_r, ra_cy - ra_r, ra_cx + ra_r, ra_cy + ra_r, outline="#333333", width=1, fill="#0a0a0a")
            c.create_line(ra_cx, ra_cy - ra_r, ra_cx, ra_cy + ra_r, fill="#222222", width=1)
            c.create_line(ra_cx - ra_r, ra_cy, ra_cx + ra_r, ra_cy, fill="#222222", width=1)
            c.create_oval(ra_cx - 4, ra_cy - 4, ra_cx + 4, ra_cy + 4, fill="#00c853", outline="")
            angle = t * 0.8
            dot_x = ra_cx + int(math.cos(angle) * 30)
            dot_y = ra_cy + int(math.sin(angle) * 30)
            c.create_oval(dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4, fill=bx, outline="")

            wm_alpha = 0.6 + 0.4 * abs(math.sin(t * 1.5))
            wm_r = int(229 * wm_alpha)
            c.create_text(8, 8, text=f"⚡ Neuro KillAura v{CURRENT_VERSION}", anchor="nw",
                          fill="#{:02x}{:02x}35".format(wm_r, int(57 * wm_alpha)), font=("Consolas", 11, "bold"))
        except Exception:
            pass

    def _update_conf_meter(self) -> None:
        try:
            t = time.time()
            conf = 0.5 + 0.4 * abs(math.sin(t * 0.8))
            self.conf_bar.set(conf)
            self.conf_lbl.configure(text=f"{conf * 100:.0f}%")
        except Exception:
            pass

    def _on_close(self) -> None:
        if self._overlay_proc:
            try:
                self._overlay_proc.terminate()
            except Exception:
                pass
        self._save_all()
        self.root.destroy()

    def run(self) -> None:
        self._log(f"[Launcher] Neuro KillAura Launcher v{CURRENT_VERSION} запущен")
        self._log("[Launcher] github.com/vovaki-coger/neuro-killaura-visuals")
        self.root.mainloop()
