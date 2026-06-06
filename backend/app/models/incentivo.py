from sqlalchemy import Column, Integer, String, Text, Boolean
from app.core.database import Base


class Incentivo(Base):
    __tablename__ = "incentivos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    nivel_requerido = Column(String(20), nullable=False)  # Bronce | Plata | Oro
    puntos_requeridos = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
