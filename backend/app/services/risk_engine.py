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
  70 < I ≤ 85 → Medio  (amarillo)
  > 85  → Alto   (rojo)

Implementado con pandas/NumPy (HU-004 criterio de aceptación, tesis pág. 29).
"""

from typing import List
from datetime import datetime

import numpy as np
import pandas as pd

# Umbrales físicos
VEL_MAX_NORMAL = 90.0         # km/h — parámetro del prototipo
FRENADA_BRUSCA_MS2 = 5.0      # m/s² — módulo de desaceleración considerado brusco
ACEL_BRUSCA_MS2 = 3.5         # m/s² — aceleración considerada brusca
HORARIO_NOCTURNO_H = (22, 6)  # entre las 22:00 y las 06:00
DISTANCIA_ALTA_KM = 50.0      # km — escala de normalización del prototipo

PESOS = np.array([0.25, 0.25, 0.20, 0.15, 0.15])  # velocidad, frenadas, acel, horario, distancia


def _nivel(indice: float) -> str:
    if indice <= 70:
        return "Bajo"
    elif indice <= 85:
        return "Medio"
    return "Alto"


def _parse_timestamp(ts) -> pd.Timestamp | None:
    if ts is None:
        return None
    if isinstance(ts, str):
        try:
            return pd.Timestamp(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    if isinstance(ts, datetime):
        return pd.Timestamp(ts)
    return None


def calcular_indice(eventos: List[dict], inicio: datetime, fin: datetime) -> dict:
    """
    Calcula el índice de riesgo a partir de los eventos de una sesión usando
    pandas DataFrames y operaciones vectorizadas NumPy.

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

    # Garantizar columnas con valores numéricos (fillna=0 para datos faltantes)
    vel = df["velocidad_kmh"].fillna(0).to_numpy(dtype=float) if "velocidad_kmh" in df.columns else np.zeros(len(df))
    fren = np.abs(df["frenada_ms2"].fillna(0).to_numpy(dtype=float)) if "frenada_ms2" in df.columns else np.zeros(len(df))
    acel = df["aceleracion_ms2"].fillna(0).to_numpy(dtype=float) if "aceleracion_ms2" in df.columns else np.zeros(len(df))

    n = len(df)

    # Puntaje velocidad
    p_vel = np.clip(np.sum(vel > VEL_MAX_NORMAL) / n * 100, 0, 100)

    # Puntaje frenadas bruscas
    p_fren = np.clip(np.sum(fren > FRENADA_BRUSCA_MS2) / n * 100, 0, 100)

    # Puntaje aceleraciones bruscas
    p_acel = np.clip(np.sum(acel > ACEL_BRUSCA_MS2) / n * 100, 0, 100)

    # Puntaje horario nocturno
    inicio_h, fin_h = HORARIO_NOCTURNO_H
    timestamps = df["timestamp"].map(_parse_timestamp) if "timestamp" in df.columns else pd.Series([None] * n)
    horas = timestamps.dropna().map(lambda ts: ts.hour).to_numpy(dtype=int)
    if len(horas) > 0:
        # cruza medianoche (22-06); denominador = eventos con timestamp válido
        nocturnos = np.sum((horas >= inicio_h) | (horas < fin_h))
        p_hor = np.clip(nocturnos / len(horas) * 100, 0, 100)
    else:
        p_hor = 0.0

    # Distancia aproximada: velocidad promedio × duración en horas
    duracion_h = max((fin - inicio).total_seconds() / 3600, 0)
    vel_promedio = float(np.mean(vel)) if len(vel) > 0 else 0.0
    distancia_km = vel_promedio * duracion_h
    p_dist = np.clip(distancia_km / DISTANCIA_ALTA_KM * 100, 0, 100)

    # Índice ponderado con NumPy dot product
    puntajes = np.array([p_vel, p_fren, p_acel, p_hor, p_dist])
    indice = float(np.clip(np.dot(puntajes, PESOS), 0, 100))
    indice = round(indice, 2)

    return {
        "indice": indice,
        "nivel": _nivel(indice),
        "puntaje_velocidad": round(float(p_vel), 2),
        "puntaje_frenadas": round(float(p_fren), 2),
        "puntaje_aceleraciones": round(float(p_acel), 2),
        "puntaje_horario": round(float(p_hor), 2),
        "puntaje_distancia": round(float(p_dist), 2),
        "distancia_km": round(distancia_km, 2),
    }
