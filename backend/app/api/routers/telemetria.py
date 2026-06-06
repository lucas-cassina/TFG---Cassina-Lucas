from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.database import get_db
from app.api.deps import get_current_conductor
from app.models.conductor import Conductor
from app.models.sesion_conduccion import SesionConduccion
from app.models.evento_telemetrico import EventoTelemetrico
from app.models.alerta_conduccion import AlertaConduccion
from app.models.indice_riesgo import IndiceRiesgo
from app.schemas.telemetria import (
    AperturaSesionRequest, AperturaSesionResponse,
    LoteEventosRequest, CierreSesionRequest, AlertaOut
)
from app.services.risk_engine import calcular_indice, FRENADA_BRUSCA_MS2, ACEL_BRUSCA_MS2, VEL_MAX_NORMAL

router = APIRouter(prefix="/telemetria", tags=["telemetría"])


@router.post("/sesion/abrir", response_model=AperturaSesionResponse, status_code=201)
async def abrir_sesion(
    data: AperturaSesionRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-003: Apertura de sesión telemétrica."""
    sesion = SesionConduccion(
        conductor_id=conductor.id,
        poliza_id=data.poliza_id,
        estado="activa",
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)
    return AperturaSesionResponse(
        sesion_id=sesion.id, inicio=sesion.inicio, estado=sesion.estado
    )


@router.post("/eventos", status_code=201)
async def recibir_eventos(
    data: LoteEventosRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-003: Recepción de lote de eventos OBD-II. Genera alertas automáticas."""
    res = await db.execute(
        select(SesionConduccion).where(
            SesionConduccion.id == data.sesion_id,
            SesionConduccion.conductor_id == conductor.id,
            SesionConduccion.estado == "activa",
        )
    )
    sesion = res.scalar_one_or_none()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o no activa")

    alertas_generadas = []
    for ev in data.eventos:
        ts = ev.timestamp or datetime.now(timezone.utc)
        tipo = "normal"

        # Detectar tipo de evento para alertas
        if abs(ev.frenada_ms2) > FRENADA_BRUSCA_MS2:
            tipo = "frenada_brusca"
        elif ev.aceleracion_ms2 > ACEL_BRUSCA_MS2:
            tipo = "aceleracion_brusca"
        elif ev.velocidad_kmh > VEL_MAX_NORMAL:
            tipo = "exceso_velocidad"

        evento = EventoTelemetrico(
            sesion_id=sesion.id,
            timestamp=ts,
            velocidad_kmh=ev.velocidad_kmh,
            aceleracion_ms2=ev.aceleracion_ms2,
            frenada_ms2=ev.frenada_ms2,
            latitud=ev.latitud,
            longitud=ev.longitud,
            tipo_evento=tipo,
        )
        db.add(evento)

        # HU-007: generar alerta si el evento es de riesgo
        if tipo != "normal":
            alerta = AlertaConduccion(
                sesion_id=sesion.id,
                conductor_id=conductor.id,
                tipo_alerta=tipo,
                descripcion=_descripcion_alerta(tipo, ev),
            )
            db.add(alerta)
            alertas_generadas.append(tipo)

    await db.commit()
    return {"eventos_procesados": len(data.eventos), "alertas_generadas": len(alertas_generadas)}


@router.post("/sesion/cerrar")
async def cerrar_sesion(
    data: CierreSesionRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-003: Cierre de sesión + cálculo automático del índice de riesgo."""
    res = await db.execute(
        select(SesionConduccion).where(
            SesionConduccion.id == data.sesion_id,
            SesionConduccion.conductor_id == conductor.id,
            SesionConduccion.estado == "activa",
        )
    )
    sesion = res.scalar_one_or_none()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o no activa")

    fin = datetime.now(timezone.utc)
    sesion.fin = fin
    sesion.estado = "cerrada"

    # Obtener eventos de la sesión
    ev_res = await db.execute(
        select(EventoTelemetrico).where(EventoTelemetrico.sesion_id == sesion.id)
    )
    eventos_orm = ev_res.scalars().all()
    eventos_dict = [
        {
            "velocidad_kmh": e.velocidad_kmh,
            "aceleracion_ms2": e.aceleracion_ms2,
            "frenada_ms2": e.frenada_ms2,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in eventos_orm
    ]

    # Calcular índice
    resultado = calcular_indice(eventos_dict, sesion.inicio, fin)

    indice_orm = IndiceRiesgo(
        sesion_id=sesion.id,
        conductor_id=conductor.id,
        **resultado,
    )
    db.add(indice_orm)
    sesion.estado = "procesada"
    await db.commit()
    await db.refresh(indice_orm)

    return {
        "sesion_id": sesion.id,
        "indice": resultado["indice"],
        "nivel": resultado["nivel"],
        "distancia_km": resultado["distancia_km"],
    }


@router.get("/alertas", response_model=list[AlertaOut])
async def listar_alertas(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-007: Alertas de conducción del conductor."""
    res = await db.execute(
        select(AlertaConduccion)
        .where(AlertaConduccion.conductor_id == conductor.id)
        .order_by(AlertaConduccion.timestamp.desc())
        .limit(50)
    )
    return res.scalars().all()


def _descripcion_alerta(tipo: str, evento) -> str:
    if tipo == "exceso_velocidad":
        return f"Velocidad excesiva detectada: {evento.velocidad_kmh:.1f} km/h"
    elif tipo == "frenada_brusca":
        return f"Frenada brusca detectada: {abs(evento.frenada_ms2):.1f} m/s²"
    elif tipo == "aceleracion_brusca":
        return f"Aceleración brusca detectada: {evento.aceleracion_ms2:.1f} m/s²"
    return tipo
