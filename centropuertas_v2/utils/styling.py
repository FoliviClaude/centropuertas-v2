"""
utils/styling.py
=================
CSS partagé par toute l'app : typographie, espacements et en-tête de
la barre latérale. Volontairement minimal -- le mode clair/sombre est
géré par le sélecteur natif de Streamlit (menu ⋮ > Settings > Theme),
donc on évite ici toute couleur de fond/texte fixe qui casserait le
contraste selon le thème actif. Le vert de la charte graphique est
déjà appliqué automatiquement par Streamlit via `primaryColor` dans
`.streamlit/config.toml` (boutons, liens, sliders, etc.).
"""

from __future__ import annotations

import streamlit as st

VERT_CENTROPUERTAS = "#4CAF50"

_CSS_GLOBAL = f"""
<style>
    /* Typographie de marque : Merriweather en gras partout (titres,
       menus, texte courant). Le poids 700 est le seul chargé depuis
       Google Fonts car c'est le seul utilisé (font-weight: bold ci-
       dessous), inutile d'alourdir le chargement avec les autres. */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@700&display=swap');

    html, body, [class*="st-emotion-cache"], .stApp,
    h1, h2, h3, h4, h5, h6, p, span, div, label, li, a, button,
    input, textarea, select {{
        font-family: 'Merriweather', serif;
        font-weight: bold;
    }}

    /* Les icônes Material (barre latérale) ont besoin de leur propre
       police à ligatures ("Material Symbols Rounded") pour afficher un
       glyphe -- la règle générale ci-dessus les ferait sinon retomber
       sur Merriweather, qui n'a pas ces ligatures, et le nom brut de
       l'icône (ex. "engineering") s'afficherait en texte au lieu du
       pictogramme. On les exclut donc explicitement. */
    [data-testid="stIconMaterial"] {{
        font-family: "Material Symbols Rounded" !important;
        font-weight: normal !important;
    }}

    /* Icône Material dans le titre de page (voir encabezado_pagina) --
       même police à ligatures que ci-dessus, même exclusion nécessaire
       vis-à-vis de la règle générale Merriweather. Sert à afficher, à
       côté du titre, exactement la même icône que celle du bouton de
       navigation correspondant dans la barre latérale. */
    .cp-page-title-icon {{
        font-family: "Material Symbols Rounded" !important;
        font-weight: normal !important;
        font-size: 1.7rem;
        vertical-align: -4px;
        margin-right: 0.4rem;
        color: {VERT_CENTROPUERTAS};
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    /* En-tête logo + nom dans la barre latérale */
    .cp-sidebar-header {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding-bottom: 0.6rem;
        margin-bottom: 0.6rem;
        border-bottom: 2px solid {VERT_CENTROPUERTAS};
    }}
    .cp-sidebar-title {{
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.15;
    }}
    .cp-sidebar-subtitle {{
        font-size: 0.78rem;
        opacity: 0.65;
    }}

    /* Boutons de navigation pleine largeur, plus hauts = plus faciles
       à toucher sur mobile après une longue journée de travail */
    section[data-testid="stSidebar"] button {{
        text-align: left;
        justify-content: flex-start;
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
    }}

    .cp-page-title {{
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }}
    .cp-page-subtitle {{
        opacity: 0.65;
        margin-bottom: 1.4rem;
    }}
</style>
"""


def inject_css() -> None:
    """Injecte le CSS global. Appelé une seule fois au début de app.py."""
    st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)


def encabezado_pagina(titulo: str, subtitulo: str = "", icono: str | None = None) -> None:
    """
    Titre standard d'une page, identique dans les 5 sections du menu.

    `icono` : nom brut d'une icône Material Symbols (ex. "engineering"),
    le même que celui passé en `icon=":material/engineering:"` au
    bouton de navigation correspondant dans app.py -- pour que le
    titre de la page affiche visuellement la même icône que celle
    utilisée dans la barre latérale pour y accéder.
    """
    icono_html = f'<span class="cp-page-title-icon">{icono}</span>' if icono else ""
    st.markdown(f'<div class="cp-page-title">{icono_html}{titulo}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f'<div class="cp-page-subtitle">{subtitulo}</div>', unsafe_allow_html=True)
