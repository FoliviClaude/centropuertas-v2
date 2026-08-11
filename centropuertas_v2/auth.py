"""
auth.py
========
Authentification multi-utilisateur : formulaire de connexion, gestion
de la session (qui est connecté), déconnexion.

Volontairement simple (pas de streamlit-authenticator, pas de cookie,
pas de fournisseur OIDC externe) : chaque technicien a un compte local
(table "technicians" dans database.py, mot de passe haché en PBKDF2 --
jamais en clair). C'est un choix délibéré, pas une facilité :
- st.login()/st.user natifs de Streamlit exigent un fournisseur OIDC
  externe (Google, Microsoft, Okta...) avec client_id/client_secret --
  hors sujet pour une petite équipe qui veut juste un login/mot de
  passe local, sans compte chez un tiers.
- streamlit-authenticator ajoute une dépendance externe (+ bcrypt, qui
  pose parfois des soucis de compilation sous Windows) pour un besoin
  qu'une cinquantaine de lignes de stdlib couvrent très bien ici.

Limite à connaître : la session vit dans `st.session_state`, donc
propre à l'onglet/navigateur ouvert -- fermer l'onglet ou redémarrer le
serveur redemande une connexion. Aucune "mémorisation" façon cookie
n'a été demandée ; à ajouter séparément si besoin un jour.
"""

from __future__ import annotations

import streamlit as st

import database as db
from locales import t

CLE_SESION = "usuario"


def usuario_actual() -> dict | None:
    """Renvoie {"login": ..., "nombre": ..., "role": ...} si quelqu'un est connecté, sinon None."""
    return st.session_state.get(CLE_SESION)


def nombre_tecnico_actual() -> str:
    """
    Raccourci le plus utilisé dans les pages : le nom du technicien
    connecté, à passer tel quel à toutes les fonctions de database.py
    qui filtrent par `technician_name`.

    Ne doit être appelé que dans du code qui s'exécute APRÈS le gate de
    connexion (app.py garantit déjà ça) -- une KeyError ici est un bug
    de câblage, pas un cas à masquer silencieusement.
    """
    return st.session_state[CLE_SESION]["nombre"]


def es_admin() -> bool:
    """
    True si le technicien connecté a le rôle 'admin'. Sert à app.py
    pour décider quelles sections afficher -- ne doit JAMAIS être
    déduit d'un widget modifiable côté client, seulement de la valeur
    posée en session au moment du login (voir formulario_login), qui
    provient elle-même directement de la colonne `role` en base.
    """
    usuario = usuario_actual()
    return usuario is not None and usuario["role"] == "admin"


def cerrar_sesion() -> None:
    st.session_state.pop(CLE_SESION, None)
    st.rerun()


def formulario_login() -> None:
    """
    Affiche le formulaire login + mot de passe. En cas de succès, écrit
    la session et relance le script (app.py affichera alors l'app).
    """
    with st.form("form_login"):
        login = st.text_input(t("auth.usuario"))
        password = st.text_input(t("auth.contrasena"), type="password")
        enviado = st.form_submit_button(t("auth.entrar"), type="primary", width="stretch")

        if enviado:
            tecnico = db.verificar_credenciales(login, password)
            if tecnico is None:
                # Message volontairement générique : ne jamais indiquer si
                # c'est le login ou le mot de passe qui est incorrect,
                # pour ne pas révéler quels comptes existent.
                st.error(t("auth.error_credenciales"))
            else:
                st.session_state[CLE_SESION] = {
                    "login": tecnico["login"],
                    "nombre": tecnico["nombre_display"],
                    "role": tecnico["role"],
                }
                st.rerun()
