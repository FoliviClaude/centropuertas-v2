"""
utils/pdf_export.py
====================
Genera el PDF del parte de trabajo mensual, listo para entregar a
administracion: logo de la empresa, tabla con los dias del mes,
resumen de totales y una linea para la firma del trabajador.

Se usa ReportLab (libreria pura Python, sin dependencias externas de
sistema) para poder generar el PDF en cualquier equipo sin instalar
nada mas que el paquete `reportlab`.
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

from database.db import MESES_ES
from utils.calculos import resumen_de_partes

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo_centropuertas.png"

# Color corporativo aproximado (tono azul/gris usado en la cabecera de
# las tablas). Ajustable si la empresa define una paleta oficial.
COLOR_CABECERA = colors.HexColor("#1F3B57")


def generar_pdf_mensual(
    anio: int,
    mes: int,
    nombre_trabajador: str,
    partes: list[sqlite3.Row],
) -> bytes:
    """
    Construye el PDF del parte mensual y devuelve los bytes del fichero
    (listos para pasar a `st.download_button`).

    partes: filas de `partes_diarios` del mes, ya ordenadas por fecha
    (viene de `database.db.get_partes_mes`).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloParte", parent=estilos["Heading1"], fontSize=16, spaceAfter=2,
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloParte", parent=estilos["Normal"], fontSize=10, textColor=colors.grey,
    )
    estilo_celda = ParagraphStyle(
        "Celda", parent=estilos["Normal"], fontSize=7.5, leading=9,
    )

    elementos = []

    # --- Cabecera: logo + titulo -----------------------------------
    nombre_mes = MESES_ES[mes - 1]
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=1.8 * cm, height=1.8 * cm)
        cabecera = Table(
            [[logo, Paragraph(
                f"<b>Parte de Trabajo Mensual</b><br/>"
                f"{nombre_mes} {anio} &nbsp;-&nbsp; {nombre_trabajador or 'Trabajador/a'}",
                estilo_titulo,
            )]],
            colWidths=[2.2 * cm, None],
        )
        cabecera.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(cabecera)
    else:
        elementos.append(Paragraph(
            f"Parte de Trabajo Mensual - {nombre_mes} {anio} - "
            f"{nombre_trabajador or 'Trabajador/a'}", estilo_titulo,
        ))

    elementos.append(Paragraph("Centropuertas - Montaje y mantenimiento de puertas automaticas", estilo_subtitulo))
    elementos.append(Spacer(1, 0.5 * cm))

    # --- Tabla de dias -----------------------------------------------
    cabeceras = ["Fecha", "Tipo", "Horas", "H. Extra", "Dietas", "Cliente",
                 "Nº Trab.", "Trabajo realizado", "Observaciones / Problemas", "Compañero"]
    filas = [cabeceras]
    for p in partes:
        if p["cliente"] and p["direccion"]:
            texto_cliente = f'<b>{p["cliente"]}</b><br/><font size="6">{p["direccion"]}</font>'
        else:
            texto_cliente = f'<b>{p["cliente"]}</b>' if p["cliente"] else "-"
        filas.append([
            p["fecha"],
            p["tipo_jornada"],
            f'{p["horas_jornada"]:g}' if p["horas_jornada"] else "-",
            f'{p["horas_extra"]:g}' if p["horas_extra"] else "-",
            f'{p["dietas"]:g}' if p["dietas"] else "-",
            Paragraph(texto_cliente, estilo_celda),
            p["numero_trabajo"] or "-",
            Paragraph(p["trabajo_realizado"] or "", estilo_celda),
            Paragraph(p["observaciones"] or "", estilo_celda),
            p["companero"] or "-",
        ])

    anchos = [1.8 * cm, 1.5 * cm, 1.2 * cm, 1.3 * cm, 1.2 * cm, 3.2 * cm,
              1.6 * cm, 5.0 * cm, 5.0 * cm, 2.7 * cm]
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CABECERA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.7 * cm))

    # --- Resumen del mes ------------------------------------------------
    resumen = resumen_de_partes(partes)
    filas_resumen = [
        ["Horas trabajadas", "Horas extra", "Dietas", "Días vacaciones",
         "Días de baja", "Días de guardia"],
        [
            f'{resumen["horas_totales"]:g} h',
            f'{resumen["horas_extra"]:g} h',
            f'{resumen["dietas"]:g}',
            str(resumen["dias_vacaciones"]),
            str(resumen["dias_baja"]),
            str(resumen["dias_guardia"]),
        ],
    ]
    tabla_resumen = Table(filas_resumen, colWidths=[4.2 * cm] * 6)
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6EF")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 1.5 * cm))

    # --- Firma -------------------------------------------------------
    firma = Table(
        [["Firma del trabajador/a:", "", "Fecha:", ""]],
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
