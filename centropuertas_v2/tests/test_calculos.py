"""Tests de utils/calculos.py -- seul module 100% pur du projet
(aucune dépendance à Streamlit ni à la base de données), donc le plus
simple à tester sans mock."""

from __future__ import annotations

from utils.calculos import dias_vacaciones_pendientes, resumen_de_partes


def test_resumen_de_partes_additionne_par_type_de_jornada():
    partes = [
        {"tipo_jornada": "Trabajo", "horas_normales": 8, "horas_extra": 1, "dietas": 10},
        {"tipo_jornada": "Trabajo", "horas_normales": 7, "horas_extra": 0, "dietas": 0},
        {"tipo_jornada": "Vacaciones", "horas_normales": 0, "horas_extra": 0, "dietas": 0},
        {"tipo_jornada": "Baja", "horas_normales": 0, "horas_extra": 0, "dietas": 0},
        {"tipo_jornada": "Guardia", "horas_normales": 0, "horas_extra": 2, "dietas": 5},
    ]

    resumen = resumen_de_partes(partes)

    assert resumen["horas_normales"] == 15
    assert resumen["horas_extra"] == 3
    assert resumen["dietas"] == 15
    assert resumen["dias_vacaciones"] == 1
    assert resumen["dias_baja"] == 1
    assert resumen["dias_guardia"] == 1
    assert resumen["total_partes"] == 5


def test_resumen_de_partes_liste_vide():
    resumen = resumen_de_partes([])

    assert resumen["total_partes"] == 0
    assert resumen["horas_normales"] == 0.0
    assert resumen["dias_vacaciones"] == 0


def test_dias_vacaciones_pendientes():
    assert dias_vacaciones_pendientes(22, 10) == 12
    assert dias_vacaciones_pendientes(22, 30) == 0
    assert dias_vacaciones_pendientes(0, 0) == 0
