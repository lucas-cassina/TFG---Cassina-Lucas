from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from app.core.database import get_db
from app.api.deps import get_current_conductor
from app.models.conductor import Conductor
from app.models.indice_riesgo import IndiceRiesgo
from app.models.sesion_conduccion import SesionConduccion
from app.models.alerta_conduccion import AlertaConduccion
from app.schemas.indice import IndiceRiesgoOut, EstadisticasMesOut, HistorialSesionOut, SesionDetalleOut, AlertaOut

router = APIRouter(prefix="/indice", tags=["índice de riesgo"])


@router.get("/actual", response_model=Optional[IndiceRiesgoOut])
async def indice_actual(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-004: Índice de riesgo más reciente del conductor."""
    res = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor.id)
        .order_by(IndiceRiesgo.calculado_en.desc())
        .limit(1)
    )
    return res.scalar_one_or_none()


@router.get("/estadisticas-mes", response_model=EstadisticasMesOut)
async def estadisticas_mes(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-005: Estadísticas del mes en curso."""
    now = datetime.now(ZoneInfo("America/Argentina/Cordoba"))
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)

    # Índices del mes
    res = await db.execute(
        select(IndiceRiesgo)
        .where(
            IndiceRiesgo.conductor_id == conductor.id,
            IndiceRiesgo.calculado_en >= inicio_mes,
        )
    )
    indices = res.scalars().all()

    if not indices:
        return EstadisticasMesOut(
            indice_promedio=0.0, nivel_predominante="Sin datos",
            total_sesiones=0, total_km=0.0, alertas_totales=0
        )

    promedio = sum(i.indice for i in indices) / len(indices)
    niveles = [i.nivel for i in indices]
    nivel_predo = max(set(niveles), key=niveles.count)
    total_km = sum(i.distancia_km or 0 for i in indices)

    # Alertas del mes
    res_alertas = await db.execute(
        select(func.count(AlertaConduccion.id)).where(
            AlertaConduccion.conductor_id == conductor.id,
            AlertaConduccion.timestamp >= inicio_mes,
        )
    )
    alertas = res_alertas.scalar() or 0

    return EstadisticasMesOut(
        indice_promedio=round(promedio, 2),
        nivel_predominante=nivel_predo,
        total_sesiones=len(indices),
        total_km=round(total_km, 2),
        alertas_totales=alertas,
    )


@router.get("/historial", response_model=list[HistorialSesionOut])
async def historial_sesiones(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    limite: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """HU-006: Historial de sesiones con filtros de fecha."""
    filters = [SesionConduccion.conductor_id == conductor.id]
    if desde:
        filters.append(SesionConduccion.inicio >= desde)
    if hasta:
        filters.append(SesionConduccion.inicio <= hasta)

    query = (
        select(
            SesionConduccion.id.label("sesion_id"),
            SesionConduccion.inicio,
            SesionConduccion.fin,
            IndiceRiesgo.indice,
            IndiceRiesgo.nivel,
            IndiceRiesgo.distancia_km,
            func.count(AlertaConduccion.id).label("alertas_count"),
        )
        .outerjoin(IndiceRiesgo, IndiceRiesgo.sesion_id == SesionConduccion.id)
        .outerjoin(AlertaConduccion, AlertaConduccion.sesion_id == SesionConduccion.id)
        .where(*filters)
        .group_by(
            SesionConduccion.id,
            SesionConduccion.inicio,
            SesionConduccion.fin,
            IndiceRiesgo.indice,
            IndiceRiesgo.nivel,
            IndiceRiesgo.distancia_km,
        )
        .order_by(SesionConduccion.inicio.desc(), SesionConduccion.id.desc())
        .offset(offset)
        .limit(limite)
    )

    res = await db.execute(query)
    rows = res.mappings().all()
    return [HistorialSesionOut(**r) for r in rows]


@router.get("/historial/{sesion_id}", response_model=SesionDetalleOut)
async def detalle_sesion(
    sesion_id: int,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-006: Detalle completo de una sesión: índice, puntajes y alertas."""
    from fastapi import HTTPException

    res = await db.execute(
        select(
            SesionConduccion.id.label("sesion_id"),
            SesionConduccion.inicio,
            SesionConduccion.fin,
            IndiceRiesgo.indice,
            IndiceRiesgo.nivel,
            IndiceRiesgo.distancia_km,
            IndiceRiesgo.puntaje_velocidad,
            IndiceRiesgo.puntaje_frenadas,
            IndiceRiesgo.puntaje_aceleraciones,
            IndiceRiesgo.puntaje_horario,
            IndiceRiesgo.puntaje_distancia,
        )
        .outerjoin(IndiceRiesgo, IndiceRiesgo.sesion_id == SesionConduccion.id)
        .where(
            SesionConduccion.id == sesion_id,
            SesionConduccion.conductor_id == conductor.id,
        )
    )
    row = res.mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    res_alertas = await db.execute(
        select(AlertaConduccion.tipo_alerta, AlertaConduccion.descripcion, AlertaConduccion.timestamp)
        .where(AlertaConduccion.sesion_id == sesion_id)
        .order_by(AlertaConduccion.timestamp.asc())
    )
    alertas = [AlertaOut(**a) for a in res_alertas.mappings().all()]

    return SesionDetalleOut(**dict(row), alertas=alertas)
