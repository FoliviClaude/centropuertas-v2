"""
utils/excel_export.py
======================
Génère l'export .xlsx de la vue mensuelle de "Historial", à partir du
même DataFrame que celui affiché à l'écran. Utilise `pandas.to_excel`
avec un buffer mémoire (`io.BytesIO`) -- pas de mise en forme avancée
ici (contrairement au PDF), juste un tableau propre et traduit, prêt à
être retravaillé dans Excel si besoin.
"""

from __future__ import annotations

import io
import sqlite3

import pandas as pd

from locales import t, t_tipo_jornada


def generar_excel_mensual(partes: list[sqlite3.Row]) -> bytes:
    """Construit le fichier Excel du mois et renvoie ses octets (pour `st.download_button`)."""
    filas = [
        {
            t("pdf.col_fecha"): p["fecha"],
            t("pdf.col_tipo"): t_tipo_jornada(p["tipo_jornada"]),
            t("pdf.col_horas"): p["horas_normales"],
            t("pdf.col_extra"): p["horas_extra"],
            t("pdf.col_dietas"): p["dietas"],
            t("pdf.col_cliente"): p["cliente_nombre"] or "",
            t("pdf.col_intervencion"): p["intervencion_nombre"] or "",
            t("pdf.col_descripcion"): p["descripcion"] or "",
            t("pdf.col_observaciones"): p["observaciones"] or "",
            t("pdf.col_colega"): p["collegue_nombre"] or "",
        }
        for p in partes
    ]
    df = pd.DataFrame(filas)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=t("historial.tab_mes")[:31])
    return buffer.getvalue()
