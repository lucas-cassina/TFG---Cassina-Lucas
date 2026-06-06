"""
Motor de cálculo del índice de riesgo asegurador (CIAS-002).

Integra 5 variables ponderadas, cada una normalizada a [0, 100]:
  - Velocidad:             25 %
  - Frenadas bruscas:      25 %
  - Aceleraciones bruscas: 20 %
  - Horario de conducción: 15 %
  - Distancia recorrida:   15 %

Índice resultado:
  ≤ 70  → Bajo   (verde)
  71-85 → Medio  (amarillo)
  > 85  → Alto   (rojo)
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

# Umbrales físicos
VEL_MAX_NORMAL = 120.0      # km/h — sobre este valor aumenta el riesgo
FRENADA_BRUSCA_MS2 = 5.0    # m/s² — módulo de desaceleración considerado brusco
ACEL_BRUSCA_MS2 = 3.5       # m/s² — aceleración considerada brusca
HORARIO_NOCTURNO_H = (22, 6) # entre las 22:00 y las 06:00
DISTANCIA_ALTA_KM = 300.0    # km — trayecto muy largo aumenta riesgo

PESOS = {
    "velocidad":       0.25,
    "frenadas":        0.25,
    "aceleraciones":   0.20,
    "horario":         0.15,
    "distancia":       0.15,
}


def _puntaje_velocidad(df: pd.DataFrame) -> float:
    """Proporción de eventos con velocidad > VEL_MAX_NORMAL, normalizada a [0,100]."""
    if df.empty:
        return 0.0
    proporcion = (df["velocidad_kmh"] > VEL_MAX_NORMAL).mean()
    return float(np.clip(proporcion * 100, 0, 100))


def _puntaje_frenadas(df: pd.DataFrame) -> float:
    """Proporción de frenadas brutas (frenada_ms2 < -FRENADA_BRUSCA_MS2)."""
    if df.empty:
        return 0.0
    proporcion = (df["frenada_ms2"].abs() > FRENADA_BRUSCA_MS2).mean()
    return float(np.clip(proporcion * 100, 0, 100))


def _puntaje_aceleraciones(df: pd.DataFrame) -> float:
    """Proporción de aceleraciones bruscas."""
    if df.empty:
        return 0.0
    proporcion = (df["aceleracion_ms2"] > ACEL_BRUSCA_MS2).mean()
    return float(np.clip(proporcion * 100, 0, 100))


def _puntaje_horario(df: pd.DataFrame) -> float:
    """Proporción de eventos en horario nocturno."""
    if df.empty or "timestamp" not in df.columns:
        return 0.0
    hours = pd.to_datetime(df["timestamp"]).dt.hour
    inicio, fin = HORARIO_NOCTURNO_H
    if inicio > fin:  # cruza medianoche
        nocturno = (hours >= inicio) | (hours < fin)
    else:
        nocturno = (hours >= inicio) & (hours < fin)
    return float(np.clip(nocturno.mean() * 100, 0, 100))


def _puntaje_distancia(distancia_km: float) -> float:
    """Distancia normalizada: a mayor distancia, mayor riesgo (hasta DISTANCIA_ALTA_KM)."""
    return float(np.clip((distancia_km / DISTANCIA_ALTA_KM) * 100, 0, 100))


def _nivel(indice: float) -> str:
    if indice <= 70:
        return "Bajo"
    elif indice <= 85:
        return "Medio"
    return "Alto"


def calcular_indice(eventos: List[dict], inicio: datetime, fin: datetime) -> dict:
    """
    Calcula el índice de riesgo a partir de los eventos de una sesión.

    Args:
        eventos: lista de dicts con keys velocidad_kmh, aceleracion_ms2,
                 frenada_ms2, timestamp (ISO string o datetime).
        inicio: datetime de apertura de sesión.
        fin:    datetime de cierre de sesión.

    Returns:
        dict con indice, nivel y puntajes parciales.
    """
    if not eventos:
        return {
            "indice": 0.0, "nivel": "Bajo",
            "puntaje_velocidad": 0.0, "puntaje_frenadas": 0.0,
            "puntaje_aceleraciones": 0.0, "puntaje_horario": 0.0,
            "puntaje_distancia": 0.0, "distancia_km": 0.0,
        }

    df = pd.DataFrame(eventos)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    # Distancia aproximada (velocidad promedio × tiempo en horas)
    duracion_h = max((fin - inicio).total_seconds() / 3600, 0)
    vel_promedio = df["velocidad_kmh"].mean() if not df.empty else 0.0
    distancia_km = vel_promedio * duracion_h

    p_vel  = _puntaje_velocidad(df)
    p_fren = _puntaje_frenadas(df)
    p_acel = _puntaje_aceleraciones(df)
    p_hor  = _puntaje_horario(df)
    p_dist = _puntaje_distancia(distancia_km)

    indice = (
        p_vel  * PESOS["velocidad"]      +
        p_fren * PESOS["frenadas"]       +
        p_acel * PESOS["aceleraciones"]  +
        p_hor  * PESOS["horario"]        +
        p_dist * PESOS["distancia"]
    )
    indice = round(float(np.clip(indice, 0, 100)), 2)

    return {
        "indice": indice,
        "nivel": _nivel(indice),
        "puntaje_velocidad": round(p_vel, 2),
        "puntaje_frenadas": round(p_fren, 2),
        "puntaje_aceleraciones": round(p_acel, 2),
        "puntaje_horario": round(p_hor, 2),
        "puntaje_distancia": round(p_dist, 2),
        "distancia_km": round(distancia_km, 2),
    }
