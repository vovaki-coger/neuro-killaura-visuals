"""
Автономный KillAura-воркер — запускается как отдельный процесс вместе с Minecraft.

Работает полностью в фоне:
- Хоткеи работают даже когда Minecraft в фокусе (pynput global listener)
- R     — вкл/выкл KillAura (автокликер)
- G     — вкл/выкл визуалы (пишет в runtime_state.json)
- H     — вкл/выкл HUD
- INSERT — показать статус в консоли
- END    — выход

KillAura = автокликер с человекоподобным таймингом (AttackTimer + AntiDetect).
Клики идут через ctypes.mouse_event (Windows), обходя DirectInput-проверки.
"""
import sys
import os
import time
import json
import threading
import random
import ctypes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from neuro_killaura.attack_timer import AttackTimer
from neuro_killaura.anti_detect import AntiDetect

STATE_PATH  = os.path.join(BASE_DIR, "configs", "runtime_state.json")
CONFIG_PATH = os.path.join(BASE_DIR, "configs", "user.json")
DEFAULT_CFG = os.path.join(BASE_DIR, "configs", "default.json")

# ─── Загрузка конфига ─────────────────────────────────────────────────────────

def _load_cfg() -> dict:
    for p in [CONFIG_PATH, DEFAULT_CFG]:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


# ─── Запись runtime state (для overlay) ──────────────────────────────────────

def _write_state(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, STATE_PATH)
    except Exception:
        pass


# ─── Клик мыши (Windows ctypes) ──────────────────────────────────────────────

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

def _do_click(hold_ms: float = 12.0) -> None:
    """Левый клик через Windows API (работает внутри Minecraft)."""
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(hold_ms / 1000.0 + random.uniform(0.0, 0.006))
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP,   0, 0, 0, 0)
            return
        except Exception:
            pass
    # Fallback: pynput
    try:
        from pynput.mouse import Button, Controller
        m = Controller()
        m.press(Button.left)
        time.sleep(hold_ms / 1000.0)
        m.release(Button.left)
    except Exception as e:
        print(f"[KillAura] click error: {e}")


# ─── Основной воркер ──────────────────────────────────────────────────────────

class KillAuraWorker:
    def __init__(self):
        cfg = _load_cfg()
        ka  = cfg.get("killaura", {})

        self.min_cps    = ka.get("min_cps", 8.0)
        self.max_cps    = ka.get("max_cps", 14.0)
        self.confidence = 0.88

        self._timer       = AttackTimer(self.min_cps, self.max_cps)
        self._anti_detect = AntiDetect()

        self.killaura_on = False
        self.visuals_on  = True
        self.hud_on      = True
        self.combo       = 0
        self._running    = True

        # Запуск основного цикла
        self._loop_thread = threading.Thread(target=self._loop, daemon=True)
        self._loop_thread.start()

        print("[KillAura Worker] Запущен.")
        print("  R      — вкл/выкл KillAura")
        print("  G      — вкл/выкл визуалы")
        print("  H      — вкл/выкл HUD")
        print("  INSERT — статус")
        print("  END    — выход")

    # ── Главный цикл автокликера ──────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            if self.killaura_on and not self._anti_detect.is_pausing():
                if self._timer.should_attack(self.confidence):
                    if not self._anti_detect.should_misclick():
                        _do_click()
                        self.combo += 1
                self._anti_detect.maybe_pause()
            else:
                self.combo = 0

            # Пишем состояние каждые ~100 мс
            _write_state({
                "killaura_enabled": self.killaura_on,
                "visuals_enabled":  self.visuals_on,
                "hud_enabled":      self.hud_on,
                "cps":              self._timer.current_cps(self.confidence) if self.killaura_on else 0.0,
                "combo":            self.combo,
                "confidence":       self.confidence,
                "target":           None,
            })

            time.sleep(1.0 / 240.0)

    # ── Хоткеи (pynput — работают в любом активном окне) ─────────────────────

    def run_with_hotkeys(self) -> None:
        try:
            from pynput.keyboard import Key, Listener
        except ImportError:
            print("[KillAura] pynput не найден — хоткеи недоступны. Установи: pip install pynput")
            self._loop_thread.join()
            return

        def on_press(key):
            try:
                ch = getattr(key, "char", None)
                if ch == "r":
                    self.killaura_on = not self.killaura_on
                    status = "ВКЛ ✅" if self.killaura_on else "ВЫКЛ ❌"
                    print(f"[KillAura] {status}")
                elif ch == "g":
                    self.visuals_on = not self.visuals_on
                    print(f"[Visuals] {'ВКЛ ✅' if self.visuals_on else 'ВЫКЛ ❌'}")
                elif ch == "h":
                    self.hud_on = not self.hud_on
                    print(f"[HUD] {'ВКЛ ✅' if self.hud_on else 'ВЫКЛ ❌'}")
            except Exception:
                pass
            try:
                if key == Key.insert:
                    cps = self._timer.current_cps(self.confidence)
                    print(f"[Status] KA={'ON' if self.killaura_on else 'OFF'}"
                          f" | CPS={cps:.1f} | Combo={self.combo}"
                          f" | Visuals={'ON' if self.visuals_on else 'OFF'}")
                elif key == Key.end:
                    print("[KillAura] Выход...")
                    self._running = False
                    return False  # Stop listener
            except Exception:
                pass

        print("[KillAura Worker] Слушаю хоткеи...")
        with Listener(on_press=on_press) as listener:
            listener.join()

        self._running = False


# ─── Точка входа ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    worker = KillAuraWorker()
    worker.run_with_hotkeys()
