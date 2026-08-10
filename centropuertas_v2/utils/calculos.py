"""
utils/calculos.py
==================
Fonctions de calcul pures (sans Streamlit ni SQL), réutilisées à la
fois par l'historique/PDF et le dashboard, pour garantir que les deux
affichent toujours les mêmes chiffres.
"""

from __future__ import annotations

from libsql_client import Row


def resumen_de_partes(partes: list[Row]) -> dict:
    """Calcule le résumé (heures, extra, indemnités, jours spéciaux) d'une liste de partes."""
    horas_normales = 0.0
    horas_extra = 0.0
    dietas = 0.0
    dias_vacaciones = 0
    dias_baja = 0
    dias_guardia = 0

    for p in partes:
        if p["tipo_jornada"] == "Trabajo":
            horas_normales += p["horas_normales"] or 0
        horas_extra += p["horas_extra"] or 0
        dietas += p["dietas"] or 0
        if p["tipo_jornada"] == "Vacaciones":
            dias_vacaciones += 1
        elif p["tipo_jornada"] == "Baja":
            dias_baja += 1
        elif p["tipo_jornada"] == "Guardia":
            dias_guardia += 1

    return {
        "horas_normales": round(horas_normales, 2),
        "horas_extra": round(horas_extra, 2),
        "dietas": round(dietas, 2),
        "dias_vacaciones": dias_vacaciones,
        "dias_baja": dias_baja,
        "dias_guardia": dias_guardia,
        "total_partes": len(partes),
    }


def dias_vacaciones_pendientes(dias_asignados: int, dias_consumidos: int) -> int:
    """Jours de vacances restant à prendre dans l'année en cours."""
    return max(dias_asignados - dias_consumidos, 0)
