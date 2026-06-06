from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class ConductorRegistro(BaseModel):
    nombre: str
    apellido: str
    dni: str
    email: EmailStr
    password: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None


class AuditorRegistro(BaseModel):
    nombre: str
    apellido: str
    legajo: str
    email: EmailStr
    password: str


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
