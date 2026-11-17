from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class Auditor(Base):
    __tablename__ = "auditores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    legajo = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(400), nullable=False)
    # Política de bloqueo temporal tras intentos fallidos (tesis pág. 43)
    intentos_fallidos = Column(Integer, nullable=False, default=0, server_default="0")
    bloqueado_hasta = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
