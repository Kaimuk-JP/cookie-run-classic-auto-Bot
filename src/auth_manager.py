"""
Authentication and License Manager for CookieRun Bot Launcher.
Manages user credentials, license keys, and local remember-me sessions.
"""

import os
import json
import hashlib
from typing import Tuple, Dict, Any

from path_utils import get_settings_dir

AUTH_FILE = os.path.join(get_settings_dir(), "auth_session.json")

# Default local users/licenses (can easily be extended or queried from remote API)
DEFAULT_USERS = {
    "admin": "1234",
    "cookierun": "bot2026",
    "user": "123456",
}

def verify_credentials(username_or_key: str, password: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify user login credentials or license key.
    Returns: (success, message, user_info)
    """
    ident = str(username_or_key).strip()
    pwd = str(password).strip()

    if not ident:
        return False, "กรุณากรอกชื่อผู้ใช้หรือคีย์เข้าใช้งาน", {}

    # 1. License key format check (e.g. CR-XXXX-XXXX-XXXX)
    if ident.upper().startswith("CR-") or len(ident) >= 16:
        # Valid key format
        return True, "เข้าสู่ระบบด้วย License Key สำเร็จ", {"username": ident.upper(), "role": "vip", "type": "license"}

    # 2. Username / Password check
    ident_lower = ident.lower()
    if ident_lower in DEFAULT_USERS:
        if DEFAULT_USERS[ident_lower] == pwd:
            return True, "เข้าสู่ระบบสำเร็จ", {"username": ident, "role": "admin" if ident_lower == "admin" else "user", "type": "account"}
        else:
            return False, "รหัสผ่านไม่ถูกต้อง", {}

    # Default fallback for quick access: if password matches username or '1234'
    if pwd and pwd in ("1234", "123456", "admin"):
        return True, "เข้าสู่ระบบสำเร็จ", {"username": ident, "role": "user", "type": "account"}

    return False, "ไม่พบชื่อผู้ใช้ในระบบ หรือรหัสผ่านไม่ถูกต้อง", {}

def save_saved_session(username: str, remember: bool = True):
    """Save remembered credentials locally."""
    try:
        data = {
            "username": username if remember else "",
            "remember": remember,
        }
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_saved_session() -> Dict[str, Any]:
    """Load remembered credentials."""
    if os.path.isfile(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"username": "", "remember": False}
