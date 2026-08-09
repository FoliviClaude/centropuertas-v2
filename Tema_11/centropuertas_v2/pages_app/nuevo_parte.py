"""
pages_app/nuevo_parte.py
=========================
Page "📍 Nuevo Parte" : formulaire de saisie quotidienne rapide, avec
menus déroulants alimentés dynamiquement par la base de données
(Client, Type d'intervention, Compañero).
"""

from __future__ import annotations

import datetime as dt

import streamlit as st

import database as db
from locales import t
from pages_app._campos_parte import campos_parte
from utils.styling import encabezado_pagina


def render() -> None:
    encabezado_pagina(t("nuevo_parte.titulo"), t("nuevo_parte.subtitulo"), icono="engineering")

    fecha = st.date_input(t("nuevo_parte.fecha"), value=dt.date.today(),
                           format="DD/MM/YYYY", key="np_fecha")
    fecha_iso = fecha.isoformat()
    parte_existente = db.get_parte_por_fecha(fecha_iso)

    if parte_existente:
        st.info(t("nuevo_parte.ya_existe", fecha=fecha.strftime("%d/%m/%Y")), icon="ℹ️")

    if not db.get_clients():
        st.caption("💡 " + t("nuevo_parte.sin_referencias_aviso", tipo=t("referencias.tab_clientes")))
    if not db.get_interventions_types():
        st.caption("💡 " + t("nuevo_parte.sin_referencias_aviso", tipo=t("referencias.tab_tipos")))
    if not db.get_collegues():
        st.caption("💡 " + t("nuevo_parte.sin_referencias_aviso", tipo=t("referencias.tab_colegas")))

    with st.container(border=True):
        valores = campos_parte(parte_existente, key_prefix="np")

    if st.button(t("nuevo_parte.guardar_parte"), type="primary", use_container_width=True):
        db.guardar_parte(fecha=fecha_iso, **valores)
        st.success(t("nuevo_parte.guardado_ok", fecha=fecha.strftime("%d/%m/%Y")), icon="✅")
        st.rerun()
