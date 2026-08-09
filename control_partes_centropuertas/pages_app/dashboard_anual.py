"""
pages_app/dashboard_anual.py
==============================
Pagina "Dashboard Anual (Totales)": el "cerebro" de la app. Calcula de
forma automatica los totales del año (horas, extras, dietas, dias de
vacaciones/baja/guardia) y los representa con graficos, sustituyendo la
hoja "TOTALES" con formulas manuales del Excel original.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import db
from utils.calculos import dias_vacaciones_pendientes
from utils.styling import encabezado_pagina

# Paleta de colores consistente para las distintas series de los graficos.
COLOR_HORAS = "#2E6F9E"
COLOR_EXTRA = "#E08E45"
COLOR_DIETAS = "#4C9F70"


def render() -> None:
    encabezado_pagina(
        "📊 Dashboard Anual",
        "Totales automáticos del año: horas, extras, dietas y vacaciones.",
    )

    hoy = dt.date.today()
    anios_disponibles = sorted(set(db.get_anios_disponibles() + [hoy.year]), reverse=True)
    anio = st.selectbox("Año", anios_disponibles, index=anios_disponibles.index(hoy.year) if hoy.year in anios_disponibles else 0)

    totales = db.get_totales_anuales(anio)
    perfil = db.get_perfil()

    if totales["total_partes"] == 0:
        st.info("Todavía no hay partes registrados para este año.", icon="📭")
        return

    # --- KPIs principales ---------------------------------------------
    pendientes = dias_vacaciones_pendientes(
        perfil["dias_vacaciones_anuales"], totales["dias_vacaciones"]
    )
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Horas trabajadas", f'{totales["horas_totales"]:g} h')
    k2.metric("Horas extra", f'{totales["horas_extra"]:g} h')
    k3.metric("Dietas", f'{totales["dietas"]:g}')
    k4.metric("Vacaciones consumidas", f'{totales["dias_vacaciones"]} días',
              help=f'De {perfil["dias_vacaciones_anuales"]} días asignados al año')
    k5.metric("Vacaciones pendientes", f'{pendientes} días')

    k6, k7 = st.columns(2)
    k6.metric("Días de baja", totales["dias_baja"])
    k7.metric("Días de guardia", totales["dias_guardia"])

    st.divider()

    # --- Graficos mes a mes --------------------------------------------
    datos_mes = db.get_totales_por_mes(anio)
    df = pd.DataFrame(datos_mes)
    # Rellenamos los 12 meses aunque no tengan datos, para que el eje X
    # del grafico siempre muestre el año completo.
    df_completo = pd.DataFrame({"mes": range(1, 13)}).merge(df, on="mes", how="left").fillna(0)
    df_completo["nombre_mes"] = df_completo["mes"].apply(lambda m: db.MESES_ES[int(m) - 1][:3])

    col_barras, col_lineas = st.columns(2)

    with col_barras:
        st.markdown("**Horas trabajadas vs. horas extra por mes**")
        fig_barras = go.Figure()
        fig_barras.add_bar(x=df_completo["nombre_mes"], y=df_completo["horas_totales"],
                            name="Horas", marker_color=COLOR_HORAS)
        fig_barras.add_bar(x=df_completo["nombre_mes"], y=df_completo["horas_extra"],
                            name="Horas extra", marker_color=COLOR_EXTRA)
        fig_barras.update_layout(
            barmode="group", height=380, legend=dict(orientation="h", y=1.12),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    with col_lineas:
        st.markdown("**Evolución de dietas por mes**")
        fig_lineas = go.Figure()
        fig_lineas.add_trace(go.Scatter(
            x=df_completo["nombre_mes"], y=df_completo["dietas"],
            mode="lines+markers", name="Dietas", line=dict(color=COLOR_DIETAS, width=3),
        ))
        fig_lineas.update_layout(
            height=380, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_lineas, use_container_width=True)
