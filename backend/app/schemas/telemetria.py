from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AperturaSesionRequest(BaseModel):
    poliza_id: Optional[int] = None


class AperturaSesionResponse(BaseModel):
    sesion_id: int
    inicio: datetime
    estado: str


class EventoTelemetricoIn(BaseModel):
    timestamp: Optional[datetime] = None
    velocidad_kmh: float
    aceleracion_ms2: float
    frenada_ms2: float
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class LoteEventosRequest(BaseModel):
    sesion_id: int
    eventos: List[EventoTelemetricoIn]


class CierreSesionRequest(BaseModel):
    sesion_id: int


class AlertaOut(BaseModel):
    id: int
    sesion_id: int
    tipo_alerta: str
    descripcion: str
    timestamp: datetime

    model_config = {"from_attributes": True}
