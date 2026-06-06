from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recompensa(Base):
    __tablename__ = "recompensas"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    incentivo_id = Column(Integer, ForeignKey("incentivos.id"), nullable=False)
    nivel_alcanzado = Column(String(20), nullable=False)  # Bronce | Plata | Oro
    puntos_acumulados = Column(Integer, default=0)
    meses_consecutivos_bajo = Column(Integer, default=0)
    otorgada_en = Column(DateTime(timezone=True), server_default=func.now())

    conductor = relationship("Conductor", backref="recompensas")
    incentivo = relationship("Incentivo")
