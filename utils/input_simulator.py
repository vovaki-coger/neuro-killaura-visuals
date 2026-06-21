"""
Симуляция ввода — мышь и клавиатура
Использует ctypes (Windows) или pynput (кроссплатформенный fallback)
"""
import sys
import time
import random


def click_left(hold_ms: float = 10.0) -> None:
    """Левый клик мыши."""
    if sys.platform == "win32":
        _click_win32_left(hold_ms)
    else:
        _click_pynput(hold_ms)


def move_mouse(dx: int, dy: int) -> None:
    """Относительное перемещение мыши."""
    if sys.platform == "win32":
        _move_win32(dx, dy)
    else:
        _move_pynput(dx, dy)


def _click_win32_left(hold_ms: float) -> None:
    try:
        import ctypes
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(hold_ms / 1000.0 + random.uniform(0, 0.005))
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    except Exception as e:
        print(f"[Input] win32 click error: {e}")


def _move_win32(dx: int, dy: int) -> None:
    try:
        import ctypes
        MOUSEEVENTF_MOVE = 0x0001
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
    except Exception as e:
        print(f"[Input] win32 move error: {e}")


def _click_pynput(hold_ms: float) -> None:
    try:
        from pynput.mouse import Button, Controller
        mouse = Controller()
        mouse.press(Button.left)
        time.sleep(hold_ms / 1000.0)
        mouse.release(Button.left)
    except Exception as e:
        print(f"[Input] pynput click error: {e}")


def _move_pynput(dx: int, dy: int) -> None:
    try:
        from pynput.mouse import Controller
        mouse = Controller()
        mouse.move(dx, dy)
    except Exception as e:
        print(f"[Input] pynput move error: {e}")
