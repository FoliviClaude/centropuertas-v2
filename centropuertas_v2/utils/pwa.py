"""
utils/pwa.py
=============
Intégration PWA (Progressive Web App) : enregistrement du service worker
et bouton d'installation personnalisé.

Pourquoi `st.iframe` et pas `st.markdown(unsafe_allow_html=True)` ?
--------------------------------------------------------------------------
Vérifié empiriquement : Streamlit insère le HTML de `st.markdown` via
`innerHTML` côté React, ce qui neutralise silencieusement toute balise
`<script>` (comportement standard des navigateurs -- un script inséré par
innerHTML ne s'exécute jamais). `st.iframe` (remplaçant officiel de l'ancien
`st.components.v1.html`, déprécié) rend son contenu dans une iframe
`srcdoc` où le HTML est réellement *parsé*, donc les `<script>` s'y
exécutent normalement.

Cette iframe est de même origine que la page (même domaine) -- documenté
explicitement par Streamlit ("same-origin access to the Streamlit app"),
et re-vérifié empiriquement après migration -- donc son JavaScript peut
accéder à `window.parent` : c'est ce qui permet d'enregistrer le service
worker et d'écouter `beforeinstallprompt` pour le VRAI document de haut
niveau (celui de l'app), pas seulement pour l'iframe isolée. Vérifié avec
`navigator.serviceWorker.getRegistrations()` appelé depuis la page
principale : l'enregistrement y apparaît bien.
"""

from __future__ import annotations

import streamlit as st

VERT_CENTROPUERTAS = "#4CAF50"


def registrar_service_worker() -> None:
    """
    Enregistre static/sw.js (scope /app/static/, seule portée que
    Streamlit permet -- voir le commentaire en tête de sw.js). Ne fait
    rien silencieusement si le navigateur ne supporte pas les service
    workers (ex: certains navigateurs embarqués/webviews).
    """
    st.iframe(
        """
        <script>
        (function () {
            function registrar() {
                if (!('serviceWorker' in window.parent.navigator)) {
                    console.warn('CentroPuertas PWA: service worker no soportado en este navegador.');
                    return;
                }
                window.parent.navigator.serviceWorker
                    .register('/app/static/sw.js', { scope: '/app/static/' })
                    .then(function (reg) {
                        console.log('CentroPuertas PWA: service worker registrado, scope =', reg.scope);
                    })
                    .catch(function (err) {
                        console.error('CentroPuertas PWA: fallo al registrar el service worker:', err);
                    });
            }
            if (window.parent.document.readyState === 'complete') {
                registrar();
            } else {
                window.parent.addEventListener('load', registrar);
            }
        })();
        </script>
        """,
        height=1,  # st.iframe exige un entier > 0 (contrairement à l'ancien
        # components.v1.html qui acceptait 0) ; ce composant n'affiche rien,
        # 1px est la plus petite valeur valide pour le garder quasi invisible.
    )


def boton_instalar_app(
    etiqueta: str, etiqueta_instalada: str, ayuda_ios: str
) -> None:
    """
    Bouton "Installer l'application" personnalisé, basé sur l'événement
    `beforeinstallprompt` (Chrome/Edge/Android -- pas Safari/iOS, qui ne
    déclenche jamais cet événement : l'installation s'y fait uniquement
    à la main via le bouton "Partager > Sur l'écran d'accueil", d'où le
    message d'aide iOS affiché en complément).

    Le bouton reste invisible tant que `beforeinstallprompt` ne s'est pas
    déclenché (l'app n'est installable, ou déjà installée, ou le
    navigateur ne le supporte pas) -- c'est le navigateur qui décide.
    """
    st.iframe(
        f"""
        <div id="cp-pwa-wrap" style="font-family: Georgia, 'Times New Roman', serif;">
            <button id="cp-pwa-btn" style="
                display: none;
                background: {VERT_CENTROPUERTAS};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0.6rem 1.2rem;
                font-size: 0.95rem;
                font-weight: 700;
                font-family: inherit;
                cursor: pointer;
            ">📲 {etiqueta}</button>
            <div id="cp-pwa-msg" style="display:none; font-size: 0.9rem; color: #2E7D32;">
                ✅ {etiqueta_instalada}
            </div>
        </div>
        <script>
        (function () {{
            var btn = document.getElementById('cp-pwa-btn');
            var msg = document.getElementById('cp-pwa-msg');
            var deferredPrompt = null;

            window.parent.addEventListener('beforeinstallprompt', function (e) {{
                e.preventDefault();
                deferredPrompt = e;
                btn.style.display = 'inline-block';
            }});

            btn.addEventListener('click', function () {{
                if (!deferredPrompt) return;
                deferredPrompt.prompt();
                deferredPrompt.userChoice.finally(function () {{
                    deferredPrompt = null;
                    btn.style.display = 'none';
                }});
            }});

            window.parent.addEventListener('appinstalled', function () {{
                btn.style.display = 'none';
                msg.style.display = 'block';
            }});
        }})();
        </script>
        """,
        height=60,
    )
    st.caption(ayuda_ios)
