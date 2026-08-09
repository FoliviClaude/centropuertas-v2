"""
pages_app/dashboard.py
========================
Page "📊 Dashboard (Totales)" : le "cerveau" de l'app. Calcule
automatiquement les totaux annuels/mensuels (heures, heures sup,
indemnités, vacances/gardes) et les représente avec des graphiques
Plotly.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db
from locales import t, t_mes
from utils.calculos import dias_vacaciones_pendientes
from utils.styling import encabezado_pagina

COLOR_HORAS = "#2E7D32"      # vert Centropuertas (foncé)
COLOR_EXTRA = "#81C784"      # vert clair
COLOR_DIETAS = "#4CAF50"     # vert charte


def render() -> None:
    encabezado_pagina(t("dashboard.titulo"), t("dashboard.subtitulo"), icono="monitoring")

    hoy = dt.date.today()
    anios_disponibles = sorted(set(db.get_anios_disponibles() + [hoy.year]), reverse=True)
    anio = st.selectbox(
        t("dashboard.anio"), anios_disponibles,
        index=anios_disponibles.index(hoy.year) if hoy.year in anios_disponibles else 0,
    )

    totales = db.get_totales_anuales(anio)
    config = db.get_configuracion()

    if totales["total_partes"] == 0:
        st.info(t("dashboard.sin_datos"), icon="📭")
        return

    pendientes = dias_vacaciones_pendientes(config["dias_vacaciones_anuales"], totales["dias_vacaciones"])

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(t("dashboard.horas_trabajadas"), f'{totales["horas_normales"]:g} h')
    k2.metric(t("dashboard.horas_extra"), f'{totales["horas_extra"]:g} h')
    k3.metric(t("dashboard.dietas"), f'{totales["dietas"]:g}')
    k4.metric(t("dashboard.vacaciones_consumidas"), f'{totales["dias_vacaciones"]}',
              help=t("dashboard.de_dias", dias=config["dias_vacaciones_anuales"]))
    k5.metric(t("dashboard.vacaciones_pendientes"), f'{pendientes}')

    k6, k7 = st.columns(2)
    k6.metric(t("dashboard.dias_baja"), totales["dias_baja"])
    k7.metric(t("dashboard.dias_guardia"), totales["dias_guardia"])

    # --- Progression sur le convenio anual (Heures annuelles de la
    # convention, configurable dans Ajustes) --------------------------
    horas_convenio = config["horas_convenio_anual"] or 0
    if horas_convenio > 0:
        horas_hechas = totales["horas_normales"] + totales["horas_extra"]
        progreso = min(horas_hechas / horas_convenio, 1.0)
        st.markdown(f"**{t('dashboard.progreso_convenio', horas_convenio=horas_convenio)}**")
        st.progress(progreso, text=f"{horas_hechas:g} h / {horas_convenio:g} h ({progreso * 100:.0f}%)")

    st.divider()

    datos_mes = db.get_totales_por_mes(anio)
    df = pd.DataFrame(datos_mes)
    df_completo = pd.DataFrame({"mes": range(1, 13)}).merge(df, on="mes", how="left").fillna(0)
    df_completo["nombre_mes"] = df_completo["mes"].apply(lambda m: t_mes(int(m))[:3])

    col_barras, col_lineas = st.columns(2)

    with col_barras:
        st.markdown(f"**{t('dashboard.grafico_horas')}**")
        fig_barras = go.Figure()
        fig_barras.add_bar(x=df_completo["nombre_mes"], y=df_completo["horas_normales"],
                            name=t("dashboard.horas_trabajadas"), marker_color=COLOR_HORAS)
        fig_barras.add_bar(x=df_completo["nombre_mes"], y=df_completo["horas_extra"],
                            name=t("dashboard.horas_extra"), marker_color=COLOR_EXTRA)
        fig_barras.update_layout(
            barmode="group", height=380, legend=dict(orientation="h", y=1.12),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    with col_lineas:
        st.markdown(f"**{t('dashboard.grafico_dietas')}**")
        fig_lineas = go.Figure()
        fig_lineas.add_trace(go.Scatter(
            x=df_completo["nombre_mes"], y=df_completo["dietas"],
            mode="lines+markers", name=t("dashboard.dietas"),
            line=dict(color=COLOR_DIETAS, width=3),
        ))
        fig_lineas.update_layout(
            height=380, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_lineas, use_container_width=True)
