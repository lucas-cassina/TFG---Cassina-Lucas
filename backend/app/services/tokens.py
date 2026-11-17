"""
Gestión de tokens revocados persistidos en base de datos (HU-011 / HU-012).

La tesis especifica (pág. 44) que la blacklist de tokens debe ser
"persistida en base de datos" para sobrevivir reinicios del servidor.

Cambios aplicados en el review:
- A6: se almacena el hash SHA-256 del token (64 chars) en vez del JWT completo.
- B4: se persiste expires_at para poder limpiar entradas expiradas.
"""

import hashlib
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.token_revocado import TokenRevocado


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def revocar_token(
    token: str,
    db: AsyncSession,
    expires_at: datetime | None = None,
) -> None:
    """Persiste el hash del token en la blacklist; ignora duplicados."""
    token_hash = _hash_token(token)
    res = await db.execute(
        select(TokenRevocado).where(TokenRevocado.token_hash == token_hash)
    )
    if not res.scalar_one_or_none():
        db.add(TokenRevocado(token_hash=token_hash, expires_at=expires_at))
        await db.commit()


async def es_token_revocado(token: str, db: AsyncSession) -> bool:
    """Devuelve True si el hash del token está en la blacklist persistida."""
    token_hash = _hash_token(token)
    res = await db.execute(
        select(TokenRevocado).where(TokenRevocado.token_hash == token_hash)
    )
    return res.scalar_one_or_none() is not None


async def limpiar_tokens_expirados(db: AsyncSession) -> int:
    """Elimina tokens revocados cuyo JWT ya expiró. Devuelve la cantidad eliminada."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        delete(TokenRevocado).where(
            TokenRevocado.expires_at.is_not(None),
            TokenRevocado.expires_at < now,
        )
    )
    await db.commit()
    return result.rowcount
