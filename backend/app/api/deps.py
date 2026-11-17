from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.models.conductor import Conductor
from app.models.auditor import Auditor
from app.services.tokens import es_token_revocado
from app.core.sse_tokens import consume_sse_token

bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Helpers internos — evitan duplicación entre get_current_* y get_conductor_sse
# ---------------------------------------------------------------------------

async def _resolver_conductor(token: str, db: AsyncSession) -> Conductor:
    """Valida un JWT de conductor y devuelve el objeto Conductor."""
    if await es_token_revocado(token, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    payload = decode_token(token)
    if not payload or payload.get("role") != "conductor":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    try:
        conductor_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    result = await db.execute(select(Conductor).where(Conductor.id == conductor_id))
    conductor = result.scalar_one_or_none()
    if not conductor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conductor no encontrado")
    return conductor


async def _resolver_auditor(token: str, db: AsyncSession) -> Auditor:
    """Valida un JWT de auditor y devuelve el objeto Auditor."""
    if await es_token_revocado(token, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    payload = decode_token(token)
    if not payload or payload.get("role") != "auditor":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    try:
        auditor_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    result = await db.execute(select(Auditor).where(Auditor.id == auditor_id))
    auditor = result.scalar_one_or_none()
    if not auditor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditor no encontrado")
    return auditor


# ---------------------------------------------------------------------------
# Dependencias públicas
# ---------------------------------------------------------------------------

async def get_current_conductor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Conductor:
    return await _resolver_conductor(credentials.credentials, db)


async def get_conductor_sse(
    sse_token: str | None = Query(None),
    token: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Conductor:
    """
    Dependencia para el endpoint SSE. Orden de prioridad:
    1. ?sse_token= — token efímero de 60 s (flujo normal del frontend)
    2. ?token=     — JWT directo (fallback para pruebas en el browser)
    3. Bearer header — útil desde curl/Swagger
    """
    if sse_token:
        conductor_id = consume_sse_token(sse_token)
        if conductor_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token SSE inválido o expirado",
            )
        result = await db.execute(select(Conductor).where(Conductor.id == conductor_id))
        conductor = result.scalar_one_or_none()
        if not conductor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conductor no encontrado")
        return conductor

    raw = token or (credentials.credentials if credentials else None)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await _resolver_conductor(raw, db)


async def get_current_auditor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Auditor:
    return await _resolver_auditor(credentials.credentials, db)
