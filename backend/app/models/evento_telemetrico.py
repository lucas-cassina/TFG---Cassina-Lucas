from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from app.core.database import Base


class EventoTelemetrico(Base):
    __tablename__ = "eventos_telemetricos"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_conduccion.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    velocidad_kmh = Column(Float, nullable=False)
    aceleracion_ms2 = Column(Float, nullable=False)
    frenada_ms2 = Column(Float, nullable=False)
    latitud = Column(Float)
    longitud = Column(Float)
    tipo_evento = Column(String(50), default="normal")  # normal | frenada_brusca | aceleracion_brusca | exceso_velocidad
