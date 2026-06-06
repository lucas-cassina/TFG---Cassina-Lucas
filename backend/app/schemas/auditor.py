from pydantic import BaseModel
from typing import Optional


class AuditorOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    legajo: str
    email: str

    model_config = {"from_attributes": True}


class BusquedaAseguradoRequest(BaseModel):
    dni: Optional[str] = None
    numero_poliza: Optional[str] = None


class PerfilRiesgoAuditorOut(BaseModel):
    conductor_id: int
    nombre: str
    apellido: str
    dni: str
    email: str
    numero_poliza: Optional[str]
    marca_vehiculo: Optional[str]
    modelo_vehiculo: Optional[str]
    indice_actual: Optional[float]
    nivel_actual: Optional[str]
    indice_promedio_6m: Optional[float]
    total_sesiones: int
    total_km: float
    nivel_incentivo: Optional[str]
