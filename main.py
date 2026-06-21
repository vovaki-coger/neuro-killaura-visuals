"""
Neuro KillAura Launcher — точка входа
"""
import sys
import os

# Добавляем папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from launcher.gui import LauncherApp

if __name__ == "__main__":
    app = LauncherApp()
    app.run()
