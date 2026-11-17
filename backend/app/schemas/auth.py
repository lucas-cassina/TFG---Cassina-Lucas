import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date


def _validar_complejidad(v: str) -> str:
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", v):
        raise ValueError("La contraseña debe contener al menos una mayúscula")
    if not re.search(r"[a-z]", v):
        raise ValueError("La contraseña debe contener al menos una minúscula")
    if not re.search(r"\d", v):
        raise ValueError("La contraseña debe contener al menos un número")
    return v


class ConductorRegistro(BaseModel):
    nombre: str
    apellido: str
    dni: str
    email: EmailStr
    password: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validar_complejidad(v)


class AuditorRegistro(BaseModel):
    nombre: str
    apellido: str
    legajo: str
    email: EmailStr
    password: str
    codigo_registro: str  # debe coincidir con AUDITOR_REGISTRATION_SECRET (A3)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validar_complejidad(v)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    nombre: str
    apellido: str
