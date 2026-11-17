from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_conductor
from app.models.conductor import Conductor
from app.models.indice_riesgo import IndiceRiesgo
from app.models.incentivo import Incentivo
from app.models.recompensa import Recompensa
from app.schemas.incentivo import RecompensaOut
from app.services.incentivos import calcular_nivel_incentivo, nivel_para_incentivo, historial_nivel_por_mes

router = APIRouter(prefix="/incentivos", tags=["incentivos"])


@router.get("/mi-nivel")
async def mi_nivel_incentivo(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-008: Nivel de incentivo actual del conductor y puntos."""
    res = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor.id)
        .order_by(IndiceRiesgo.calculado_en.asc())
    )
    todos = res.scalars().all()
    resultado = calcular_nivel_incentivo(historial_nivel_por_mes(todos))
    nivel_alcanzado = resultado["nivel_incentivo"]

    # Auto-otorgar Recompensa si el conductor alcanzó un nivel nuevo (HU-008)
    if nivel_alcanzado != "Sin nivel":
        ya_existe = await db.execute(
            select(Recompensa).where(
                Recompensa.conductor_id == conductor.id,
                Recompensa.nivel_alcanzado == nivel_alcanzado,
            )
        )
        if not ya_existe.scalars().first():
            # Buscar el Incentivo correspondiente al nivel
            res_inc = await db.execute(
                select(Incentivo).where(
                    Incentivo.nivel_requerido == nivel_alcanzado,
                    Incentivo.activo == True,
                ).limit(1)
            )
            incentivo = res_inc.scalar_one_or_none()
            nueva_recompensa = Recompensa(
                conductor_id=conductor.id,
                incentivo_id=incentivo.id if incentivo else None,
                nivel_alcanzado=nivel_alcanzado,
                puntos_acumulados=resultado["puntos_acumulados"],
                meses_consecutivos_bajo=resultado["meses_consecutivos_bajo"],
            )
            db.add(nueva_recompensa)
            await db.commit()

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


@router.get("/mis-recompensas", response_model=List[RecompensaOut])
async def mis_recompensas(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-008: Lista de recompensas (niveles) obtenidos por el conductor."""
    res = await db.execute(
        select(Recompensa)
        .where(Recompensa.conductor_id == conductor.id)
        .order_by(Recompensa.otorgada_en.desc())
    )
    return res.scalars().all()
