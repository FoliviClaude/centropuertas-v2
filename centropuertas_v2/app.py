"""
app.py
======
Point d'entrée de l'application. Se lance avec :

    streamlit run app.py

Responsabilités de ce fichier (et uniquement celles-ci -- la logique
de chaque écran vit dans `pages_app/`, l'accès aux données dans
`database.py`, l'authentification dans `auth.py`, les traductions dans
`locales.py`) :

    1. Configurer la page (titre, icône, layout large).
    2. Initialiser la base de données SQLite si besoin.
    3. Bloquer l'accès tant que personne n'est connecté (auth.py).
    4. Charger la langue active (mémorisée en base) dans la session.
    5. Afficher la barre latérale : logo Centropuertas, technicien
       connecté + déconnexion, sélecteur de langue, menu de navigation.
    6. Router vers le module de la section choisie.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import auth
import database as db
from locales import IDIOMAS_DISPONIBLES, get_idioma_activo, set_idioma_activo, t
from pages_app import ajustes, dashboard, dashboard_admin, historial, nuevo_parte, referencias
from utils.pwa import registrar_service_worker
from utils.styling import inject_css

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo_centropuertas.png"

# Chaque section du menu associe : (clé de traduction du libellé, icône
# Material Symbols, fonction render() du module correspondant). Les
# icônes utilisent le système Material Icons intégré à Streamlit
# (syntaxe ":material/nom_icone:") -- plus lisibles et cohérentes que
# des emojis, et elles s'adaptent automatiquement au thème actif.
#
# Accès par rôle (voir auth.es_admin) :
#   - technicien : saisie + son propre dashboard/historique (déjà
#     filtrés par technician_name -- rien de confidentiel n'y fuite).
#   - admin : en plus, le dashboard GLOBAL (tous techniciens) et la
#     gestion des données (Referencias = catalogues partagés, Ajustes
#     = configuration de l'entreprise).
SECCIONES_TECNICO = [
    ("nav.nuevo_parte", ":material/engineering:", nuevo_parte.render),
    ("nav.dashboard", ":material/monitoring:", dashboard.render),
    ("nav.historial", ":material/history:", historial.render),
]
SECCIONES_SOLO_ADMIN = [
    ("nav.dashboard_admin", ":material/groups:", dashboard_admin.render),
    ("nav.referencias", ":material/database:", referencias.render),
    ("nav.ajustes", ":material/settings:", ajustes.render),
]


def _secciones_para(usuario: dict) -> list[tuple[str, str, object]]:
    """
    Liste des sections visibles pour ce rôle. Recalculée à chaque appel
    (pas mise en cache) à partir de `usuario["role"]` -- jamais d'un
    widget modifiable côté client -- pour que la liste des sections
    reste correcte même si le rôle change (nouvelle connexion) sans
    redémarrer le serveur.
    """
    if usuario["role"] == "admin":
        return SECCIONES_TECNICO + SECCIONES_SOLO_ADMIN
    return SECCIONES_TECNICO


def _configurar_pagina() -> None:
  st.set_page_config(
        page_title="Centropuertas",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🚪",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Nettoyage de l'interface (Masquer header, footer et boutons)
    st.markdown("""
        <style>
        header {visibility: hidden !important;}
        [data-testid="stHeader"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        .stAppDeployButton {display: none !important;}
        </style>
    """, unsafe_allow_html=True)

def _ocultar_chrome_streamlit() -> None:
    """
    Masque les éléments d'interface propres à Streamlit (pas à
    l'application) pour un rendu plus épuré sur mobile.

    Le bouton "Deploy" et le menu ⋮ (rerun, clear cache...) sont déjà
    masqués de façon robuste par `client.toolbarMode = "minimal"` dans
    .streamlit/config.toml -- un réglage officiel qui ne dépend pas de
    la structure interne du DOM de Streamlit. #MainMenu/.stAppDeployButton
    ci-dessous sont donc redondants avec ce réglage -- gardés seulement
    en filet de sécurité si jamais toolbarMode était un jour réinitialisé
    (ex. surcharge par Streamlit Community Cloud).

    IMPORTANT -- NE JAMAIS masquer <header> ou [data-testid="stToolbar"]
    en entier (ex. "header {display: none}"), même si ça revient souvent
    dans des exemples trouvés en ligne (y compris des extraits fournis
    par l'utilisateur à deux reprises) -- vérifié en conditions réelles
    (viewport mobile, Playwright) : le bouton qui réouvre la barre
    latérale une fois repliée (data-testid="stExpandSidebarButton") est
    un DESCENDANT de stToolbar, lui-même dans <header>, dans cette
    version de Streamlit. "display: none" sur un ancêtre est en plus
    irrécupérable pour un descendant (contrairement à "visibility:
    hidden", qu'un enfant peut réafficher) -- masquer l'un ou l'autre de
    ces deux éléments rend ce bouton définitivement injoignable et
    bloque toute navigation sur mobile une fois la sidebar repliée.
    Testé et confirmé cassé avant d'écarter ces deux règles.

    [data-testid="stDecoration"] (la fine barre colorée tout en haut de
    la page) est en revanche un élément à part, sans aucun lien avec la
    sidebar -- son masquage est sûr.
    """
   


def _pantalla_login() -> None:
    """Écran affiché tant que personne n'est connecté : logo + formulaire."""
    _, columna_centro, _ = st.columns([1, 1.2, 1])
    with columna_centro:
        st.write("")
        st.write("")
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=90)
        st.markdown(f'<div class="cp-page-title">{t("auth.titulo")}</div>', unsafe_allow_html=True)
        st.caption(t("auth.subtitulo"))
        auth.formulario_login()


def _inyectar_etiquetas_pwa() -> None:
    """
    Ajoute les balises nécessaires pour que l'app soit installable comme
    PWA (icône sur l'écran d'accueil du téléphone, ouverture en plein
    écran sans barre de navigateur).

    Le manifest.json et les icônes vivent dans "static/" et sont servis
    par Streamlit lui-même (option "server.enableStaticServing = true"
    dans .streamlit/config.toml) à l'URL /app/static/<fichier>.

    Limite connue : `st.markdown` insère ce HTML dans le corps de la
    page, pas dans son <head> -- Chrome/Android le détecte quand même
    (il scanne tout le DOM pour "link[rel=manifest]"), mais surtout,
    l'invite d'installation automatique n'apparaît que sur une origine
    "sécurisée" (HTTPS, ou "localhost"). En HTTP simple sur le réseau
    local (ex: http://192.168.x.x:8501 depuis un téléphone), le
    manifest est bien détecté mais Chrome n'affichera pas la bannière
    d'installation automatique ; "Ajouter à l'écran d'accueil" depuis
    le menu du navigateur fonctionne quand même grâce à ces balises.
    """
    st.markdown(
        """
        <link rel="manifest" href="/app/static/manifest.json">
        <link rel="icon" href="/app/static/icon-192.png">
        <link rel="apple-touch-icon" sizes="180x180" href="/app/static/icon-180.png">
        <meta name="theme-color" content="#4CAF50">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="CentroPuertas">
        """,
        unsafe_allow_html=True,
    )
    # Le service worker (static/sw.js) doit passer par st.iframe -- un
    # <script> via st.markdown ne s'execute jamais (verifie : Streamlit
    # insere ce HTML par innerHTML, qui neutralise les balises <script>
    # par design du navigateur). Voir le docstring de utils/pwa.py.
    registrar_service_worker()


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


def _barra_lateral(usuario: dict) -> str:
    """Dessine le logo, le technicien connecté, le sélecteur de langue et le menu."""
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

        st.markdown("<hr style='margin-top:0.4rem; margin-bottom:0.4rem'>", unsafe_allow_html=True)

        # Technicien connecté + déconnexion. Le nom affiché ici est la
        # même valeur (session_state) utilisée pour filtrer/insérer les
        # partes -- c'est la garantie visuelle que "ce qu'on voit" et
        # "ce qui filtre les données" sont bien la même personne.
        col_nom, col_logout = st.columns([2.4, 1])
        col_nom.markdown(t("auth.sesion_como", nombre=usuario["nombre"]))
        if col_logout.button("⏻", help=t("auth.cerrar_sesion")):
            auth.cerrar_sesion()

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

        secciones = _secciones_para(usuario)
        claves_permitidas = {clave for clave, _, _ in secciones}

        # Garde-fou : "seccion_activa" peut contenir une valeur d'un rôle
        # différent si un autre compte s'est connecté dans la même session
        # de navigateur (cerrar_sesion() ne vide que l'identité, pas le
        # reste de session_state) -- ne jamais afficher une page admin à
        # partir d'une valeur laissée par une session précédente.
        if st.session_state.get("seccion_activa") not in claves_permitidas:
            st.session_state["seccion_activa"] = secciones[0][0]

        for clave_etiqueta, icono, _ in secciones:
            etiqueta = t(clave_etiqueta)
            es_activa = st.session_state["seccion_activa"] == clave_etiqueta
            if st.button(
                etiqueta, key=f"nav_{clave_etiqueta}", icon=icono, width="stretch",
                type="primary" if es_activa else "secondary",
            ):
                st.session_state["seccion_activa"] = clave_etiqueta
                st.rerun()

        st.caption(t("common.footer"))

    return st.session_state["seccion_activa"]


def main() -> None:
    _configurar_pagina()
    _ocultar_chrome_streamlit()
    db.init_db()

    usuario = auth.usuario_actual()
    if usuario is None:
        _pantalla_login()
        return

    _cargar_idioma_inicial()
    inject_css()
    _inyectar_etiquetas_pwa()

    seccion_activa = _barra_lateral(usuario)

    render_por_seccion = {clave: fn for clave, _, fn in _secciones_para(usuario)}
    render_por_seccion[seccion_activa]()


if __name__ == "__main__":
    main()
