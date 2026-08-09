"""
pages_app/referencias.py
==========================
Page "🗂️ Referencias" : CRUD (Créer/Lire/Modifier/Supprimer) pour les
3 catalogues qui alimentent les menus déroulants de "Nuevo Parte" :
Clients, Types d'intervention et Compañeros.

Deux pièges à éviter avec `@st.dialog` (découverts en testant) :

  1. Le titre passé à `@st.dialog("...")` est figé au moment où Python
     importe ce module (une seule fois par process), donc PAS
     traduisible dynamiquement avec `t()`. On utilise un titre neutre
     dans le décorateur et on affiche le vrai titre traduit à
     l'intérieur du corps de la fonction, qui lui se ré-exécute à
     chaque ouverture du dialogue.

  2. Ne JAMAIS passer une fonction/lambda en argument à une fonction
     décorée par `@st.dialog` : Streamlit doit pouvoir re-invoquer ce
     même dialogue sur les reruns suivants (par ex. quand on clique un
     bouton à l'intérieur), et une closure fraîchement recréée à
     chaque script rerun n'est pas un argument stable -- le dialogue
     cesse alors de réagir aux clics (bug reproduit et confirmé). On
     passe donc uniquement des valeurs simples (id, chaîne "type
     d'entité") et on fait le dispatch vers la bonne fonction
     `database.py` à l'intérieur du dialogue.
"""

from __future__ import annotations

import sqlite3

import streamlit as st

import database as db
from locales import t
from utils.styling import encabezado_pagina

# Dispatch "type d'entité" -> fonctions CRUD correspondantes, utilisé
# par les dialogues génériques ci-dessous pour rester réutilisables
# sans avoir à leur passer une fonction en argument (voir piège n°2).
_GET_POR_TIPO = {
    "cliente": db.get_clients,
    "tipo": db.get_interventions_types,
    "colega": db.get_collegues,
}
_ACTUALIZAR_SIMPLE_POR_TIPO = {
    "tipo": db.actualizar_intervention_type,
    "colega": db.actualizar_collegue,
}
_ELIMINAR_POR_TIPO = {
    "cliente": db.eliminar_client,
    "tipo": db.eliminar_intervention_type,
    "colega": db.eliminar_collegue,
}
_TITULO_NUEVO_POR_TIPO = {
    "tipo": "referencias.nuevo_tipo",
    "colega": "referencias.nuevo_colega",
}


def _buscar_por_id(tipo: str, item_id: int) -> sqlite3.Row | None:
    for item in _GET_POR_TIPO[tipo]():
        if item["id"] == item_id:
            return item
    return None


# ----------------------------------------------------------------------
# Dialogues génériques (réutilisés par les 3 catalogues)
# ----------------------------------------------------------------------

@st.dialog(" ", width="small")
def _dialogo_confirmar_eliminar(tipo: str, item_id: int, nombre: str) -> None:
    st.markdown(f"### {t('referencias.confirmar_eliminar_titulo', nombre=nombre)}")
    st.caption(t("referencias.confirmar_eliminar_texto"))
    c1, c2 = st.columns(2)
    if c1.button(t("referencias.confirmar_eliminar_boton"), type="primary",
                 use_container_width=True, key="dlg_confirmar_eliminar_si"):
        _ELIMINAR_POR_TIPO[tipo](item_id)
        st.success(t("referencias.eliminado_ok"), icon="✅")
        st.rerun()
    if c2.button(t("common.cancelar"), use_container_width=True, key="dlg_confirmar_eliminar_no"):
        st.rerun()


@st.dialog(" ", width="small")
def _dialogo_editar_simple(tipo: str, item_id: int) -> None:
    """Édition d'une entité à un seul champ "nombre" (types, collègues)."""
    item = _buscar_por_id(tipo, item_id)
    st.markdown(f"### {t(_TITULO_NUEVO_POR_TIPO[tipo])}")
    nuevo_nombre = st.text_input(t("referencias.nombre"), value=item["nombre"], key="dlg_editar_simple_nombre")
    c1, c2 = st.columns(2)
    if c1.button(t("common.guardar"), type="primary", use_container_width=True, key="dlg_editar_simple_guardar"):
        if not nuevo_nombre.strip():
            st.error(t("referencias.nombre_obligatorio"))
        else:
            _ACTUALIZAR_SIMPLE_POR_TIPO[tipo](item_id, nuevo_nombre)
            st.success(t("referencias.actualizado_ok"), icon="✅")
            st.rerun()
    if c2.button(t("common.cancelar"), use_container_width=True, key="dlg_editar_simple_cancelar"):
        st.rerun()


@st.dialog(" ", width="large")
def _dialogo_editar_cliente(cliente_id: int) -> None:
    cliente = _buscar_por_id("cliente", cliente_id)
    st.markdown(f"### {t('common.editar')} — {cliente['nombre']}")
    nombre = st.text_input(t("referencias.nombre"), value=cliente["nombre"], key="dlg_editar_cli_nombre")
    direccion = st.text_input(t("referencias.direccion"), value=cliente["direccion"], key="dlg_editar_cli_direccion")
    telefono = st.text_input(t("referencias.telefono"), value=cliente["telefono"], key="dlg_editar_cli_telefono")
    notas = st.text_area(t("referencias.notas"), value=cliente["notas"], key="dlg_editar_cli_notas")
    c1, c2 = st.columns(2)
    if c1.button(t("common.guardar"), type="primary", use_container_width=True, key="dlg_editar_cli_guardar"):
        if not nombre.strip():
            st.error(t("referencias.nombre_obligatorio"))
        else:
            db.actualizar_client(cliente_id, nombre, direccion, telefono, notas)
            st.success(t("referencias.actualizado_ok"), icon="✅")
            st.rerun()
    if c2.button(t("common.cancelar"), use_container_width=True, key="dlg_editar_cli_cancelar"):
        st.rerun()


# ----------------------------------------------------------------------
# Onglet Clients
# ----------------------------------------------------------------------

def _tab_clientes() -> None:
    with st.expander(t("referencias.nuevo_cliente"), icon="➕"):
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            nombre = st.text_input(t("referencias.nombre"))
            c1, c2 = st.columns(2)
            direccion = c1.text_input(t("referencias.direccion"))
            telefono = c2.text_input(t("referencias.telefono"))
            notas = st.text_area(t("referencias.notas"))
            if st.form_submit_button(t("common.anadir"), type="primary"):
                if not nombre.strip():
                    st.error(t("referencias.nombre_obligatorio"))
                else:
                    db.crear_client(nombre, direccion, telefono, notas)
                    st.success(t("referencias.creado_ok"), icon="✅")
                    st.rerun()

    clientes = db.get_clients()
    if not clientes:
        st.info(t("referencias.lista_vacia"), icon="📭")
        return

    for cliente in clientes:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**🏢 {cliente['nombre']}**")
                detalles = [d for d in (cliente["direccion"], cliente["telefono"]) if d]
                if detalles:
                    st.caption(" · ".join(detalles))
                if cliente["notas"]:
                    st.caption(f"📝 {cliente['notas']}")
            with c2:
                if st.button(t("common.editar"), key=f"edit_cli_{cliente['id']}", use_container_width=True):
                    _dialogo_editar_cliente(cliente["id"])
                if st.button(t("common.eliminar"), key=f"del_cli_{cliente['id']}", use_container_width=True):
                    _dialogo_confirmar_eliminar("cliente", cliente["id"], cliente["nombre"])


# ----------------------------------------------------------------------
# Onglet Types d'intervention
# ----------------------------------------------------------------------

def _tab_tipos() -> None:
    with st.expander(t("referencias.nuevo_tipo"), icon="➕"):
        with st.form("form_nuevo_tipo", clear_on_submit=True):
            nombre = st.text_input(t("referencias.nombre"))
            if st.form_submit_button(t("common.anadir"), type="primary"):
                if not nombre.strip():
                    st.error(t("referencias.nombre_obligatorio"))
                else:
                    db.crear_intervention_type(nombre)
                    st.success(t("referencias.creado_ok"), icon="✅")
                    st.rerun()

    tipos = db.get_interventions_types()
    if not tipos:
        st.info(t("referencias.lista_vacia"), icon="📭")
        return

    for tipo in tipos:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**🔧 {tipo['nombre']}**")
            with c2:
                if st.button(t("common.editar"), key=f"edit_tip_{tipo['id']}", use_container_width=True):
                    _dialogo_editar_simple("tipo", tipo["id"])
                if st.button(t("common.eliminar"), key=f"del_tip_{tipo['id']}", use_container_width=True):
                    _dialogo_confirmar_eliminar("tipo", tipo["id"], tipo["nombre"])


# ----------------------------------------------------------------------
# Onglet Compañeros
# ----------------------------------------------------------------------

def _tab_colegas() -> None:
    with st.expander(t("referencias.nuevo_colega"), icon="➕"):
        with st.form("form_nuevo_colega", clear_on_submit=True):
            nombre = st.text_input(t("referencias.nombre"))
            if st.form_submit_button(t("common.anadir"), type="primary"):
                if not nombre.strip():
                    st.error(t("referencias.nombre_obligatorio"))
                else:
                    db.crear_collegue(nombre)
                    st.success(t("referencias.creado_ok"), icon="✅")
                    st.rerun()

    colegas = db.get_collegues()
    if not colegas:
        st.info(t("referencias.lista_vacia"), icon="📭")
        return

    for colega in colegas:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**👷 {colega['nombre']}**")
            with c2:
                if st.button(t("common.editar"), key=f"edit_col_{colega['id']}", use_container_width=True):
                    _dialogo_editar_simple("colega", colega["id"])
                if st.button(t("common.eliminar"), key=f"del_col_{colega['id']}", use_container_width=True):
                    _dialogo_confirmar_eliminar("colega", colega["id"], colega["nombre"])


def render() -> None:
    encabezado_pagina(t("referencias.titulo"), t("referencias.subtitulo"), icono="database")
    tab_clientes, tab_tipos, tab_colegas = st.tabs([
        t("referencias.tab_clientes"), t("referencias.tab_tipos"), t("referencias.tab_colegas"),
    ])
    with tab_clientes:
        _tab_clientes()
    with tab_tipos:
        _tab_tipos()
    with tab_colegas:
        _tab_colegas()
