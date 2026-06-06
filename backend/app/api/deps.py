from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token, is_token_revoked
from app.models.conductor import Conductor
from app.models.auditor import Auditor

bearer_scheme = HTTPBearer()


async def get_current_conductor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Conductor:
    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    payload = decode_token(token)
    if not payload or payload.get("role") != "conductor":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    conductor_id = payload.get("sub")
    result = await db.execute(select(Conductor).where(Conductor.id == int(conductor_id)))
    conductor = result.scalar_one_or_none()
    if not conductor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conductor no encontrado")
    return conductor


async def get_current_auditor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Auditor:
    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    payload = decode_token(token)
    if not payload or payload.get("role") != "auditor":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    auditor_id = payload.get("sub")
    result = await db.execute(select(Auditor).where(Auditor.id == int(auditor_id)))
    auditor = result.scalar_one_or_none()
    if not auditor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditor no encontrado")
    return auditor
