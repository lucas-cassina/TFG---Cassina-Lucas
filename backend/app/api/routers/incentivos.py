from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.database import get_db
from app.api.deps import get_current_conductor
from app.models.conductor import Conductor
from app.models.indice_riesgo import IndiceRiesgo
from app.models.incentivo import Incentivo
from app.services.incentivos import calcular_nivel_incentivo, nivel_para_incentivo

router = APIRouter(prefix="/incentivos", tags=["incentivos"])


@router.get("/mi-nivel")
async def mi_nivel_incentivo(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-008: Nivel de incentivo actual del conductor y puntos."""
    # Obtener historial de índices ordenado cronológicamente (1 por mes)
    res = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor.id)
        .order_by(IndiceRiesgo.calculado_en.asc())
    )
    todos = res.scalars().all()

    # Agrupar por mes: tomar el índice promedio de cada mes
    meses: dict[str, list[str]] = {}
    for idx in todos:
        clave = idx.calculado_en.strftime("%Y-%m")
        meses.setdefault(clave, []).append(idx.nivel)

    historial_meses = []
    for clave in sorted(meses.keys()):
        niveles_mes = meses[clave]
        # Nivel predominante del mes
        nivel_mes = max(set(niveles_mes), key=niveles_mes.count)
        historial_meses.append(nivel_mes)

    resultado = calcular_nivel_incentivo(historial_meses)
    return resultado


@router.get("/disponibles")
async def incentivos_disponibles(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-008: Lista de incentivos disponibles para el nivel del conductor."""
    # Obtener nivel del conductor
    nivel_res = await mi_nivel_incentivo(conductor=conductor, db=db)
    nivel_actual = nivel_res["nivel_incentivo"]

    res = await db.execute(select(Incentivo).where(Incentivo.activo == True))
    todos = res.scalars().all()

    disponibles = [
        {
            "id": inc.id,
            "nombre": inc.nombre,
            "descripcion": inc.descripcion,
            "nivel_requerido": inc.nivel_requerido,
            "accesible": nivel_para_incentivo(nivel_actual, inc.nivel_requerido),
        }
        for inc in todos
    ]
    return {"nivel_actual": nivel_actual, "incentivos": disponibles}
