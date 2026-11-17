import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.event_bus import event_bus
from app.core.sse_tokens import issue_sse_token
from app.api.deps import get_current_conductor, get_conductor_sse
from app.models.conductor import Conductor
from app.models.sesion_conduccion import SesionConduccion
from app.models.evento_telemetrico import EventoTelemetrico
from app.models.alerta_conduccion import AlertaConduccion
from app.models.indice_riesgo import IndiceRiesgo
from app.schemas.telemetria import (
    AperturaSesionRequest, AperturaSesionResponse,
    LoteEventosRequest, CierreSesionRequest, AlertaOut,
)
from app.services.risk_engine import calcular_indice, FRENADA_BRUSCA_MS2, ACEL_BRUSCA_MS2, VEL_MAX_NORMAL

router = APIRouter(prefix="/telemetria", tags=["telemetría"])


@router.post("/sse-token")
async def obtener_sse_token(
    conductor: Conductor = Depends(get_current_conductor),
):
    """
    Emite un token SSE efímero (60 s, single-use) para autenticar la conexión
    al stream sin exponer el JWT en la URL (A1).
    """
    return {"sse_token": issue_sse_token(conductor.id)}


@router.get("/sesion/activa")
async def sesion_activa(
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """Indica si el conductor tiene una sesión activa en este momento."""
    res = await db.execute(
        select(SesionConduccion)
        .where(
            SesionConduccion.conductor_id == conductor.id,
            SesionConduccion.estado == "activa",
        )
        .order_by(SesionConduccion.inicio.desc())
        .limit(1)
    )
    sesion = res.scalar_one_or_none()
    if not sesion:
        return {"activa": False}
    return {"activa": True, "sesion_id": sesion.id, "inicio": sesion.inicio.isoformat()}


@router.get("/stream")
async def stream_eventos(
    conductor: Conductor = Depends(get_conductor_sse),
):
    """SSE: transmite en tiempo real los eventos de sesión del conductor."""
    async def generator():
        q = event_bus.subscribe(conductor.id)
        try:
            yield f"data: {json.dumps({'tipo': 'conectado', 'conductor_id': conductor.id})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'tipo': 'ping'})}\n\n"
        finally:
            event_bus.unsubscribe(conductor.id, q)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/sesion/abrir", response_model=AperturaSesionResponse, status_code=201)
async def abrir_sesion(
    data: AperturaSesionRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: AsyncSession = Depends(get_db),
):
    """HU-003: Apertura de sesión telemétrica."""
    # B3: rechazar si ya hay una sesión activa
    res_activa = await db.execute(
        select(SesionConduccion).where(
            SesionConduccion.conductor_id == conductor.id,
            SesionConduccion.estado == "activa",
        )
    )
    if res_activa.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya tenés una sesión activa")

    sesion = SesionConduccion(
        conductor_id=conductor.id,
        poliza_id=data.poliza_id,
        estado="activa",
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)

    await event_bus.publish(conductor.id, {
        "tipo": "sesion_abierta",
        "sesion_id": sesion.id,
        "inicio": sesion.inicio.isoformat(),
    })

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
    eventos_para_publicar = []

    for ev in data.eventos:
        ts = ev.timestamp or datetime.now(timezone.utc)
        tipo = "normal"

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

        if tipo != "normal":
            descripcion = _descripcion_alerta(tipo, ev)
            alerta = AlertaConduccion(
                sesion_id=sesion.id,
                conductor_id=conductor.id,
                tipo_alerta=tipo,
                descripcion=descripcion,
            )
            db.add(alerta)
            alertas_generadas.append(tipo)
            eventos_para_publicar.append({
                "tipo": "alerta",
                "tipo_alerta": tipo,
                "descripcion": descripcion,
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                "velocidad_kmh": round(ev.velocidad_kmh, 1),
            })

    await db.commit()

    for evento_pub in eventos_para_publicar:
        await event_bus.publish(conductor.id, evento_pub)

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

    await event_bus.publish(conductor.id, {
        "tipo": "sesion_cerrada",
        "sesion_id": sesion.id,
        "indice": resultado["indice"],
        "nivel": resultado["nivel"],
        "distancia_km": resultado["distancia_km"],
    })

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
