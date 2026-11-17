#!/usr/bin/env python3
"""
CIAS — Script de datos de muestra
==================================
Crea 3 conductores y 1 auditor con escenarios sintéticos para probar los umbrales.
Los tiempos y eventos se preparan como fixtures y se recalculan con el motor;
no son viajes observados. Incluye sesiones de conducción simuladas
distribuidas en el tiempo para demostrar todos los casos de uso.

Requisitos:
    pip install httpx asyncpg

Uso (con docker compose up corriendo):
    python seed.py

Usuarios creados:
    maria.garcia@cias.demo  / Demo1234!  → índice Bajo,  nivel Oro
    carlos.lopez@cias.demo  / Demo1234!  → índice Medio, nivel Bronce
    pablo.rodriguez@cias.demo/ Demo1234! → índice Alto,  nivel Sin nivel
    ana.torres@cias.demo    / Demo1234!  → Auditora (legajo AUD-001)
"""

import asyncio
import random
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
from app.services.risk_engine import calcular_indice
from datetime import datetime, timezone, timedelta

import httpx
import asyncpg

API = os.getenv("CIAS_API_URL", "http://localhost:8000")
DB_DSN = os.getenv("CIAS_DB_DSN", os.getenv("DATABASE_URL", "postgresql://cias:cias_password@localhost:5432/cias_db")).replace("postgresql+asyncpg://", "postgresql://")
AUDITOR_CODE = os.getenv("AUDITOR_REGISTRATION_SECRET", "dev_auditor_secret")

# ── Usuarios de muestra ──────────────────────────────────────────────
CONDUCTORES = [
    {
        "nombre": "María",   "apellido": "García",
        "dni": "30111222",   "email": "maria.garcia@cias.demo",
        "password": "Demo1234!", "telefono": "3513001111",
        "perfil": "prudente", "sesiones": 6,
        "meses_atras": [5, 4, 3, 2, 1, 0],   # 1 sesión por mes, 6 meses
    },
    {
        "nombre": "Carlos",  "apellido": "López",
        "dni": "27333444",   "email": "carlos.lopez@cias.demo",
        "password": "Demo1234!", "telefono": "3513002222",
        "perfil": "medio",   "sesiones": 4,
        "meses_atras": [1, 1, 0, 0],
    },
    {
        "nombre": "Pablo",   "apellido": "Rodríguez",
        "dni": "33555666",   "email": "pablo.rodriguez@cias.demo",
        "password": "Demo1234!", "telefono": "3513003333",
        "perfil": "riesgoso", "sesiones": 3,
        "meses_atras": [0, 0, 0],
    },
]

AUDITOR = {
    "nombre": "Ana",  "apellido": "Torres",
    "legajo": "AUD-001", "email": "ana.torres@cias.demo",
    "password": "Demo1234!",
}


# ── Generadores de eventos por perfil ────────────────────────────────
def evento(vel, acel, fren, ts):
    return {
        "velocidad_kmh":  round(max(0, vel  + random.gauss(0, 4)), 1),
        "aceleracion_ms2": round(acel + random.gauss(0, 0.3), 2),
        "frenada_ms2":     round(fren + random.gauss(0, 0.3), 2),
        "latitud":  round(-31.4 + random.uniform(-0.05, 0.05), 6),
        "longitud": round(-64.2 + random.uniform(-0.05, 0.05), 6),
        "timestamp": ts.isoformat(),
    }

def generar_eventos(perfil: str, n=20, base_ts=None):
    base = base_ts or datetime.now(timezone.utc)
    eventos = []
    for i in range(n):
        if perfil == "prudente":
            vel, acel, fren = 60.0, 1.0, -1.0
        elif perfil == "medio":
            vel, acel, fren = 120.0, (4.0 if i < int(n * .95) else 1.0), -6.0
        else:
            vel, acel, fren = 150.0, 5.0, -7.0
        eventos.append({
            "velocidad_kmh": vel, "aceleracion_ms2": acel, "frenada_ms2": fren,
            "latitud": -31.4, "longitud": -64.2,
            "timestamp": (base + timedelta(seconds=i * 3600 / n)).isoformat(),
        })
    return eventos


# ── Helpers HTTP ─────────────────────────────────────────────────────
def post(client, path, data, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = client.post(f"{API}{path}", json=data, headers=headers)
    r.raise_for_status()
    return r.json()

def get(client, path, token):
    r = client.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json()


# ── Crear sesión de conducción ───────────────────────────────────────
def crear_sesion(client, token, perfil, base_ts=None):
    sesion = post(client, "/telemetria/sesion/abrir", {}, token)
    sesion_id = sesion["sesion_id"]
    eventos = generar_eventos(perfil, n=20, base_ts=base_ts)
    post(client, "/telemetria/eventos",
         {"sesion_id": sesion_id, "eventos": eventos}, token)
    resultado = post(client, "/telemetria/sesion/cerrar",
                     {"sesion_id": sesion_id}, token)
    return sesion_id, resultado


# ── Cargar incentivos base ───────────────────────────────────────────
INCENTIVOS_BASE = [
    ("Bronce", "5% de descuento en tu próxima renovación de póliza",            "Bronce", 10),
    ("Plata",  "10% de descuento y asistencia al viajero gratuita",              "Plata",  25),
    ("Oro",    "15% de descuento, asistencia al viajero y bonificación de franquicia", "Oro", 50),
]

async def seed_incentivos():
    conn = await asyncpg.connect(DB_DSN)
    try:
        for nombre, descripcion, nivel, puntos in INCENTIVOS_BASE:
            exists = await conn.fetchval(
                "SELECT id FROM incentivos WHERE nivel_requerido=$1", nivel
            )
            if not exists:
                await conn.execute(
                    "INSERT INTO incentivos (nombre, descripcion, nivel_requerido, puntos_requeridos, activo) "
                    "VALUES ($1, $2, $3, $4, true)",
                    nombre, descripcion, nivel, puntos,
                )
    finally:
        await conn.close()


# ── Actualizar fechas en DB para distribuir meses ────────────────────
async def backdate_sesiones(conductor_id: int, meses_atras: list[int], perfil: str):
    conn = await asyncpg.connect(DB_DSN)
    try:
        rows = await conn.fetch(
            "SELECT id FROM sesiones_conduccion WHERE conductor_id=$1 ORDER BY id", conductor_id)
        now = datetime.now(timezone.utc) - timedelta(hours=3)
        for row, meses in zip(rows, meses_atras):
            mes_num = now.year * 12 + now.month - 1 - meses
            fecha = datetime(mes_num // 12, mes_num % 12 + 1, 1,
                             0 if perfil == "riesgoso" else 10, tzinfo=timezone.utc)
            ids = await conn.fetch(
                "SELECT id FROM eventos_telemetricos WHERE sesion_id=$1 ORDER BY id", row["id"])
            eventos = generar_eventos(perfil, n=len(ids), base_ts=fecha)
            fin = fecha + timedelta(hours=1)
            resultado = calcular_indice(eventos, fecha, fin)
            async with conn.transaction():
                await conn.execute(
                    "UPDATE sesiones_conduccion SET inicio=$1, fin=$2 WHERE id=$3", fecha, fin, row["id"])
                for ev, ev_id in zip(eventos, ids):
                    await conn.execute(
                        "UPDATE eventos_telemetricos SET timestamp=$1, velocidad_kmh=$2, aceleracion_ms2=$3, frenada_ms2=$4 WHERE id=$5",
                        datetime.fromisoformat(ev["timestamp"]), ev["velocidad_kmh"], ev["aceleracion_ms2"], ev["frenada_ms2"], ev_id["id"])
                await conn.execute(
                    "UPDATE indices_riesgo SET calculado_en=$1, indice=$2, nivel=$3, puntaje_velocidad=$4, "
                    "puntaje_frenadas=$5, puntaje_aceleraciones=$6, puntaje_horario=$7, puntaje_distancia=$8, distancia_km=$9 WHERE sesion_id=$10",
                    fin, resultado["indice"], resultado["nivel"], resultado["puntaje_velocidad"],
                    resultado["puntaje_frenadas"], resultado["puntaje_aceleraciones"], resultado["puntaje_horario"],
                    resultado["puntaje_distancia"], resultado["distancia_km"], row["id"])
                await conn.execute("DELETE FROM alertas_conduccion WHERE sesion_id=$1", row["id"])
                for ev in eventos:
                    if abs(ev["frenada_ms2"]) > 5:
                        tipo, descripcion = "frenada_brusca", f"Frenada brusca detectada: {abs(ev['frenada_ms2']):.1f} m/s²"
                    elif ev["aceleracion_ms2"] > 3.5:
                        tipo, descripcion = "aceleracion_brusca", f"Aceleración brusca detectada: {ev['aceleracion_ms2']:.1f} m/s²"
                    elif ev["velocidad_kmh"] > 90:
                        tipo, descripcion = "exceso_velocidad", f"Velocidad excesiva detectada: {ev['velocidad_kmh']:.1f} km/h"
                    else:
                        continue
                    await conn.execute(
                        "INSERT INTO alertas_conduccion (sesion_id, conductor_id, tipo_alerta, descripcion, timestamp) VALUES ($1,$2,$3,$4,$5)",
                        row["id"], conductor_id, tipo, descripcion, datetime.fromisoformat(ev["timestamp"]))
            print(f"     Fixture #{row['id']}: {resultado['indice']} ({resultado['nivel']}), {resultado['distancia_km']} km")
    finally:
        await conn.close()


async def cuenta_sesiones(conductor_id):
    conn = await asyncpg.connect(DB_DSN)
    try:
        return await conn.fetchval("SELECT count(*) FROM sesiones_conduccion WHERE conductor_id=$1", conductor_id)
    finally:
        await conn.close()


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("\n╔══════════════════════════════════════╗")
    print("║   CIAS — Seed de datos de muestra    ║")
    print("╚══════════════════════════════════════╝\n")

    # 0. Incentivos base (idempotente)
    print("→ Cargando incentivos base...")
    asyncio.run(seed_incentivos())
    print("  ✓ Bronce / Plata / Oro listos")

    with httpx.Client(timeout=30) as client:
        # 1. Auditor
        print("→ Creando auditor...")
        try:
            post(client, "/auth/registro/auditor", {**AUDITOR, "codigo_registro": AUDITOR_CODE})
            print(f"  ✓ {AUDITOR['nombre']} {AUDITOR['apellido']} ({AUDITOR['email']})")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                print(f"  · ya existe, saltando")
            else:
                raise

        # 2. Conductores
        for c in CONDUCTORES:
            print(f"\n→ Creando conductor: {c['nombre']} {c['apellido']} (perfil {c['perfil']})...")

            # Registro
            try:
                resp = post(client, "/auth/registro/conductor", {
                    "nombre": c["nombre"], "apellido": c["apellido"],
                    "dni": c["dni"], "email": c["email"],
                    "password": c["password"], "telefono": c["telefono"],
                })
                conductor_id = resp["user_id"]
                token = resp["access_token"]
                print(f"  ✓ Registrado (ID {conductor_id})")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    print(f"  · ya existe, iniciando sesión...")
                    resp = post(client, "/auth/login",
                                {"email": c["email"], "password": c["password"]})
                    conductor_id = resp["user_id"]
                    token = resp["access_token"]
                else:
                    raise

            # Sesiones
            print(f"  → Generando {c['sesiones']} sesiones...")
            faltan = max(0, c["sesiones"] - asyncio.run(cuenta_sesiones(conductor_id)))
            for i in range(faltan):
                sid, res = crear_sesion(client, token, c["perfil"])
                print(f"     Sesión {i+1}: recibida por API")

            print("  → Preparando períodos y recalculando escenarios sintéticos...")
            asyncio.run(backdate_sesiones(conductor_id, c["meses_atras"], c["perfil"]))

            # Verificar nivel final
            nivel = get(client, "/incentivos/mi-nivel", token)
            print(f"  ✓ Nivel incentivo: {nivel['nivel_incentivo']} "
                  f"({nivel['meses_consecutivos_bajo']} meses Bajo, "
                  f"{nivel['puntos_acumulados']} pts)")

    # Resumen
    print("\n" + "="*45)
    print("  USUARIOS CREADOS — CIAS Demo")
    print("="*45)
    print("\n  CONDUCTORES\n")
    for c in CONDUCTORES:
        print(f"  {c['nombre']} {c['apellido']}")
        print(f"    Email:    {c['email']}")
        print(f"    Password: {c['password']}")
        print(f"    DNI:      {c['dni']}")
        print(f"    Perfil:   {c['perfil']}\n")
    print("  AUDITOR\n")
    print(f"  {AUDITOR['nombre']} {AUDITOR['apellido']}")
    print(f"    Email:    {AUDITOR['email']}")
    print(f"    Password: {AUDITOR['password']}")
    print(f"    Legajo:   {AUDITOR['legajo']}\n")
    print("="*45)
    print("\n✓ Seed completado. Podés iniciar sesión en http://localhost:3000\n")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("\n✗ No se pudo conectar al backend en http://localhost:8000")
        print("  Asegurate de tener el stack corriendo: docker compose up\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
