from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.models.conductor import Conductor
from app.models.auditor import Auditor
from app.schemas.auth import ConductorRegistro, AuditorRegistro, LoginRequest, TokenResponse
from app.services.tokens import revocar_token
from app.services.passwords import guardar_contrasena

router = APIRouter(prefix="/auth", tags=["autenticación"])
bearer_scheme = HTTPBearer()

MAX_INTENTOS = 5
LOCKOUT_MINUTOS = 30


@router.post("/registro/conductor", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registrar_conductor(data: ConductorRegistro, db: AsyncSession = Depends(get_db)):
    """HU-001: Registro de asegurado."""
    res = await db.execute(select(Conductor).where(
        (Conductor.email == data.email) | (Conductor.dni == data.dni)
    ))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email o DNI ya registrado")

    conductor = Conductor(
        nombre=data.nombre,
        apellido=data.apellido,
        dni=data.dni,
        email=data.email,
        hashed_password=hash_password(data.password),
        telefono=data.telefono,
        fecha_nacimiento=data.fecha_nacimiento,
    )
    db.add(conductor)
    await db.commit()
    await db.refresh(conductor)

    await guardar_contrasena(conductor.id, "conductor", conductor.hashed_password, db)

    token = create_access_token({"sub": str(conductor.id), "role": "conductor"})
    return TokenResponse(
        access_token=token, role="conductor",
        user_id=conductor.id, nombre=conductor.nombre, apellido=conductor.apellido
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """HU-002: Inicio de sesión con bloqueo tras 5 intentos fallidos (tesis pág. 43)."""
    res = await db.execute(select(Conductor).where(Conductor.email == data.email))
    user = res.scalar_one_or_none()
    role = "conductor"

    if not user:
        res = await db.execute(select(Auditor).where(Auditor.email == data.email))
        user = res.scalar_one_or_none()
        role = "auditor"

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar bloqueo temporal
    # SQLite devuelve datetimes naive aunque la columna tenga timezone=True;
    # normalizamos a UTC antes de comparar.
    now = datetime.now(timezone.utc)
    bloqueado_hasta = user.bloqueado_hasta
    if bloqueado_hasta and bloqueado_hasta.tzinfo is None:
        bloqueado_hasta = bloqueado_hasta.replace(tzinfo=timezone.utc)
    if bloqueado_hasta and bloqueado_hasta > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Cuenta bloqueada temporalmente. Intente nuevamente a las "
                   f"{bloqueado_hasta.strftime('%H:%M UTC')}.",
        )

    if not verify_password(data.password, user.hashed_password):
        user.intentos_fallidos += 1
        if user.intentos_fallidos >= MAX_INTENTOS:
            user.bloqueado_hasta = now + timedelta(minutes=LOCKOUT_MINUTOS)
            user.intentos_fallidos = 0
        await db.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Login exitoso — resetear contador
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    await db.commit()

    token = create_access_token({"sub": str(user.id), "role": role})
    return TokenResponse(
        access_token=token, role=role,
        user_id=user.id, nombre=user.nombre, apellido=user.apellido
    )


@router.post("/logout", status_code=204)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """HU-011/012: Cierre de sesión con invalidación de token persistida en DB (tesis pág. 44)."""
    token = credentials.credentials
    # Extraer expiry del JWT para permitir limpieza automática de la blacklist (B4)
    payload = decode_token(token)
    expires_at = None
    if payload and payload.get("exp"):
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    await revocar_token(token, db, expires_at=expires_at)
    return None


@router.post("/registro/auditor", response_model=TokenResponse, status_code=201)
async def registrar_auditor(data: AuditorRegistro, db: AsyncSession = Depends(get_db)):
    """Registro de auditor protegido por código de registro (A3)."""
    if data.codigo_registro != settings.AUDITOR_REGISTRATION_SECRET:
        raise HTTPException(status_code=403, detail="Código de registro inválido")

    res = await db.execute(select(Auditor).where(
        (Auditor.email == data.email) | (Auditor.legajo == data.legajo)
    ))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email o legajo ya registrado")

    auditor = Auditor(
        nombre=data.nombre, apellido=data.apellido, legajo=data.legajo,
        email=data.email, hashed_password=hash_password(data.password),
    )
    db.add(auditor)
    await db.commit()
    await db.refresh(auditor)

    await guardar_contrasena(auditor.id, "auditor", auditor.hashed_password, db)

    token = create_access_token({"sub": str(auditor.id), "role": "auditor"})
    return TokenResponse(
        access_token=token, role="auditor",
        user_id=auditor.id, nombre=auditor.nombre, apellido=auditor.apellido
    )
