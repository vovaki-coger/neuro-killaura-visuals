"""
Авторизация: Microsoft OAuth, Mojang Legacy, Offline
"""
import json
import os
import threading
import webbrowser
import urllib.parse
import urllib.request
import http.server
from typing import Optional, Callable, Tuple

AUTH_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "auth_cache.json")

MICROSOFT_CLIENT_ID = "00000000402b5328"
MICROSOFT_REDIRECT = "https://login.live.com/oauth20_desktop.srf"
MICROSOFT_SCOPE = "XboxLive.signin%20offline_access"
MICROSOFT_AUTH_URL = (
    "https://login.live.com/oauth20_authorize.srf"
    f"?client_id={MICROSOFT_CLIENT_ID}"
    f"&response_type=code"
    f"&scope={MICROSOFT_SCOPE}"
    f"&redirect_uri={urllib.parse.quote(MICROSOFT_REDIRECT, safe='')}"
)


def load_auth_cache() -> dict:
    if os.path.exists(AUTH_CACHE_PATH):
        try:
            with open(AUTH_CACHE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_auth_cache(data: dict) -> None:
    os.makedirs(os.path.dirname(AUTH_CACHE_PATH), exist_ok=True)
    with open(AUTH_CACHE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def clear_auth_cache() -> None:
    if os.path.exists(AUTH_CACHE_PATH):
        os.remove(AUTH_CACHE_PATH)


class AuthManager:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or print
        self.cache = load_auth_cache()

    def offline_login(self, username: str) -> Tuple[bool, dict]:
        if not username or len(username) < 2:
            return False, {"error": "Никнейм слишком короткий"}
        profile = {
            "mode": "offline",
            "username": username,
            "uuid": "offline-" + username.lower().replace(" ", "_"),
            "token": "offline-token",
        }
        self.cache = profile
        save_auth_cache(profile)
        self.log(f"[Auth] Оффлайн вход: {username}")
        return True, profile

    def mojang_login(self, email: str, password: str) -> Tuple[bool, dict]:
        self.log("[Auth] Попытка Mojang-входа...")
        try:
            payload = json.dumps({
                "agent": {"name": "Minecraft", "version": 1},
                "username": email,
                "password": password,
                "requestUser": True,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://authserver.mojang.com/authenticate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            profile = {
                "mode": "mojang",
                "username": data["selectedProfile"]["name"],
                "uuid": data["selectedProfile"]["id"],
                "token": data["accessToken"],
            }
            self.cache = profile
            save_auth_cache(profile)
            self.log(f"[Auth] Mojang вход: {profile['username']}")
            return True, profile
        except Exception as e:
            self.log(f"[Auth] Ошибка Mojang: {e}")
            return False, {"error": str(e)}

    def microsoft_open_browser(self) -> None:
        self.log("[Auth] Открываю Microsoft OAuth в браузере...")
        webbrowser.open(MICROSOFT_AUTH_URL)

    def microsoft_finish_with_code(self, code: str) -> Tuple[bool, dict]:
        self.log("[Auth] Обмен кода Microsoft на токен...")
        try:
            payload = urllib.parse.urlencode({
                "client_id": MICROSOFT_CLIENT_ID,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": MICROSOFT_REDIRECT,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://login.live.com/oauth20_token.srf",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                ms_data = json.loads(resp.read())

            ms_token = ms_data.get("access_token", "")
            if not ms_token:
                return False, {"error": "Не получен MS-токен"}

            xbl = self._xbl_auth(ms_token)
            xsts = self._xsts_auth(xbl["token"])
            mc_token = self._mc_auth(xsts["token"], xsts["uhs"])

            profile = self._mc_profile(mc_token)
            result = {
                "mode": "microsoft",
                "username": profile.get("name", "Player"),
                "uuid": profile.get("id", ""),
                "token": mc_token,
            }
            self.cache = result
            save_auth_cache(result)
            self.log(f"[Auth] Microsoft вход: {result['username']}")
            return True, result
        except Exception as e:
            self.log(f"[Auth] Ошибка Microsoft: {e}")
            return False, {"error": str(e)}

    def _xbl_auth(self, ms_token: str) -> dict:
        payload = json.dumps({
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={ms_token}",
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://user.auth.xboxlive.com/user/authenticate",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return {"token": data["Token"], "uhs": data["DisplayClaims"]["xui"][0]["uhs"]}

    def _xsts_auth(self, xbl_token: str) -> dict:
        payload = json.dumps({
            "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl_token]},
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://xsts.auth.xboxlive.com/xsts/authorize",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return {"token": data["Token"], "uhs": data["DisplayClaims"]["xui"][0]["uhs"]}

    def _mc_auth(self, xsts_token: str, uhs: str) -> str:
        payload = json.dumps({
            "identityToken": f"XBL3.0 x={uhs};{xsts_token}"
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.minecraftservices.com/authentication/login_with_xbox",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data["access_token"]

    def _mc_profile(self, mc_token: str) -> dict:
        req = urllib.request.Request(
            "https://api.minecraftservices.com/minecraft/profile",
            headers={"Authorization": f"Bearer {mc_token}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())

    def restore_session(self) -> Optional[dict]:
        if self.cache and "username" in self.cache:
            self.log(f"[Auth] Восстановление сессии: {self.cache['username']}")
            return self.cache
        return None

    def logout(self) -> None:
        self.cache = {}
        clear_auth_cache()
        self.log("[Auth] Выход из аккаунта")
