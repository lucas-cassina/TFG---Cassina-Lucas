from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RecompensaOut(BaseModel):
    id: int
    nivel_alcanzado: str
    puntos_acumulados: int
    meses_consecutivos_bajo: int
    otorgada_en: datetime
    incentivo_id: Optional[int] = None

    model_config = {"from_attributes": True}
