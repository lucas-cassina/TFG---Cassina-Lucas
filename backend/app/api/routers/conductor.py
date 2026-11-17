from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_conductor
from app.core.database import get_db
from app.models.conductor import Conductor
from app.models.poliza import Poliza
from app.models.indice_riesgo import IndiceRiesgo
from app.schemas.conductor import PerfilConductorOut, CambioContrasenaRequest, PolizaIn, PolizaOut
from app.services.reportes import generar_poliza_pdf, generar_reporte_pdf
from app.services.incentivos import calcular_nivel_incentivo, historial_nivel_por_mes
from app.core.security import hash_password, verify_password
from app.services.passwords import guardar_contrasena, es_contrasena_reutilizada

router = APIRouter(prefix="/conductor", tags=["conductor"])


@router.get("/perfil", response_model=PerfilConductorOut)
async def mi_perfil(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """Datos propios del conductor y su póliza vigente más reciente."""
    res = await db.execute(
        select(Poliza)
        .where(Poliza.conductor_id == conductor.id)
        .order_by(Poliza.fecha_vencimiento.desc())
        .limit(1)
    )
    return PerfilConductorOut(conductor=conductor, poliza=res.scalar_one_or_none())


@router.get("/poliza/pdf")
async def descargar_poliza_pdf(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """Genera y descarga el PDF de la póliza vigente del conductor."""
    res = await db.execute(
        select(Poliza)
        .where(Poliza.conductor_id == conductor.id)
        .order_by(Poliza.fecha_vencimiento.desc())
        .limit(1)
    )
    poliza = res.scalar_one_or_none()
    if not poliza:
        raise HTTPException(status_code=404, detail="No tenés una póliza registrada")

    datos = {
        "nombre": conductor.nombre,
        "apellido": conductor.apellido,
        "dni": conductor.dni,
        "email": conductor.email,
        "telefono": conductor.telefono,
        "fecha_nacimiento": conductor.fecha_nacimiento,
        "numero_poliza": poliza.numero_poliza,
        "marca_vehiculo": poliza.marca_vehiculo,
        "modelo_vehiculo": poliza.modelo_vehiculo,
        "anio_vehiculo": poliza.anio_vehiculo,
        "patente": poliza.patente,
        "zona": poliza.zona,
        "fecha_inicio": poliza.fecha_inicio,
        "fecha_vencimiento": poliza.fecha_vencimiento,
    }

    pdf_bytes = generar_poliza_pdf(datos)
    filename = f"poliza_{poliza.numero_poliza}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/estadisticas/pdf")
async def descargar_estadisticas_pdf(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """Genera y descarga el PDF de estadísticas de conducción del conductor autenticado."""
    res_pol = await db.execute(
        select(Poliza)
        .where(Poliza.conductor_id == conductor.id)
        .order_by(Poliza.fecha_vencimiento.desc())
        .limit(1)
    )
    poliza = res_pol.scalar_one_or_none()

    res_idx = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor.id)
        .order_by(IndiceRiesgo.calculado_en.desc())
        .limit(1)
    )
    ultimo = res_idx.scalar_one_or_none()

    hace_6m = datetime.now(timezone.utc) - timedelta(days=180)
    res_6m = await db.execute(
        select(func.avg(IndiceRiesgo.indice), func.count(IndiceRiesgo.id), func.sum(IndiceRiesgo.distancia_km))
        .where(IndiceRiesgo.conductor_id == conductor.id, IndiceRiesgo.calculado_en >= hace_6m)
    )
    avg_6m, total_ses, total_km = res_6m.one()

    res_todos = await db.execute(
        select(IndiceRiesgo)
        .where(IndiceRiesgo.conductor_id == conductor.id)
        .order_by(IndiceRiesgo.calculado_en.asc())
    )
    todos = res_todos.scalars().all()

    historial_m = historial_nivel_por_mes(todos)
    nivel_inc = calcular_nivel_incentivo(historial_m)["nivel_incentivo"]

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
    filename = f"estadisticas_{conductor.dni}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/poliza", response_model=PolizaOut, status_code=201)
async def cargar_poliza(
    data: PolizaIn,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """Crea o reemplaza la póliza del conductor autenticado."""
    res = await db.execute(
        select(Poliza).where(Poliza.conductor_id == conductor.id).limit(1)
    )
    poliza = res.scalar_one_or_none()
    if poliza:
        for field, value in data.model_dump().items():
            setattr(poliza, field, value)
        await db.commit()
    else:
        poliza = Poliza(conductor_id=conductor.id, **data.model_dump())
        db.add(poliza)
        try:
            await db.commit()
        except IntegrityError:
            # Otra request concurrent ganó la carrera; leer y actualizar
            await db.rollback()
            res = await db.execute(
                select(Poliza).where(Poliza.conductor_id == conductor.id).limit(1)
            )
            poliza = res.scalar_one()
            for field, value in data.model_dump().items():
                setattr(poliza, field, value)
            await db.commit()
    await db.refresh(poliza)
    return poliza


@router.put("/cambiar-contrasena", status_code=204)
async def cambiar_contrasena(
    data: CambioContrasenaRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """
    HU-002 (seguridad): Cambio de contraseña con verificación de la actual
    y validación de no-reutilización de las últimas 3 (tesis pág. 43).
    """
    # 1. Verificar contraseña actual
    if not verify_password(data.contrasena_actual, conductor.hashed_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    # 2. Verificar que la nueva contraseña no se haya usado antes (últimas 3)
    if await es_contrasena_reutilizada(conductor.id, "conductor", data.contrasena_nueva, db):
        raise HTTPException(
            status_code=400,
            detail="No podés reutilizar ninguna de tus últimas 3 contraseñas",
        )

    # 3. Actualizar hash y guardar en historial
    conductor.hashed_password = hash_password(data.contrasena_nueva)
    await guardar_contrasena(conductor.id, "conductor", conductor.hashed_password, db)
    await db.commit()
    return None
