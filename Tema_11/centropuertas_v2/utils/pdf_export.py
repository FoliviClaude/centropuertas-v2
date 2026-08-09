"""
utils/pdf_export.py
====================
Génère le PDF du rapport de travail mensuel, entièrement traduit dans
la langue active : logo, tableau des jours, résumé du mois et une
ligne pour la signature du travailleur.
"""

from __future__ import annotations

import io
import sqlite3
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from locales import t, t_mes, t_tipo_jornada
from utils.calculos import resumen_de_partes

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo_centropuertas.png"

# Vert de la charte graphique Centropuertas pour la cabecera du tableau.
COLOR_CABECERA = colors.HexColor("#2E7D32")


def generar_pdf_mensual(
    anio: int,
    mes: int,
    nombre_trabajador: str,
    partes: list[sqlite3.Row],
    empresa: str = "",
    nif_cif: str = "",
) -> bytes:
    """Construit le PDF du rapport mensuel et renvoie les octets du fichier."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("TituloParte", parent=estilos["Heading1"], fontSize=16, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle("SubtituloParte", parent=estilos["Normal"], fontSize=10, textColor=colors.grey)
    estilo_celda = ParagraphStyle("Celda", parent=estilos["Normal"], fontSize=7.5, leading=9)

    elementos = []

    nombre_mes = t_mes(mes)
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=1.8 * cm, height=1.8 * cm)
        cabecera = Table(
            [[logo, Paragraph(
                f"<b>{t('pdf.titulo_parte')}</b><br/>"
                f"{nombre_mes} {anio} &nbsp;-&nbsp; {nombre_trabajador or '-'}",
                estilo_titulo,
            )]],
            colWidths=[2.2 * cm, None],
        )
        cabecera.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        elementos.append(cabecera)
    else:
        elementos.append(Paragraph(
            f"{t('pdf.titulo_parte')} - {nombre_mes} {anio} - {nombre_trabajador or '-'}", estilo_titulo,
        ))

    # Ligne "Empresa - NIF/CIF" : personnalise l'en-tête du rapport avec
    # les informations professionnelles saisies dans "Ajustes".
    linea_empresa = empresa or "Centropuertas"
    if nif_cif:
        linea_empresa += f" &nbsp;·&nbsp; {t('ajustes.nif_cif')}: {nif_cif}"
    elementos.append(Paragraph(linea_empresa, estilo_subtitulo))
    elementos.append(Paragraph(t("common.footer"), estilo_subtitulo))
    elementos.append(Spacer(1, 0.5 * cm))

    cabeceras = [
        t("pdf.col_fecha"), t("pdf.col_tipo"), t("pdf.col_horas"), t("pdf.col_extra"),
        t("pdf.col_dietas"), t("pdf.col_cliente"), t("pdf.col_intervencion"),
        t("pdf.col_descripcion"), t("pdf.col_observaciones"), t("pdf.col_colega"),
    ]
    filas = [cabeceras]
    for p in partes:
        filas.append([
            p["fecha"],
            t_tipo_jornada(p["tipo_jornada"]),
            f'{p["horas_normales"]:g}' if p["horas_normales"] else "-",
            f'{p["horas_extra"]:g}' if p["horas_extra"] else "-",
            f'{p["dietas"]:g}' if p["dietas"] else "-",
            p["cliente_nombre"] or "-",
            p["intervencion_nombre"] or "-",
            Paragraph(p["descripcion"] or "", estilo_celda),
            Paragraph(p["observaciones"] or "", estilo_celda),
            p["collegue_nombre"] or "-",
        ])

    anchos = [1.8 * cm, 1.7 * cm, 1.2 * cm, 1.3 * cm, 1.2 * cm, 3.0 * cm,
              2.8 * cm, 5.0 * cm, 5.0 * cm, 2.5 * cm]
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CABECERA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F7F0")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.7 * cm))

    resumen = resumen_de_partes(partes)
    filas_resumen = [
        [t("dashboard.horas_trabajadas"), t("dashboard.horas_extra"), t("dashboard.dietas"),
         t("dashboard.vacaciones_consumidas"), t("dashboard.dias_baja"), t("dashboard.dias_guardia")],
        [
            f'{resumen["horas_normales"]:g} h', f'{resumen["horas_extra"]:g} h',
            f'{resumen["dietas"]:g}', str(resumen["dias_vacaciones"]),
            str(resumen["dias_baja"]), str(resumen["dias_guardia"]),
        ],
    ]
    tabla_resumen = Table(filas_resumen, colWidths=[4.2 * cm] * 6)
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDF0DD")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elementos.append(Paragraph(f"<b>{t('pdf.resumen')}</b>", estilos["Normal"]))
    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 1.5 * cm))

    firma = Table(
        [[f"{t('pdf.firma')}:", "", f"{t('pdf.fecha_firma')}:", ""]],
        colWidths=[4 * cm, 6 * cm, 2.5 * cm, 6 * cm],
    )
    firma.setStyle(TableStyle([
        ("LINEBELOW", (1, 0), (1, 0), 0.7, colors.black),
        ("LINEBELOW", (3, 0), (3, 0), 0.7, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    elementos.append(firma)

    doc.build(elementos)
    return buffer.getvalue()
