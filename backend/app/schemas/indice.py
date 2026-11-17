from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IndiceRiesgoOut(BaseModel):
    id: int
    sesion_id: int
    indice: float
    nivel: str
    puntaje_velocidad: Optional[float]
    puntaje_frenadas: Optional[float]
    puntaje_aceleraciones: Optional[float]
    puntaje_horario: Optional[float]
    puntaje_distancia: Optional[float]
    distancia_km: Optional[float]
    calculado_en: datetime

    model_config = {"from_attributes": True}


class EstadisticasMesOut(BaseModel):
    indice_promedio: float
    nivel_predominante: str
    total_sesiones: int
    total_km: float
    alertas_totales: int


class HistorialSesionOut(BaseModel):
    sesion_id: int
    inicio: datetime
    fin: Optional[datetime]
    indice: Optional[float]
    nivel: Optional[str]
    distancia_km: Optional[float]
    alertas_count: int = 0

    model_config = {"from_attributes": True}


class AlertaOut(BaseModel):
    tipo_alerta: str
    descripcion: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}


class SesionDetalleOut(BaseModel):
    sesion_id: int
    inicio: datetime
    fin: Optional[datetime]
    indice: Optional[float]
    nivel: Optional[str]
    distancia_km: Optional[float]
    puntaje_velocidad: Optional[float]
    puntaje_frenadas: Optional[float]
    puntaje_aceleraciones: Optional[float]
    puntaje_horario: Optional[float]
    puntaje_distancia: Optional[float]
    alertas: List[AlertaOut] = []

    model_config = {"from_attributes": True}
