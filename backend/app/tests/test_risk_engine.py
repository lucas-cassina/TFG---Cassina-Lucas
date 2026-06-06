import pytest
from datetime import datetime, timezone, timedelta
from app.services.risk_engine import calcular_indice, _nivel


def make_eventos(n=10, velocidad=60.0, acel=1.0, frenada=-1.0):
    now = datetime.now(timezone.utc)
    return [
        {
            "velocidad_kmh": velocidad,
            "aceleracion_ms2": acel,
            "frenada_ms2": frenada,
            "timestamp": (now + timedelta(seconds=i*30)).isoformat(),
        }
        for i in range(n)
    ]


def test_conductor_prudente():
    """Conducción prudente → índice Bajo."""
    inicio = datetime.now(timezone.utc)
    fin = inicio + timedelta(minutes=30)
    eventos = make_eventos(20, velocidad=60.0, acel=1.0, frenada=-1.5)
    res = calcular_indice(eventos, inicio, fin)
    assert res["nivel"] == "Bajo"
    assert res["indice"] <= 70


def test_conductor_riesgoso():
    """Conducción con excesos constantes → índice Alto."""
    inicio = datetime.now(timezone.utc)
    fin = inicio + timedelta(hours=1)
    eventos = make_eventos(30, velocidad=150.0, acel=5.0, frenada=-8.0)
    res = calcular_indice(eventos, inicio, fin)
    assert res["nivel"] in ("Medio", "Alto")
    assert res["indice"] > 50


def test_sin_eventos():
    """Sin eventos devuelve índice 0 y nivel Bajo."""
    inicio = datetime.now(timezone.utc)
    fin = inicio + timedelta(minutes=5)
    res = calcular_indice([], inicio, fin)
    assert res["indice"] == 0.0
    assert res["nivel"] == "Bajo"


def test_niveles():
    assert _nivel(50) == "Bajo"
    assert _nivel(70) == "Bajo"
    assert _nivel(71) == "Medio"
    assert _nivel(85) == "Medio"
    assert _nivel(86) == "Alto"
    assert _nivel(100) == "Alto"
