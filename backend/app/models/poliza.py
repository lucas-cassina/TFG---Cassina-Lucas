from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Poliza(Base):
    __tablename__ = "polizas"

    id = Column(Integer, primary_key=True, index=True)
    numero_poliza = Column(String(50), unique=True, nullable=False, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False)
    marca_vehiculo = Column(String(100), nullable=False)
    modelo_vehiculo = Column(String(100), nullable=False)
    anio_vehiculo = Column(Integer, nullable=False)
    patente = Column(String(20), nullable=False)
    zona = Column(String(100))
    fecha_inicio = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conductor = relationship("Conductor", backref="polizas")
