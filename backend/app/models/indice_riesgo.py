from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from app.core.database import Base


class IndiceRiesgo(Base):
    __tablename__ = "indices_riesgo"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_conduccion.id"), unique=True, nullable=False, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    indice = Column(Float, nullable=False)           # 0-100
    nivel = Column(String(10), nullable=False)        # Bajo | Medio | Alto
    puntaje_velocidad = Column(Float)
    puntaje_frenadas = Column(Float)
    puntaje_aceleraciones = Column(Float)
    puntaje_horario = Column(Float)
    puntaje_distancia = Column(Float)
    distancia_km = Column(Float)
    calculado_en = Column(DateTime(timezone=True), server_default=func.now())
