from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.api.deps import get_current_auditor
from app.models.auditor import Auditor
from app.models.conductor import Conductor
from app.models.poliza import Poliza
from app.models.indice_riesgo import IndiceRiesgo
from app.services.reportes import generar_reporte_pdf
from app.services.incentivos import calcular_nivel_incentivo

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/conductor/{conductor_id}/pdf")
async def reporte_pdf(
    conductor_id: int,
    auditor: Auditor = Depends(get_current_auditor),
    db: AsyncSession = Depends(get_db),
):
    """HU-010: Genera y devuelve el reporte PDF del perfil de riesgo."""
    res = await db.execute(select(Conductor).where(Conductor.id == conductor_id))
    conductor = res.scalar_one_or_none()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    res_pol = await db.execute(
        select(Poliza).where(Poliza.conductor_id == conductor_id).limit(1)
    )
    poliza = res_pol.scalar_one_or_none()

    res_idx = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor_id)
        .order_by(IndiceRiesgo.calculado_en.desc())
        .limit(1)
    )
    ultimo = res_idx.scalar_one_or_none()

    hace_6m = datetime.now(timezone.utc) - timedelta(days=180)
    res_6m = await db.execute(
        select(func.avg(IndiceRiesgo.indice), func.count(IndiceRiesgo.id), func.sum(IndiceRiesgo.distancia_km))
        .where(IndiceRiesgo.conductor_id == conductor_id, IndiceRiesgo.calculado_en >= hace_6m)
    )
    avg_6m, total_ses, total_km = res_6m.one()

    # Historial para nivel incentivo
    res_todos = await db.execute(
        select(IndiceRiesgo).where(IndiceRiesgo.conductor_id == conductor_id)
        .order_by(IndiceRiesgo.calculado_en.asc())
    )
    todos = res_todos.scalars().all()
    meses: dict[str, list[str]] = {}
    for idx in todos:
        clave = idx.calculado_en.strftime("%Y-%m")
        meses.setdefault(clave, []).append(idx.nivel)
    historial_m = [max(set(v), key=v.count) for v in (meses[k] for k in sorted(meses))]
    nivel_inc = calcular_nivel_incentivo(historial_m)["nivel_incentivo"]

    # Historial de sesiones para el PDF
    historial_pdf = [
        {
            "fecha": idx.calculado_en.strftime("%d/%m/%Y"),
            "indice": idx.indice,
            "nivel": idx.nivel,
            "distancia_km": idx.distancia_km or 0,
        }
        for idx in todos[-10:]
    ]

    datos = {
        "nombre": conductor.nombre,
        "apellido": conductor.apellido,
        "dni": conductor.dni,
        "email": conductor.email,
        "numero_poliza": poliza.numero_poliza if poliza else None,
        "marca_vehiculo": poliza.marca_vehiculo if poliza else None,
        "modelo_vehiculo": poliza.modelo_vehiculo if poliza else None,
        "anio_vehiculo": poliza.anio_vehiculo if poliza else None,
        "indice_actual": ultimo.indice if ultimo else None,
        "nivel_actual": ultimo.nivel if ultimo else None,
        "indice_promedio_6m": round(float(avg_6m), 2) if avg_6m else None,
        "total_sesiones": total_ses or 0,
        "total_km": float(total_km or 0),
        "nivel_incentivo": nivel_inc,
        "historial": historial_pdf,
    }

    pdf_bytes = generar_reporte_pdf(datos)
    filename = f"reporte_riesgo_{conductor.dni}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
