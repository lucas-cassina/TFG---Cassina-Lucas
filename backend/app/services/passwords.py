"""
Historial de contraseñas para evitar reutilización (tesis pág. 43).

"El sistema tampoco permite reutilizar ninguna de las últimas tres (3)
contraseñas utilizadas por el mismo usuario."
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.historial_contrasena import HistorialContrasena
from app.core.security import verify_password

MAX_HISTORIAL = 3


async def guardar_contrasena(
    user_id: int, user_type: str, hashed_password: str, db: AsyncSession
) -> None:
    """Registra la contraseña hasheada en el historial del usuario."""
    db.add(HistorialContrasena(
        user_id=user_id,
        user_type=user_type,
        hashed_password=hashed_password,
    ))
    await db.commit()


async def es_contrasena_reutilizada(
    user_id: int, user_type: str, plain_password: str, db: AsyncSession
) -> bool:
    """
    Devuelve True si plain_password coincide con alguna de las últimas
    MAX_HISTORIAL contraseñas almacenadas para ese usuario.
    """
    res = await db.execute(
        select(HistorialContrasena)
        .where(
            HistorialContrasena.user_id == user_id,
            HistorialContrasena.user_type == user_type,
        )
        .order_by(HistorialContrasena.creado_en.desc())
        .limit(MAX_HISTORIAL)
    )
    historial = res.scalars().all()
    return any(verify_password(plain_password, h.hashed_password) for h in historial)
