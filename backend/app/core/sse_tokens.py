"""
Tokens SSE efímeros (A1).

EventSource no soporta headers custom, por lo que pasar el JWT en la URL
quedaría expuesto en logs de servidor e historial del browser. Este módulo
emite tokens de vida corta (60 s) y single-use que se pasan en la query string
en lugar del JWT completo.

LIMITACIÓN: el store es in-memory. En un deployment multi-worker (Gunicorn
con múltiples procesos) un token emitido en el worker A no puede consumirse
en el worker B. Este sistema asume un único proceso asyncio. Para multi-worker,
migrar a Redis con TTL y DEL atómico.
"""

import secrets
from datetime import datetime, timedelta, timezone

_sse_tokens: dict[str, dict] = {}
_SSE_TOKEN_TTL_SECONDS = 60


def issue_sse_token(conductor_id: int) -> str:
    """Genera y registra un token SSE efímero vinculado a conductor_id."""
    token = secrets.token_urlsafe(32)
    _sse_tokens[token] = {
        "conductor_id": conductor_id,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=_SSE_TOKEN_TTL_SECONDS),
    }
    _cleanup_expired()
    return token


def consume_sse_token(token: str) -> int | None:
    """Valida y consume el token SSE (single-use). Devuelve conductor_id o None."""
    entry = _sse_tokens.pop(token, None)
    if not entry:
        return None
    if entry["expires_at"] < datetime.now(timezone.utc):
        return None
    return entry["conductor_id"]


def _cleanup_expired() -> None:
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _sse_tokens.items() if v["expires_at"] < now]
    for k in expired:
        del _sse_tokens[k]
