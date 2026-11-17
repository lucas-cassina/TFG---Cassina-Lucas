from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class HistorialContrasena(Base):
    """Almacena las últimas contraseñas de cada usuario para evitar reutilización (tesis pág. 43)."""

    __tablename__ = "historial_contrasenas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_type = Column(String(20), nullable=False)   # conductor | auditor
    hashed_password = Column(String(400), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
