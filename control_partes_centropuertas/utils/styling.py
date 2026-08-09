"""
utils/styling.py
=================
Ajustes visuales compartidos por toda la app: inyeccion de CSS ligero y
pequenos helpers para construir "tarjetas" (cards) en vez de tablas tipo
Excel.

Nota sobre el modo claro/oscuro: no se implementa un interruptor propio.
Streamlit ya trae un selector de tema nativo (menu ☰ > Settings > Theme
> Light / Dark / Custom) que respeta automaticamente el tema del sistema
operativo. Por eso el CSS de aqui evita colores fijos (blancos o negros
"a fuego") y usa unicamente los componentes nativos de Streamlit
(`st.container(border=True)`, `st.metric`, etc.), que ya se adaptan
solos al tema activo.
"""

from __future__ import annotations

import streamlit as st

# CSS global: solo tipografia, espaciados y detalles de la cabecera.
# Deliberadamente NO se fijan colores de fondo/texto para no romper el
# contraste cuando el usuario cambia entre modo claro y oscuro.
_CSS_GLOBAL = """
<style>
    /* Mas aire entre el borde de la ventana y el contenido */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Cabecera con el logo y el nombre de la app en la barra lateral */
    .cp-sidebar-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding-bottom: 0.5rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
    }
    .cp-sidebar-header img {
        border-radius: 10px;
    }
    .cp-sidebar-title {
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.15;
    }
    .cp-sidebar-subtitle {
        font-size: 0.78rem;
        opacity: 0.65;
    }

    /* Botones de navegacion a ancho completo y mas altos = mas facil
       de pulsar despues de un dia largo de trabajo con el movil/tablet */
    section[data-testid="stSidebar"] button {
        text-align: left;
        justify-content: flex-start;
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
    }

    /* Cabecera principal de cada pagina */
    .cp-page-title {
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }
    .cp-page-subtitle {
        opacity: 0.65;
        margin-bottom: 1.4rem;
    }
</style>
"""


def inject_css() -> None:
    """Inyecta el CSS global. Se llama una vez al principio de app.py."""
    st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)


def encabezado_pagina(titulo: str, subtitulo: str = "") -> None:
    """
    Pinta el titulo estandar de una pagina (mismo estilo en las 4
    secciones) para que la navegacion se sienta consistente.
    """
    st.markdown(f'<div class="cp-page-title">{titulo}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(
            f'<div class="cp-page-subtitle">{subtitulo}</div>',
            unsafe_allow_html=True,
        )
