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
