"""
pages_app/nuevo_parte.py
=========================
Pagina "Nuevo Parte Diario": el formulario que sustituye a rellenar una
fila del Excel a mano. Al elegir una fecha que ya tiene parte guardado,
el formulario se rellena solo con esos datos para poder corregirlos.
"""

from __future__ import annotations

import datetime as dt

import streamlit as st

from database import db
from pages_app._campos_parte import campos_parte
from utils.styling import encabezado_pagina


def render() -> None:
    encabezado_pagina(
        "📝 Nuevo Parte Diario",
        "Registra tu jornada de hoy: horas, dietas, trabajo realizado e incidencias.",
    )

    fecha = st.date_input(
        "Fecha", value=dt.date.today(), format="DD/MM/YYYY", key="np_fecha",
    )
    fecha_iso = fecha.isoformat()
    parte_existente = db.get_parte_por_fecha(fecha_iso)

    if parte_existente:
        st.info(
            f"Ya existe un parte guardado para el {fecha.strftime('%d/%m/%Y')}. "
            "Los campos de abajo se han rellenado con esos datos; puedes "
            "modificarlos y volver a guardar.",
            icon="ℹ️",
        )

    with st.container(border=True):
        valores = campos_parte(parte_existente, key_prefix="np")

    guardar = st.button("💾 Guardar parte del día", type="primary", use_container_width=True)
    if guardar:
        db.guardar_parte(fecha=fecha_iso, **valores)
        st.success(f"Parte del {fecha.strftime('%d/%m/%Y')} guardado correctamente.", icon="✅")
        st.rerun()
