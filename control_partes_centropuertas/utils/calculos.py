"""
utils/calculos.py
==================
Funciones de calculo puras (sin Streamlit ni SQL) que transforman filas
de la base de datos en los numeros que se muestran en pantalla o en el
PDF. Separarlas de db.py y de las paginas permite testearlas de forma
aislada y reutilizarlas tanto en el Dashboard como en la Exportacion PDF.
"""

from __future__ import annotations

import sqlite3


def resumen_de_partes(partes: list[sqlite3.Row]) -> dict:
    """
    Calcula el resumen (horas, extras, dietas, dias especiales) de una
    lista de partes ya filtrada -- por ejemplo, los partes de un mes.

    Se usa tanto en "Visualizar Mes" como en la generacion del PDF, de
    forma que ambos muestren siempre el mismo numero.
    """
    horas_totales = 0.0
    horas_extra = 0.0
    dietas = 0.0
    dias_vacaciones = 0
    dias_baja = 0
    dias_guardia = 0

    for p in partes:
        if p["tipo_jornada"] == "Trabajo":
            horas_totales += p["horas_jornada"] or 0
        horas_extra += p["horas_extra"] or 0
        dietas += p["dietas"] or 0
        if p["tipo_jornada"] == "Vacaciones":
            dias_vacaciones += 1
        elif p["tipo_jornada"] == "Baja":
            dias_baja += 1
        elif p["tipo_jornada"] == "Guardia":
            dias_guardia += 1

    return {
        "horas_totales": round(horas_totales, 2),
        "horas_extra": round(horas_extra, 2),
        "dietas": round(dietas, 2),
        "dias_vacaciones": dias_vacaciones,
        "dias_baja": dias_baja,
        "dias_guardia": dias_guardia,
        "total_partes": len(partes),
    }


def dias_vacaciones_pendientes(dias_asignados: int, dias_consumidos: int) -> int:
    """Dias de vacaciones que quedan por disfrutar en el año en curso."""
    return max(dias_asignados - dias_consumidos, 0)
