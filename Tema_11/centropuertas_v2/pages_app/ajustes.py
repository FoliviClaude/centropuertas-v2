"""
pages_app/ajustes.py
======================
Page "⚙️ Ajustes" : langue, année en cours et configuration globale
(heures de convention, jours de vacances, données du travailleur).
Le sélecteur de langue est aussi disponible dans la barre latérale ;
celui-ci est la version "officielle" qui persiste en base de données.
"""

from __future__ import annotations

import streamlit as st

import database as db
from locales import IDIOMAS_DISPONIBLES, set_idioma_activo, t
from utils.styling import encabezado_pagina


def render() -> None:
    encabezado_pagina(t("ajustes.titulo"), t("ajustes.subtitulo"), icono="settings")

    config = db.get_configuracion()

    with st.form("form_ajustes"):
        st.markdown(f"**🌐 {t('ajustes.idioma')}**")
        codigos = list(IDIOMAS_DISPONIBLES.keys())
        etiquetas = list(IDIOMAS_DISPONIBLES.values())
        idioma_sel = st.selectbox(
            t("ajustes.idioma"), etiquetas,
            index=codigos.index(config["idioma"]) if config["idioma"] in codigos else 0,
            label_visibility="collapsed",
        )

        st.markdown(f"**{t('ajustes.datos_trabajador')}**")
        nombre_trabajador = st.text_input(t("ajustes.nombre_trabajador"), value=config["nombre_trabajador"])
        c_empresa, c_nif = st.columns(2)
        empresa = c_empresa.text_input(t("ajustes.empresa"), value=config["empresa"])
        nif_cif = c_nif.text_input(t("ajustes.nif_cif"), value=config["nif_cif"])

        st.markdown(f"**{t('ajustes.config_global')}**")
        c1, c2, c3 = st.columns(3)
        anio_actual = c1.number_input(
            t("ajustes.anio_actual"), min_value=2000, max_value=2100,
            step=1, value=int(config["anio_actual"]),
        )
        horas_convenio = c2.number_input(
            t("ajustes.horas_convenio_anual"), min_value=0.0, max_value=3000.0,
            step=10.0, value=float(config["horas_convenio_anual"]),
        )
        dias_vacaciones = c3.number_input(
            t("ajustes.dias_vacaciones_anuales"), min_value=0, max_value=45,
            step=1, value=int(config["dias_vacaciones_anuales"]),
        )

        if st.form_submit_button(t("common.guardar"), type="primary"):
            codigo_idioma = codigos[etiquetas.index(idioma_sel)]
            db.actualizar_configuracion(
                idioma=codigo_idioma, anio_actual=anio_actual,
                horas_convenio_anual=horas_convenio, dias_vacaciones_anuales=dias_vacaciones,
                nombre_trabajador=nombre_trabajador.strip(), empresa=empresa.strip(),
                nif_cif=nif_cif.strip(),
            )
            set_idioma_activo(codigo_idioma)
            st.success(t("ajustes.guardado_ok"), icon="✅")
            st.rerun()

    st.divider()

    st.markdown(f"**{t('ajustes.backup')}**")
    st.caption(t("ajustes.backup_desc"))
    if db.DB_PATH.exists():
        with open(db.DB_PATH, "rb") as f:
            st.download_button(
                t("ajustes.descargar_backup"), data=f.read(),
                file_name="centropuertas_backup.db", mime="application/octet-stream",
            )
