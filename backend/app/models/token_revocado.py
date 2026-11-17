from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class TokenRevocado(Base):
    __tablename__ = "tokens_revocados"

    id = Column(Integer, primary_key=True, index=True)
    # SHA-256 del JWT (64 chars fijos): índice más eficiente y no expone el token si la DB se compromete
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    revocado_en = Column(DateTime(timezone=True), server_default=func.now())
    # Expiry del JWT original: permite limpiar entradas ya inválidas (B4)
    expires_at = Column(DateTime(timezone=True), nullable=True)
