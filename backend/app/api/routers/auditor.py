from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.api.deps import get_current_auditor
from app.models.auditor import Auditor
from app.models.conductor import Conductor
from app.models.poliza import Poliza
from app.models.indice_riesgo import IndiceRiesgo
from app.models.sesion_conduccion import SesionConduccion
from app.schemas.auditor import BusquedaAseguradoRequest, PerfilRiesgoAuditorOut
from app.services.incentivos import calcular_nivel_incentivo

router = APIRouter(prefix="/auditor", tags=["auditor"])


@router.post("/buscar-asegurado")
async def buscar_asegurado(
    data: BusquedaAseguradoRequest,
    auditor: Auditor = Depends(get_current_auditor),
    db: AsyncSession = Depends(get_db),
):
    """HU-009: Búsqueda de asegurado por DNI o número de póliza."""
    if not data.dni and not data.numero_poliza:
        raise HTTPException(status_code=400, detail="Proporcionar DNI o número de póliza")

    if data.dni:
        res = await db.execute(select(Conductor).where(Conductor.dni == data.dni))
        conductor = res.scalar_one_or_none()
    else:
        res = await db.execute(select(Poliza).where(Poliza.numero_poliza == data.numero_poliza))
        poliza = res.scalar_one_or_none()
        if not poliza:
            raise HTTPException(status_code=404, detail="Póliza no encontrada")
        res2 = await db.execute(select(Conductor).where(Conductor.id == poliza.conductor_id))
        conductor = res2.scalar_one_or_none()

    if not conductor:
        raise HTTPException(status_code=404, detail="Asegurado no encontrado")

    return {"conductor_id": conductor.id, "nombre": conductor.nombre,
            "apellido": conductor.apellido, "dni": conductor.dni, "email": conductor.email}


@router.get("/perfil-riesgo/{conductor_id}", response_model=PerfilRiesgoAuditorOut)
async def perfil_riesgo(
    conductor_id: int,
    auditor: Auditor = Depends(get_current_auditor),
    db: AsyncSession = Depends(get_db),
):
    """HU-009: Perfil de riesgo completo de un asegurado para el auditor."""
    res = await db.execute(select(Conductor).where(Conductor.id == conductor_id))
    conductor = res.scalar_one_or_none()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    # Última póliza
    res_pol = await db.execute(
        select(Poliza).where(Poliza.conductor_id == conductor_id).limit(1)
    )
    poliza = res_pol.scalar_one_or_none()

    # Índice actual
    res_idx = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor_id)
        .order_by(IndiceRiesgo.calculado_en.desc())
        .limit(1)
    )
    ultimo_idx = res_idx.scalar_one_or_none()

    # Promedio 6 meses
    from datetime import datetime, timezone, timedelta
    hace_6m = datetime.now(timezone.utc) - timedelta(days=180)
    res_6m = await db.execute(
        select(func.avg(IndiceRiesgo.indice), func.count(IndiceRiesgo.id), func.sum(IndiceRiesgo.distancia_km))
        .where(IndiceRiesgo.conductor_id == conductor_id, IndiceRiesgo.calculado_en >= hace_6m)
    )
    avg_6m, total_ses, total_km = res_6m.one()

    # Nivel incentivo
    res_todos = await db.execute(
        select(IndiceRiesgo).where(IndiceRiesgo.conductor_id == conductor_id)
        .order_by(IndiceRiesgo.calculado_en.asc())
    )
    todos_idx = res_todos.scalars().all()
    meses: dict[str, list[str]] = {}
    for idx in todos_idx:
        clave = idx.calculado_en.strftime("%Y-%m")
        meses.setdefault(clave, []).append(idx.nivel)
    historial_m = [max(set(v), key=v.count) for v in (meses[k] for k in sorted(meses))]
    nivel_inc = calcular_nivel_incentivo(historial_m)["nivel_incentivo"]

    return PerfilRiesgoAuditorOut(
        conductor_id=conductor.id,
        nombre=conductor.nombre,
        apellido=conductor.apellido,
        dni=conductor.dni,
        email=conductor.email,
        numero_poliza=poliza.numero_poliza if poliza else None,
        marca_vehiculo=poliza.marca_vehiculo if poliza else None,
        modelo_vehiculo=poliza.modelo_vehiculo if poliza else None,
        indice_actual=ultimo_idx.indice if ultimo_idx else None,
        nivel_actual=ultimo_idx.nivel if ultimo_idx else None,
        indice_promedio_6m=round(float(avg_6m), 2) if avg_6m else None,
        total_sesiones=total_ses or 0,
        total_km=float(total_km or 0),
        nivel_incentivo=nivel_inc,
    )
