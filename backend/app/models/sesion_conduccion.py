from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SesionConduccion(Base):
    __tablename__ = "sesiones_conduccion"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    poliza_id = Column(Integer, ForeignKey("polizas.id"), nullable=True)
    inicio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fin = Column(DateTime(timezone=True))
    estado = Column(String(20), default="activa")  # activa | cerrada | procesada
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conductor = relationship("Conductor", backref="sesiones")
    eventos = relationship("EventoTelemetrico", backref="sesion", cascade="all, delete-orphan")
    indice = relationship("IndiceRiesgo", backref="sesion", uselist=False)
    alertas = relationship("AlertaConduccion", backref="sesion", cascade="all, delete-orphan")
