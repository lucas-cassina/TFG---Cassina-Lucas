"""
Perfiles de conducción para el simulador OBD-II (CIAS-002).
Cada perfil define distribuciones de velocidad, aceleración y frenada.
"""

import random
from datetime import datetime, timezone


def _evento_base(velocidad, acel, frenada, hora=None):
    now = datetime.now(timezone.utc)
    if hora is not None:
        now = now.replace(hour=hora % 24, minute=random.randint(0, 59))
    return {
        "velocidad_kmh": round(max(0, velocidad + random.gauss(0, 5)), 1),
        "aceleracion_ms2": round(acel + random.gauss(0, 0.3), 2),
        "frenada_ms2": round(frenada + random.gauss(0, 0.3), 2),
        "latitud": round(-31.4 + random.uniform(-0.05, 0.05), 6),
        "longitud": round(-64.2 + random.uniform(-0.05, 0.05), 6),
        "timestamp": now.isoformat(),
    }


def generar_perfil_prudente(n_eventos=20):
    """Velocidades moderadas, sin excesos. Horario diurno."""
    return [_evento_base(
        velocidad=random.uniform(40, 100),
        acel=random.uniform(0.5, 2.0),
        frenada=random.uniform(-2.0, -0.5),
        hora=random.randint(7, 20),
    ) for _ in range(n_eventos)]


def generar_perfil_medio(n_eventos=20):
    """Velocidades normales con algunas superaciones puntuales."""
    eventos = []
    for _ in range(n_eventos):
        exceso = random.random() < 0.15
        eventos.append(_evento_base(
            velocidad=random.uniform(60, 130) if exceso else random.uniform(40, 100),
            acel=random.uniform(0.5, 3.8) if exceso else random.uniform(0.5, 2.0),
            frenada=random.uniform(-4.0, -0.5) if exceso else random.uniform(-2.0, -0.5),
            hora=random.randint(6, 23),
        ))
    return eventos


def generar_perfil_riesgoso(n_eventos=20):
    """Altas velocidades, frenadas bruscas, horario nocturno frecuente."""
    return [_evento_base(
        velocidad=random.uniform(90, 180),
        acel=random.uniform(2.0, 6.0),
        frenada=random.uniform(-9.0, -3.0),
        hora=random.choice([random.randint(0, 5), random.randint(22, 23)]),
    ) for _ in range(n_eventos)]


PERFILES = {
    "prudente": generar_perfil_prudente,
    "medio": generar_perfil_medio,
    "riesgoso": generar_perfil_riesgoso,
}
