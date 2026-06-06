import pytest
from app.services.incentivos import calcular_nivel_incentivo


def test_sin_historial():
    res = calcular_nivel_incentivo([])
    assert res["nivel_incentivo"] == "Sin nivel"


def test_bronce_1_mes_bajo():
    res = calcular_nivel_incentivo(["Bajo"])
    assert res["nivel_incentivo"] == "Bronce"


def test_plata_3_meses_bajos():
    res = calcular_nivel_incentivo(["Bajo", "Bajo", "Bajo"])
    assert res["nivel_incentivo"] == "Plata"


def test_oro_6_meses_bajos():
    res = calcular_nivel_incentivo(["Bajo"] * 6)
    assert res["nivel_incentivo"] == "Oro"


def test_mes_medio_no_penaliza():
    """1 mes Medio reinicia contador pero mantiene nivel."""
    res = calcular_nivel_incentivo(["Bajo", "Bajo", "Bajo", "Medio"])
    assert res["nivel_incentivo"] == "Plata"
    assert res["meses_consecutivos_bajo"] == 0


def test_2_meses_medios_desciende():
    """2 meses medios consecutivos descienden un escalón."""
    res = calcular_nivel_incentivo(["Bajo", "Bajo", "Bajo", "Medio", "Medio"])
    assert res["nivel_incentivo"] == "Bronce"


def test_mes_alto_desciende():
    """1 mes Alto desciende inmediatamente."""
    res = calcular_nivel_incentivo(["Bajo", "Bajo", "Bajo", "Alto"])
    assert res["nivel_incentivo"] == "Bronce"


def test_puntos_acumulados():
    res = calcular_nivel_incentivo(["Bajo", "Bajo", "Medio"])
    assert res["puntos_acumulados"] == 10 + 10 + 3
