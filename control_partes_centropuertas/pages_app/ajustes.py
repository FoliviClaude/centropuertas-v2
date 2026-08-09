"""
pages_app/ajustes.py
======================
Pagina "Ajustes/Perfil": datos del trabajador que se usan en el resto
de la app (cabecera del PDF, calculo de vacaciones pendientes) y una
copia de seguridad rapida de la base de datos SQLite.
"""

from __future__ import annotations

import streamlit as st

from database.db import DB_PATH, get_perfil, update_perfil
from utils.styling import encabezado_pagina


def render() -> None:
    encabezado_pagina(
        "⚙️ Ajustes / Perfil",
        "Datos del trabajador y preferencias de la aplicación.",
    )

    perfil = get_perfil()

    with st.form("form_perfil"):
        st.markdown("**👤 Datos del trabajador**")
        nombre = st.text_input("Nombre y apellidos", value=perfil["nombre_trabajador"])
        empresa = st.text_input("Empresa", value=perfil["empresa"])

        c1, c2 = st.columns(2)
        horas_jornada = c1.number_input(
            "Horas de jornada estándar", min_value=1.0, max_value=12.0,
            step=0.5, value=float(perfil["horas_jornada_estandar"]),
        )
        dias_vacaciones = c2.number_input(
            "Días de vacaciones anuales", min_value=0, max_value=45,
            step=1, value=int(perfil["dias_vacaciones_anuales"]),
        )

        guardado = st.form_submit_button("💾 Guardar cambios", type="primary")
        if guardado:
            update_perfil(nombre.strip(), empresa.strip(), horas_jornada, dias_vacaciones)
            st.success("Perfil actualizado.", icon="✅")
            st.rerun()

    st.divider()

    st.markdown("**🎨 Apariencia**")
    st.caption(
        "Esta app usa el selector de tema nativo de Streamlit: abre el menú "
        "**⋮ (arriba a la derecha) → Settings → Theme** para cambiar entre "
        "modo claro, oscuro o personalizado."
    )

    st.divider()

    st.markdown("**💾 Copia de seguridad**")
    st.caption("Descarga el fichero de base de datos SQLite completo como copia de seguridad.")
    if DB_PATH.exists():
        with open(DB_PATH, "rb") as f:
            st.download_button(
                "⬇️ Descargar copia de seguridad (partes.db)",
                data=f.read(),
                file_name="partes_centropuertas_backup.db",
                mime="application/octet-stream",
            )
