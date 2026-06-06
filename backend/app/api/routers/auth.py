from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, revoke_token
from app.models.conductor import Conductor
from app.models.auditor import Auditor
from app.schemas.auth import ConductorRegistro, AuditorRegistro, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["autenticación"])
bearer_scheme = HTTPBearer()


@router.post("/registro/conductor", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registrar_conductor(data: ConductorRegistro, db: AsyncSession = Depends(get_db)):
    """HU-001: Registro de asegurado."""
    # Verificar unicidad
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

    token = create_access_token({"sub": str(conductor.id), "role": "conductor"})
    return TokenResponse(
        access_token=token, role="conductor",
        user_id=conductor.id, nombre=conductor.nombre, apellido=conductor.apellido
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """HU-002: Inicio de sesión (conductor o auditor)."""
    # Intentar como conductor
    res = await db.execute(select(Conductor).where(Conductor.email == data.email))
    user = res.scalar_one_or_none()
    role = "conductor"

    if not user:
        res = await db.execute(select(Auditor).where(Auditor.email == data.email))
        user = res.scalar_one_or_none()
        role = "auditor"

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({"sub": str(user.id), "role": role})
    return TokenResponse(
        access_token=token, role=role,
        user_id=user.id, nombre=user.nombre, apellido=user.apellido
    )


@router.post("/logout", status_code=204)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """HU-011/012: Cierre de sesión con invalidación de token en servidor."""
    revoke_token(credentials.credentials)
    return None


@router.post("/registro/auditor", response_model=TokenResponse, status_code=201)
async def registrar_auditor(data: AuditorRegistro, db: AsyncSession = Depends(get_db)):
    """Registro de auditor."""
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

    token = create_access_token({"sub": str(auditor.id), "role": "auditor"})
    return TokenResponse(
        access_token=token, role="auditor",
        user_id=auditor.id, nombre=auditor.nombre, apellido=auditor.apellido
    )
