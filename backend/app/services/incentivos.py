"""
Módulo de incentivos y recompensas (CIAS-004 / HU-008).

Reglas:
  - Bronce: 1 mes consecutivo con nivel Bajo
  - Plata:  3 meses consecutivos con nivel Bajo
  - Oro:    6 meses consecutivos con nivel Bajo
  - 1 mes Medio: reinicia contador sin penalizar nivel actual
  - 1 mes Alto o 2 Medios consecutivos: desciende un escalón
"""

from typing import List

NIVELES_ORDEN = ["Sin nivel", "Bronce", "Plata", "Oro"]


def historial_nivel_por_mes(indices: list) -> list[str]:
    """
    Agrupa una lista de IndiceRiesgo por mes y devuelve el nivel predominante de cada mes.
    Extrae la lógica duplicada en conductor, reportes y auditor (A4).
    """
    meses: dict[str, list[str]] = {}
    for idx in indices:
        clave = idx.calculado_en.strftime("%Y-%m")
        meses.setdefault(clave, []).append(idx.nivel)
    return [max(set(v), key=v.count) for v in (meses[k] for k in sorted(meses))]
PUNTOS_POR_MES_BAJO = 10
PUNTOS_POR_MES_MEDIO = 3


def calcular_nivel_incentivo(historial_meses: List[str]) -> dict:
    """
    Determina el nivel de incentivo y puntos acumulados a partir del historial
    de niveles de riesgo mensual (lista ordenada cronológicamente, más reciente al final).

    Args:
        historial_meses: lista de strings "Bajo" | "Medio" | "Alto"

    Returns:
        dict con nivel_incentivo, meses_consecutivos_bajo, puntos_acumulados
    """
    meses_bajos_consecutivos = 0
    meses_medios_consecutivos = 0
    nivel_actual_idx = 0  # índice en NIVELES_ORDEN
    puntos = 0

    for nivel_mes in historial_meses:
        if nivel_mes == "Bajo":
            meses_bajos_consecutivos += 1
            meses_medios_consecutivos = 0
            puntos += PUNTOS_POR_MES_BAJO

            # Ascenso
            if meses_bajos_consecutivos >= 6:
                nivel_actual_idx = 3  # Oro
            elif meses_bajos_consecutivos >= 3:
                nivel_actual_idx = max(nivel_actual_idx, 2)  # Plata
            elif meses_bajos_consecutivos >= 1:
                nivel_actual_idx = max(nivel_actual_idx, 1)  # Bronce

        elif nivel_mes == "Medio":
            meses_medios_consecutivos += 1
            meses_bajos_consecutivos = 0
            puntos += PUNTOS_POR_MES_MEDIO

            # 2 meses medios consecutivos: descenso
            if meses_medios_consecutivos >= 2:
                nivel_actual_idx = max(0, nivel_actual_idx - 1)
                meses_medios_consecutivos = 0

        elif nivel_mes == "Alto":
            meses_bajos_consecutivos = 0
            meses_medios_consecutivos = 0
            # 1 mes Alto: descenso inmediato
            nivel_actual_idx = max(0, nivel_actual_idx - 1)

    return {
        "nivel_incentivo": NIVELES_ORDEN[nivel_actual_idx],
        "meses_consecutivos_bajo": meses_bajos_consecutivos,
        "puntos_acumulados": puntos,
    }


def nivel_para_incentivo(nivel_incentivo: str, nivel_requerido: str) -> bool:
    """Devuelve True si el conductor tiene acceso al incentivo según su nivel."""
    try:
        return NIVELES_ORDEN.index(nivel_incentivo) >= NIVELES_ORDEN.index(nivel_requerido)
    except ValueError:
        return False
