from __future__ import annotations
import os
from typing import Optional
from app.models import User


def _admin_usernames() -> set[str]:
    raw = os.environ.get("ADMIN_USERS", "").strip()
    if not raw:
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}


def _admin_user_ids() -> set[int]:
    raw = os.environ.get("ADMIN_USER_IDS", "").strip()
    out: set[int] = set()
    if not raw:
        return out
    for x in raw.split(","):
        x = x.strip()
        if not x:
            continue
        try:
            out.add(int(x))
        except Exception:
            pass
    return out


def is_admin(user_id: int) -> bool:
    ids = _admin_user_ids()
    if user_id in ids:
        return True
    u: Optional[User] = User.query.get(int(user_id))
    if not u:
        return False
    # 始终将用户名 'admin' 视为管理员（内置超级用户）
    if u.username == 'admin':
        return True
    names = _admin_usernames()
    if names:
        return u.username in names
    return False
