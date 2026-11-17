import hashlib
import secrets
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError

from .config import settings


# ---------------------------------------------------------------------------
# Password hashing — PBKDF2-HMAC-SHA256 via stdlib, 260 000 iteraciones
# OWASP Password Storage Cheat Sheet (tesis pág. 43)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000
    )
    return f"pbkdf2$sha256$260000${salt}${base64.b64encode(key).decode()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        _, _alg, iters, salt, stored = hashed_password.split("$")
        key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), int(iters)
        )
        return secrets.compare_digest(base64.b64encode(key).decode(), stored)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT — PyJWT con HS256
# La revocación de tokens se persiste en DB (ver services/tokens.py)
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except InvalidTokenError:
        return None
