"""
app.py
======
Punto de entrada de la aplicacion. Se ejecuta con:

    streamlit run app.py

Responsabilidades de este archivo (y solo estas -- la logica de cada
pantalla vive en `pages_app/`, el acceso a datos en `database/db.py`):

    1. Configurar la pagina (titulo, icono, layout ancho).
    2. Inicializar la base de datos SQLite si es la primera vez que se
       ejecuta la app.
    3. Pintar la barra lateral con el logo de Centropuertas y el menu
       de navegacion.
    4. Enrutar hacia el modulo de la seccion elegida.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from database.db import init_db
from pages_app import ajustes, dashboard_anual, nuevo_parte, visualizar_mes
from utils.styling import inject_css

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo_centropuertas.png"

# Cada seccion del menu lateral se asocia a: (etiqueta con icono, funcion
# render() del modulo correspondiente). Anadir una seccion nueva en el
# futuro es tan sencillo como agregar una tupla mas a esta lista.
SECCIONES = [
    ("📝 Nuevo Parte Diario", nuevo_parte.render),
    ("📅 Visualizar Mes", visualizar_mes.render),
    ("📊 Dashboard Anual (Totales)", dashboard_anual.render),
    ("⚙️ Ajustes / Perfil", ajustes.render),
]


def _configurar_pagina() -> None:
    st.set_page_config(
        page_title="Centropuertas · Partes de Trabajo",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🛠️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _barra_lateral() -> str:
    """Pinta el logo + el menu de navegacion y devuelve la seccion activa."""
    with st.sidebar:
        col_logo, col_texto = st.columns([1, 2.2])
        with col_logo:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), width=56)
        with col_texto:
            st.markdown(
                '<div class="cp-sidebar-title">Centropuertas</div>'
                '<div class="cp-sidebar-subtitle">Partes de trabajo</div>',
                unsafe_allow_html=True,
            )
        st.markdown("<hr style='margin-top:0.4rem'>", unsafe_allow_html=True)

        # session_state guarda que boton se pulso por ultima vez, para
        # que la navegacion "recuerde" la pagina activa entre acciones
        # (por ejemplo, tras guardar un formulario con st.rerun()).
        if "seccion_activa" not in st.session_state:
            st.session_state["seccion_activa"] = SECCIONES[0][0]

        for etiqueta, _ in SECCIONES:
            es_activa = st.session_state["seccion_activa"] == etiqueta
            if st.button(
                etiqueta,
                key=f"nav_{etiqueta}",
                use_container_width=True,
                type="primary" if es_activa else "secondary",
            ):
                st.session_state["seccion_activa"] = etiqueta
                st.rerun()

        st.markdown("<div style='flex-grow:1'></div>", unsafe_allow_html=True)
        st.caption("Montaje y mantenimiento de puertas automáticas")

    return st.session_state["seccion_activa"]


def main() -> None:
    _configurar_pagina()
    init_db()
    inject_css()

    seccion_activa = _barra_lateral()

    # Enrutado: busca la funcion render() asociada a la seccion elegida
    # y la ejecuta. Un diccionario evita una cadena larga de if/elif.
    render_por_seccion = dict(SECCIONES)
    render_por_seccion[seccion_activa]()


if __name__ == "__main__":
    main()
