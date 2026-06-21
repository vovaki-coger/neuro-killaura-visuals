"""
Автообновление — проверка версии на GitHub Releases
"""
import json
import urllib.request
import threading
from typing import Callable, Optional

CURRENT_VERSION = "2.0.0"
GITHUB_API_URL = "https://api.github.com/repos/vovaki-coger/neuro-killaura-visuals/releases/latest"


class Updater:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or print
        self.latest_version: Optional[str] = None
        self.download_url: Optional[str] = None

    def check_async(self, on_result: Callable[[bool, str], None]) -> None:
        def _check():
            has_update, info = self.check()
            on_result(has_update, info)
        t = threading.Thread(target=_check, daemon=True)
        t.start()

    def check(self) -> tuple[bool, str]:
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "NeuroKillAura-Launcher"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            tag = data.get("tag_name", "v0.0.0").lstrip("v")
            self.latest_version = tag

            assets = data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".exe") or name.endswith(".zip"):
                    self.download_url = asset["browser_download_url"]
                    break

            if self._version_gt(tag, CURRENT_VERSION):
                self.log(f"[Updater] Доступна новая версия: v{tag}")
                return True, f"Доступна версия v{tag}"
            else:
                self.log(f"[Updater] Актуальная версия: v{CURRENT_VERSION}")
                return False, f"Версия актуальна (v{CURRENT_VERSION})"
        except Exception as e:
            self.log(f"[Updater] Ошибка проверки обновлений: {e}")
            return False, f"Ошибка: {e}"

    def _version_gt(self, a: str, b: str) -> bool:
        try:
            av = tuple(int(x) for x in a.split("."))
            bv = tuple(int(x) for x in b.split("."))
            return av > bv
        except Exception:
            return False
