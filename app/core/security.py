import re
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

_EXPIRATION_RE = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def expiration_to_seconds(expiration: str | None = None) -> int:
    """Convert strings such as ``8h`` / ``30m`` to seconds (default 8h)."""
    value = (expiration or "8h").strip()
    match = _EXPIRATION_RE.match(value)
    if not match:
        return 8 * 3600
    amount = int(match.group(1))
    return amount * _UNIT_SECONDS[match.group(2)]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(*, user_id: int, username: str, role: str) -> tuple[str, int]:
    expires_in = expiration_to_seconds(settings.jwt_expiration)
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str) -> dict:
    # PyJWT >= 2.10 validates that ``sub`` is a string unless explicitly disabled.
    # The legacy contract uses an integer ``sub``, so verification is disabled here.
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"verify_sub": False},
    )
