#!/usr/bin/env python3
"""
CIAS — Simulador OBD-II
========================
Replica el comportamiento exacto de un dongle OBD-II conectado al vehículo:

  1. El conductor se autentica en la app (ya lo hizo; el dispositivo usa su token).
  2. Al detectar encendido del motor → abre sesión telemétrica.
  3. Cada BATCH_INTERVAL segundos → envía lote de eventos al backend.
  4. Al detectar apagado (Ctrl+C o duración cumplida) → cierra sesión y muestra índice.

Los eventos siguen un modelo físico realista:
  - Velocidad con transiciones suaves (no saltos bruscos)
  - Aceleración/frenada calculadas a partir del delta de velocidad
  - GPS que avanza a lo largo de un segmento urbano de Córdoba, Argentina

Uso:
    python obd_sim.py                                       # perfil medio, usuario seed
    python obd_sim.py --perfil prudente
    python obd_sim.py --perfil riesgoso
    python obd_sim.py --email tu@email.com --password Pass1!
    python obd_sim.py --duracion 3                         # 3 minutos de conducción
    python obd_sim.py --api http://localhost:8000

Perfiles disponibles:
    prudente  → índice Bajo   (velocidad ≤ 90 km/h, frenadas suaves)
    medio     → índice Medio  (velocidad hasta 125 km/h, algún evento brusco)
    riesgoso  → índice Alto   (velocidad hasta 155 km/h, frenadas y aceleraciones bruscas)

Requisitos:
    pip install httpx
"""

import argparse
import math
import random
import signal
import sys
import time
from datetime import datetime, timezone, timedelta

import httpx

# ── Configuración por defecto ─────────────────────────────────────────────────

API_DEFAULT = "http://localhost:8000"

CREDENCIALES_DEFAULT = {
    "prudente": {"email": "maria.garcia@cias.demo",     "password": "Demo1234!"},
    "medio":    {"email": "carlos.lopez@cias.demo",     "password": "Demo1234!"},
    "riesgoso": {"email": "pablo.rodriguez@cias.demo",  "password": "Demo1234!"},
}

# Frecuencia de muestreo OBD-II real: ~1 Hz (1 evento por segundo)
# Lote enviado al servidor cada BATCH_INTERVAL segundos
SAMPLE_HZ = 1
BATCH_INTERVAL = 5   # segundos entre envíos HTTP (= 5 eventos por lote)

# Umbrales físicos (deben coincidir con risk_engine.py)
VEL_MAX_NORMAL   = 90.0    # km/h
FRENADA_BRUSCA   = 5.0     # m/s²
ACEL_BRUSCA      = 3.5     # m/s²

# Ruta GPS de ejemplo: Av. Colón → Av. Rafael Núñez, Córdoba
RUTA = [
    (-31.4167, -64.1833),  # inicio
    (-31.4100, -64.1900),
    (-31.4050, -64.1950),
    (-31.4000, -64.2000),
    (-31.3950, -64.2050),
    (-31.3900, -64.2100),  # fin
]


# ── Modelo de conducción por perfil ──────────────────────────────────────────

PERFILES = {
    "prudente": {
        "vel_crucero":  (50, 85),    # rango de velocidad de crucero (km/h)
        "vel_max":       95,          # velocidad máxima alcanzable
        "acel_normal":   (0.5, 1.8),  # m/s² en aceleración normal
        "fren_normal":  (-1.8, -0.5), # m/s² en frenada normal
        "prob_evento":   0.03,        # probabilidad de evento brusco por tick
        "acel_brusca":   (2.0, 3.2),
        "fren_brusca":  (-4.5, -3.0),
        "vel_brusca":    None,        # no genera exceso de velocidad
    },
    "medio": {
        "vel_crucero":  (70, 115),
        "vel_max":      130,
        "acel_normal":  (0.8, 2.5),
        "fren_normal":  (-2.5, -0.8),
        "prob_evento":   0.08,
        "acel_brusca":   (2.8, 4.5),
        "fren_brusca":  (-5.5, -3.5),
        "vel_brusca":   (100, 130),
    },
    "riesgoso": {
        "vel_crucero":  (90, 140),
        "vel_max":      160,
        "acel_normal":  (1.5, 3.2),
        "fren_normal":  (-4.0, -1.5),
        "prob_evento":   0.20,
        "acel_brusca":   (3.8, 6.0),
        "fren_brusca":  (-7.5, -5.0),
        "vel_brusca":   (125, 155),
    },
}


class SimuladorOBD:
    """Máquina de estados que modela la conducción y genera eventos telemétricos."""

    def __init__(self, perfil: str, duracion_min: int):
        self.cfg = PERFILES[perfil]
        self.duracion_s = duracion_min * 60

        # Estado físico del vehículo
        self.velocidad = 0.0        # km/h
        self.vel_objetivo = 0.0     # km/h
        self.aceleracion = 0.0      # m/s²
        self.frenada = 0.0          # m/s²
        self.tick = 0               # segundos transcurridos
        self.fase = "arrancando"    # arrancando | circulando | desacelerando | parado

        # GPS: interpolamos a lo largo de la ruta
        self._ruta_idx = 0
        self.lat, self.lon = RUTA[0]

        # Estadísticas locales para mostrar en terminal
        self.alertas_locales: list[str] = []
        self.max_vel = 0.0
        self.total_eventos = 0

    def _nuevo_objetivo(self) -> float:
        lo, hi = self.cfg["vel_crucero"]
        return random.uniform(lo, hi)

    def _avanzar_gps(self):
        """Interpolación lineal a lo largo de los waypoints de la ruta."""
        if self._ruta_idx >= len(RUTA) - 1:
            return
        p1 = RUTA[self._ruta_idx]
        p2 = RUTA[self._ruta_idx + 1]
        fraccion = (self.tick % 60) / 60.0
        self.lat = p1[0] + (p2[0] - p1[0]) * fraccion
        self.lon = p1[1] + (p2[1] - p1[1]) * fraccion
        if fraccion > 0.95:
            self._ruta_idx = min(self._ruta_idx + 1, len(RUTA) - 1)

    def tick_evento(self) -> dict:
        """Genera el evento del siguiente segundo de conducción."""
        self.tick += 1
        progreso = self.tick / self.duracion_s

        # Fases del viaje
        if progreso < 0.08:
            self.fase = "arrancando"
            self.vel_objetivo = self._nuevo_objetivo() * progreso / 0.08
        elif progreso > 0.85:
            self.fase = "desacelerando"
            self.vel_objetivo *= 0.92
        else:
            self.fase = "circulando"
            # Cambiar objetivo de velocidad esporádicamente (simula semáforos, curvas)
            if random.random() < 0.04:
                self.vel_objetivo = self._nuevo_objetivo()

        # Evento brusco esporádico
        acel = 0.0
        fren = 0.0
        if self.fase == "circulando" and random.random() < self.cfg["prob_evento"]:
            tipo_evento = random.choice(["frenada", "aceleracion", "velocidad"])
            if tipo_evento == "frenada":
                lo, hi = self.cfg["fren_brusca"]
                fren = random.uniform(lo, hi)
                self.vel_objetivo = max(0, self.velocidad - random.uniform(20, 40))
                self.alertas_locales.append("frenada_brusca")
            elif tipo_evento == "aceleracion":
                lo, hi = self.cfg["acel_brusca"]
                acel = random.uniform(lo, hi)
                self.alertas_locales.append("aceleracion_brusca")
            elif tipo_evento == "velocidad" and self.cfg["vel_brusca"]:
                lo, hi = self.cfg["vel_brusca"]
                self.vel_objetivo = random.uniform(lo, hi)
                self.alertas_locales.append("exceso_velocidad")
        else:
            # Transición suave hacia objetivo
            diff = self.vel_objetivo - self.velocidad
            if diff > 0:
                lo, hi = self.cfg["acel_normal"]
                acel = random.uniform(lo, hi) + random.gauss(0, 0.2)
            elif diff < -2:
                lo, hi = self.cfg["fren_normal"]
                fren = random.uniform(lo, hi) + random.gauss(0, 0.2)

        # Actualizar velocidad (dt = 1s; convertimos m/s² a km/h)
        delta_vel = (acel + abs(fren if fren < 0 else 0)) * (1 if acel > 0 else -1) * 3.6
        self.velocidad = max(0.0, min(self.cfg["vel_max"],
                                       self.velocidad + delta_vel + random.gauss(0, 0.8)))

        if self.velocidad > self.max_vel:
            self.max_vel = self.velocidad

        self._avanzar_gps()
        self.total_eventos += 1

        return {
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "velocidad_kmh":  round(self.velocidad, 1),
            "aceleracion_ms2": round(acel + random.gauss(0, 0.15), 2),
            "frenada_ms2":    round(fren + random.gauss(0, 0.15), 2),
            "latitud":        round(self.lat + random.gauss(0, 0.00005), 6),
            "longitud":       round(self.lon + random.gauss(0, 0.00005), 6),
        }


# ── Utilidades de terminal ────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"
CLEAR_LINE = "\033[2K\033[1G"


def barra_progreso(progreso: float, ancho: int = 30) -> str:
    lleno = int(progreso * ancho)
    return f"[{'█' * lleno}{'░' * (ancho - lleno)}] {progreso * 100:.0f}%"


def color_velocidad(vel: float) -> str:
    if vel > VEL_MAX_NORMAL:
        return RED
    elif vel > 100:
        return YELLOW
    return GREEN


def color_indice(indice: float) -> str:
    if indice > 85:
        return RED
    elif indice > 70:
        return YELLOW
    return GREEN


def print_estado(sim: SimuladorOBD, batch_num: int, ultimo_lote_ms: float):
    vel = sim.velocidad
    col = color_velocidad(vel)
    barra = barra_progreso(sim.tick / sim.duracion_s)

    alertas_str = ""
    if sim.alertas_locales:
        ultima = sim.alertas_locales[-1].replace("_", " ").upper()
        alertas_str = f"  {RED}⚠ {ultima}{RESET}"

    print(
        f"{CLEAR_LINE}"
        f"{CYAN}OBD-II{RESET} "
        f"{col}{vel:6.1f} km/h{RESET}  "
        f"{DIM}lote #{batch_num:02d}  {ultimo_lote_ms:.0f}ms{RESET}  "
        f"{barra}"
        f"{alertas_str}",
        end="",
        flush=True,
    )


# ── Lógica principal ──────────────────────────────────────────────────────────

def login(client: httpx.Client, api: str, email: str, password: str) -> str:
    r = client.post(f"{api}/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    data = r.json()
    return data["access_token"], data["nombre"], data["apellido"]


def abrir_sesion(client: httpx.Client, api: str, token: str) -> int:
    r = client.post(
        f"{api}/telemetria/sesion/abrir",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return r.json()["sesion_id"]


def enviar_lote(client: httpx.Client, api: str, token: str, sesion_id: int, eventos: list) -> dict:
    r = client.post(
        f"{api}/telemetria/eventos",
        json={"sesion_id": sesion_id, "eventos": eventos},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def cerrar_sesion(client: httpx.Client, api: str, token: str, sesion_id: int) -> dict:
    r = client.post(
        f"{api}/telemetria/sesion/cerrar",
        json={"sesion_id": sesion_id},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def run(api: str, email: str, password: str, perfil: str, duracion_min: int):
    print(f"\n{BOLD}{'─'*55}{RESET}")
    print(f"{BOLD}  CIAS — Simulador OBD-II{RESET}")
    print(f"{'─'*55}")
    print(f"  Backend : {api}")
    print(f"  Perfil  : {BOLD}{perfil}{RESET}")
    print(f"  Duración: {duracion_min} min")
    print(f"{'─'*55}\n")

    sim = SimuladorOBD(perfil, duracion_min)
    token = None
    sesion_id = None
    lote_buffer: list[dict] = []
    batch_num = 0
    ultimo_lote_ms = 0.0
    interrumpido = False

    with httpx.Client(timeout=20) as client:

        # ── 1. Autenticación ──────────────────────────────────────────
        print(f"  {DIM}[1/3] Autenticando conductor...{RESET}", end=" ", flush=True)
        try:
            token, nombre, apellido = login(client, api, email, password)
        except httpx.HTTPStatusError as e:
            print(f"\n  {RED}✗ Login fallido ({e.response.status_code}): {e.response.text}{RESET}\n")
            sys.exit(1)
        except httpx.ConnectError:
            print(f"\n  {RED}✗ No se pudo conectar a {api}{RESET}")
            print(f"  {DIM}Verificá que el backend esté corriendo: docker compose up{RESET}\n")
            sys.exit(1)
        print(f"{GREEN}✓{RESET} {nombre} {apellido}")

        # ── 2. Apertura de sesión (motor encendido) ───────────────────
        print(f"  {DIM}[2/3] Encendiendo motor — abriendo sesión...{RESET}", end=" ", flush=True)
        sesion_id = abrir_sesion(client, api, token)
        print(f"{GREEN}✓{RESET} sesión #{sesion_id}")

        print(f"\n  {DIM}[3/3] Transmitiendo telemetría OBD-II...{RESET}")
        print(f"  {DIM}Presioná Ctrl+C para apagar el motor y cerrar la sesión.{RESET}\n")
        time.sleep(1)

        # ── 3. Loop de telemetría ─────────────────────────────────────
        def apagar_motor(sig, frame):
            nonlocal interrumpido
            interrumpido = True

        signal.signal(signal.SIGINT, apagar_motor)

        t_inicio = time.monotonic()

        try:
            while sim.tick < sim.duracion_s and not interrumpido:
                ev = sim.tick_evento()
                lote_buffer.append(ev)

                # Enviar lote acumulado cada BATCH_INTERVAL segundos
                if len(lote_buffer) >= BATCH_INTERVAL:
                    t0 = time.monotonic()
                    try:
                        enviar_lote(client, api, token, sesion_id, lote_buffer)
                    except httpx.HTTPStatusError as e:
                        print(f"\n  {RED}✗ Error enviando lote: {e.response.text}{RESET}")
                    finally:
                        ultimo_lote_ms = (time.monotonic() - t0) * 1000
                        batch_num += 1
                        lote_buffer.clear()

                print_estado(sim, batch_num, ultimo_lote_ms)
                time.sleep(1.0 / SAMPLE_HZ)

        except Exception as e:
            print(f"\n  {RED}✗ Error inesperado: {e}{RESET}")

        # Enviar eventos residuales en el buffer
        if lote_buffer:
            try:
                enviar_lote(client, api, token, sesion_id, lote_buffer)
                batch_num += 1
            except Exception:
                pass

        # ── 4. Cierre de sesión (motor apagado) ───────────────────────
        print(f"\n\n  {DIM}Motor apagado. Cerrando sesión y calculando índice...{RESET}", end=" ", flush=True)
        try:
            resultado = cerrar_sesion(client, api, token, sesion_id)
        except httpx.HTTPStatusError as e:
            print(f"\n  {RED}✗ Error cerrando sesión: {e.response.text}{RESET}\n")
            sys.exit(1)

        print(f"{GREEN}✓{RESET}\n")

    # ── 5. Resumen ────────────────────────────────────────────────────
    duracion_real = time.monotonic() - t_inicio
    indice  = resultado["indice"]
    nivel   = resultado["nivel"]
    dist_km = resultado.get("distancia_km", 0)
    col_idx = color_indice(indice)

    print(f"{'─'*55}")
    print(f"  {BOLD}RESUMEN DE SESIÓN #{sesion_id}{RESET}")
    print(f"{'─'*55}")
    print(f"  Conductor     : {nombre} {apellido}")
    print(f"  Duración real : {duracion_real/60:.1f} min")
    print(f"  Distancia est.: {dist_km:.1f} km")
    print(f"  Velocidad máx.: {sim.max_vel:.1f} km/h")
    print(f"  Eventos OBD-II: {sim.total_eventos} ({batch_num} lotes)")
    print(f"  Alertas gen.  : {len(sim.alertas_locales)}")
    if sim.alertas_locales:
        tipos = {}
        for a in sim.alertas_locales:
            tipos[a] = tipos.get(a, 0) + 1
        for tipo, cnt in tipos.items():
            print(f"    · {tipo.replace('_', ' ')}: {cnt}x")
    print(f"{'─'*55}")
    print(f"  {BOLD}ÍNDICE DE RIESGO : {col_idx}{indice:.1f}{RESET}{BOLD} — {nivel}{RESET}")
    print(f"{'─'*55}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Simulador OBD-II para CIAS — replica el comportamiento del dongle real.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python obd_sim.py                              # perfil medio, usuario seed
  python obd_sim.py --perfil prudente            # conducción segura
  python obd_sim.py --perfil riesgoso            # conducción de alto riesgo
  python obd_sim.py --duracion 5                 # sesión de 5 minutos
  python obd_sim.py --email yo@mail.com --password MiClave1!
        """,
    )
    parser.add_argument("--api",      default=API_DEFAULT,  help="URL del backend CIAS")
    parser.add_argument("--perfil",   default="medio",      choices=["prudente", "medio", "riesgoso"],
                        help="Perfil de conducción a simular")
    parser.add_argument("--duracion", default=2, type=int,  help="Duración en minutos (default: 2)")
    parser.add_argument("--email",    default=None,         help="Email del conductor")
    parser.add_argument("--password", default=None,         help="Contraseña del conductor")
    args = parser.parse_args()

    if args.email and args.password:
        email, password = args.email, args.password
    else:
        creds = CREDENCIALES_DEFAULT[args.perfil]
        email, password = creds["email"], creds["password"]

    run(
        api=args.api,
        email=email,
        password=password,
        perfil=args.perfil,
        duracion_min=args.duracion,
    )


if __name__ == "__main__":
    main()
