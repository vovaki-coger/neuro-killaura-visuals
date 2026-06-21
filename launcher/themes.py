"""
Темы оформления лаунчера
"""

THEMES = {
    "dark": {
        "bg": "#0d0d0f",
        "bg2": "#141416",
        "bg3": "#1a1a1e",
        "frame_bg": "#1e1e24",
        "accent": "#e53935",
        "accent2": "#ff5252",
        "text": "#ffffff",
        "text2": "#aaaaaa",
        "text3": "#666666",
        "border": "#2a2a32",
        "success": "#00c853",
        "warning": "#ffab00",
        "error": "#ff1744",
        "button_hover": "#c62828",
        "entry_bg": "#16161a",
        "scrollbar": "#2a2a32",
        "tag": "dark",
    },
    "light": {
        "bg": "#f5f5f5",
        "bg2": "#eeeeee",
        "bg3": "#e0e0e0",
        "frame_bg": "#fafafa",
        "accent": "#e53935",
        "accent2": "#ff5252",
        "text": "#111111",
        "text2": "#444444",
        "text3": "#888888",
        "border": "#cccccc",
        "success": "#00c853",
        "warning": "#ffab00",
        "error": "#ff1744",
        "button_hover": "#c62828",
        "entry_bg": "#ffffff",
        "scrollbar": "#cccccc",
        "tag": "light",
    },
    "purple": {
        "bg": "#0e0a14",
        "bg2": "#130f1c",
        "bg3": "#1a1428",
        "frame_bg": "#1e1830",
        "accent": "#9c27b0",
        "accent2": "#ce93d8",
        "text": "#ffffff",
        "text2": "#ccbbdd",
        "text3": "#776688",
        "border": "#2e2240",
        "success": "#00c853",
        "warning": "#ffab00",
        "error": "#ff1744",
        "button_hover": "#7b1fa2",
        "entry_bg": "#110d1a",
        "scrollbar": "#2e2240",
        "tag": "dark",
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["dark"])
