from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class ConductorOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    email: EmailStr
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PolizaOut(BaseModel):
    id: int
    numero_poliza: str
    marca_vehiculo: str
    modelo_vehiculo: str
    anio_vehiculo: int
    patente: str
    zona: Optional[str] = None
    fecha_inicio: date
    fecha_vencimiento: date

    model_config = {"from_attributes": True}


class PerfilConductorOut(BaseModel):
    conductor: ConductorOut
    poliza: Optional[PolizaOut] = None


class PolizaIn(BaseModel):
    numero_poliza: str
    marca_vehiculo: str
    modelo_vehiculo: str
    anio_vehiculo: int
    patente: str
    zona: Optional[str] = None
    fecha_inicio: date
    fecha_vencimiento: date


class CambioContrasenaRequest(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str
