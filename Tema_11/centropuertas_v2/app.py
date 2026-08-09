"""
app.py
======
Point d'entrée de l'application. Se lance avec :

    streamlit run app.py

Responsabilités de ce fichier (et uniquement celles-ci -- la logique
de chaque écran vit dans `pages_app/`, l'accès aux données dans
`database.py`, les traductions dans `locales.py`) :

    1. Configurer la page (titre, icône, layout large).
    2. Initialiser la base de données SQLite si besoin.
    3. Charger la langue active (mémorisée en base) dans la session.
    4. Afficher la barre latérale : logo Centropuertas, sélecteur de
       langue (🇪🇸/🇫🇷/🇬🇧) et menu de navigation.
    5. Router vers le module de la section choisie.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import database as db
from locales import IDIOMAS_DISPONIBLES, get_idioma_activo, set_idioma_activo, t
from pages_app import ajustes, dashboard, historial, nuevo_parte, referencias
from utils.styling import inject_css

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo_centropuertas.png"

# Chaque section du menu associe : (clé de traduction du libellé, icône
# Material Symbols, fonction render() du module correspondant). Les
# icônes utilisent le système Material Icons intégré à Streamlit
# (syntaxe ":material/nom_icone:") -- plus lisibles et cohérentes que
# des emojis, et elles s'adaptent automatiquement au thème actif.
SECCIONES = [
    ("nav.nuevo_parte", ":material/engineering:", nuevo_parte.render),
    ("nav.referencias", ":material/database:", referencias.render),
    ("nav.dashboard", ":material/monitoring:", dashboard.render),
    ("nav.historial", ":material/history:", historial.render),
    ("nav.ajustes", ":material/settings:", ajustes.render),
]


def _configurar_pagina() -> None:
    st.set_page_config(
        page_title="Centropuertas",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🚪",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _cargar_idioma_inicial() -> None:
    """
    Au tout premier chargement de la session, la langue active se
    récupère depuis la configuration en base (mémorisée d'une session
    à l'autre) ; ensuite elle reste gérée en session_state pour rester
    réactive sans requête supplémentaire.
    """
    if "idioma" not in st.session_state:
        config = db.get_configuracion()
        set_idioma_activo(config["idioma"])


def _barra_lateral() -> str:
    """Dessine le logo, le sélecteur de langue et le menu ; renvoie la section active."""
    with st.sidebar:
        col_logo, col_texto = st.columns([1, 2.2])
        with col_logo:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), width=56)
        with col_texto:
            st.markdown(
                f'<div class="cp-sidebar-title">{t("common.app_name")}</div>'
                f'<div class="cp-sidebar-subtitle">{t("common.app_tagline")}</div>',
                unsafe_allow_html=True,
            )

        codigos = list(IDIOMAS_DISPONIBLES.keys())
        etiquetas = list(IDIOMAS_DISPONIBLES.values())
        idioma_actual = get_idioma_activo()
        idioma_elegido = st.selectbox(
            "🌐", etiquetas, index=codigos.index(idioma_actual),
            label_visibility="collapsed", key="selector_idioma_sidebar",
        )
        codigo_elegido = codigos[etiquetas.index(idioma_elegido)]
        if codigo_elegido != idioma_actual:
            set_idioma_activo(codigo_elegido)
            db.actualizar_idioma(codigo_elegido)
            st.rerun()

        st.markdown("<hr style='margin-top:0.4rem'>", unsafe_allow_html=True)

        if "seccion_activa" not in st.session_state:
            st.session_state["seccion_activa"] = SECCIONES[0][0]

        for clave_etiqueta, icono, _ in SECCIONES:
            etiqueta = t(clave_etiqueta)
            es_activa = st.session_state["seccion_activa"] == clave_etiqueta
            if st.button(
                etiqueta, key=f"nav_{clave_etiqueta}", icon=icono, use_container_width=True,
                type="primary" if es_activa else "secondary",
            ):
                st.session_state["seccion_activa"] = clave_etiqueta
                st.rerun()

        st.caption(t("common.footer"))

    return st.session_state["seccion_activa"]


def main() -> None:
    _configurar_pagina()
    db.init_db()
    _cargar_idioma_inicial()
    inject_css()

    seccion_activa = _barra_lateral()

    render_por_seccion = {clave: fn for clave, _, fn in SECCIONES}
    render_por_seccion[seccion_activa]()


if __name__ == "__main__":
    main()
