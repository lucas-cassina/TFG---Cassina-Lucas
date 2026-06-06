from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.core.database import Base


class AlertaConduccion(Base):
    __tablename__ = "alertas_conduccion"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_conduccion.id"), nullable=False, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    tipo_alerta = Column(String(60), nullable=False)  # exceso_velocidad | frenada_brusca | aceleracion_brusca
    descripcion = Column(String(300))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
