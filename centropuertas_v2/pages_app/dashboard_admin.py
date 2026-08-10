"""
pages_app/dashboard_admin.py
==============================
Page "📊 Dashboard Global" : réservée au rôle 'admin' (voir app.py,
qui retire cette section du menu -- et donc de tout accès -- pour un
compte 'technicien'; cette page ne refait pas cette vérification
elle-même, par cohérence avec referencias.py/ajustes.py où le contrôle
d'accès est centralisé dans app.py).

Deux sections :
  1. Totaux de l'entreprise (tous techniciens confondus) + ventilation
     par technicien pour l'année choisie.
  2. Gestion des utilisateurs : création de comptes techniciens/admin
     et tableau récapitulatif des comptes existants (jamais les mots
     de passe/hash, même hachés -- voir database.get_technicians_resumen).
"""

from __future__ import annotations

import datetime as dt

import libsql_client
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db
from locales import t, t_role
from utils.styling import encabezado_pagina

COLOR_HORAS = "#2E7D32"
COLOR_EXTRA = "#81C784"


def render() -> None:
    encabezado_pagina(t("dashboard_admin.titulo"), t("dashboard_admin.subtitulo"), icono="groups")

    _seccion_totales_globales()
    st.divider()
    _seccion_gestion_usuarios()


def _seccion_totales_globales() -> None:
    hoy = dt.date.today()
    anios_disponibles = sorted(set(db.get_anios_disponibles_global() + [hoy.year]), reverse=True)
    anio = st.selectbox(
        t("dashboard.anio"), anios_disponibles,
        index=anios_disponibles.index(hoy.year) if hoy.year in anios_disponibles else 0,
    )

    totales = db.get_totales_anuales_global(anio)

    if totales["total_partes"] == 0:
        st.info(t("dashboard_admin.sin_datos"), icon="📭")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("dashboard.horas_trabajadas"), f'{totales["horas_normales"]:g} h')
    k2.metric(t("dashboard.horas_extra"), f'{totales["horas_extra"]:g} h')
    k3.metric(t("dashboard.dietas"), f'{totales["dietas"]:g}')
    k4.metric(t("dashboard_admin.total_technicians"), totales["total_technicians"])

    st.markdown(f"**{t('dashboard_admin.por_technician')}**")
    por_technician = db.get_totales_por_technician(anio)
    df = pd.DataFrame(por_technician)

    fig = go.Figure()
    fig.add_bar(x=df["technician_name"], y=df["horas_normales"],
                name=t("dashboard.horas_trabajadas"), marker_color=COLOR_HORAS)
    fig.add_bar(x=df["technician_name"], y=df["horas_extra"],
                name=t("dashboard.horas_extra"), marker_color=COLOR_EXTRA)
    fig.update_layout(
        barmode="group", height=380, legend=dict(orientation="h", y=1.12),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        df.rename(columns={
            "technician_name": t("dashboard_admin.columna_technician"),
            "horas_normales": t("dashboard.horas_trabajadas"),
            "horas_extra": t("dashboard.horas_extra"),
            "dietas": t("dashboard.dietas"),
            "total_partes": t("dashboard_admin.columna_total_partes"),
        }),
        hide_index=True, width="stretch",
    )


def _seccion_gestion_usuarios() -> None:
    """
    Création de comptes + tableau récapitulatif. Toujours affichée,
    même si `_seccion_totales_globales` s'est arrêtée court faute de
    partes pour l'année choisie -- gérer les accès ne doit jamais
    dépendre de l'existence de données.
    """
    st.markdown(f"**{t('dashboard_admin.gestion_usuarios')}**")
    st.caption(t("dashboard_admin.gestion_usuarios_desc"))

    with st.form("form_nuevo_usuario", clear_on_submit=True):
        login = st.text_input(t("dashboard_admin.nuevo_usuario_login"))
        nombre_mostrado = st.text_input(t("dashboard_admin.nuevo_usuario_nombre"))
        password = st.text_input(t("dashboard_admin.nuevo_usuario_password"), type="password")

        roles_codigo = db.ROLES_DISPONIBLES  # ["technicien", "admin"]
        roles_etiqueta = [t_role(r) for r in roles_codigo]
        role_etiqueta_sel = st.selectbox(t("dashboard_admin.nuevo_usuario_role"), roles_etiqueta, index=0)
        role_sel = roles_codigo[roles_etiqueta.index(role_etiqueta_sel)]

        if st.form_submit_button(t("dashboard_admin.crear_cuenta"), type="primary"):
            login_limpio = login.strip()
            nombre_limpio = nombre_mostrado.strip()
            if not login_limpio or not nombre_limpio or not password:
                st.error(t("dashboard_admin.error_campos_vacios"))
            elif db.technician_login_existe(login_limpio):
                st.error(t("dashboard_admin.error_usuario_existe"))
            else:
                # nombre_display (ici "Nom affiché") est le nom utilisé
                # partout ailleurs comme technician_name -- Dashboard,
                # Historial, Nuevo Parte -- distinct du login : c'est ce
                # qui apparaît sur les partes de travail (PDF, Excel,
                # cartes d'historique), donc pensé pour être lisible
                # ("Antonio García") plutôt qu'un identifiant de connexion.
                try:
                    db.crear_technician(login_limpio, password, nombre_display=nombre_limpio, role=role_sel)
                except libsql_client.LibsqlError:
                    # Filet de sécurité si deux admins créent le même login
                    # au même instant (course entre la vérification
                    # ci-dessus et l'INSERT) -- la contrainte UNIQUE de la
                    # base tranche, ce message reste correct dans ce cas.
                    st.error(t("dashboard_admin.error_usuario_existe"))
                else:
                    st.success(t("dashboard_admin.usuario_creado_ok", login=login_limpio), icon="✅")
                    st.rerun()

    st.markdown(f"**{t('dashboard_admin.tabla_usuarios')}**")
    usuarios = db.get_technicians_resumen()
    filas = [
        {
            t("dashboard_admin.columna_login"): u["login"],
            t("dashboard_admin.columna_nombre"): u["nombre_display"],
            t("dashboard_admin.columna_role"): t_role(u["role"]),
            t("dashboard_admin.columna_activo"): "✅" if u["activo"] else "❌",
            t("dashboard_admin.columna_creado_en"): u["creado_en"],
        }
        for u in usuarios
    ]
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
