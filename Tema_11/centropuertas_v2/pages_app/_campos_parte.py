"""
pages_app/_campos_parte.py
============================
Bloc de champs du formulaire d'un parte (heures, indemnités, client,
type d'intervention, description, observations, collègue), factorisé
car utilisé à la fois par "Nuevo Parte" (page complète) et par le
dialogue d'édition rapide depuis "Historial".
"""

from __future__ import annotations

import sqlite3

import streamlit as st

import database as db
from locales import t


def _selector_referencia(label_key: str, sin_valor_key: str, opciones: list,
                          valor_actual_id: int | None, key: str) -> int | None:
    """Selectbox "Nom venant de la BDD" -> renvoie l'ID choisi (ou None)."""
    etiquetas = [t(sin_valor_key)] + [o["nombre"] for o in opciones]
    ids = [None] + [o["id"] for o in opciones]
    indice_actual = ids.index(valor_actual_id) if valor_actual_id in ids else 0
    seleccion = st.selectbox(t(label_key), etiquetas, index=indice_actual, key=key)
    return ids[etiquetas.index(seleccion)]


def campos_parte(parte_existente: sqlite3.Row | None, key_prefix: str) -> dict:
    """Dessine tous les champs (sauf la date) et renvoie les valeurs saisies."""
    tipos_valores = db.TIPOS_JORNADA
    tipos_etiquetas = [t(f"tipo.{v}") for v in tipos_valores]
    tipo_defecto = parte_existente["tipo_jornada"] if parte_existente else "Trabajo"
    tipo_jornada = st.selectbox(
        t("nuevo_parte.tipo_jornada"), tipos_etiquetas,
        index=tipos_valores.index(tipo_defecto), key=f"{key_prefix}_tipo",
    )
    tipo_jornada_valor = tipos_valores[tipos_etiquetas.index(tipo_jornada)]

    st.markdown(f"**{t('nuevo_parte.horas_dietas')}**")
    c1, c2, c3 = st.columns(3)
    horas_normales = c1.number_input(
        t("nuevo_parte.horas_normales"), min_value=0.0, max_value=24.0, step=0.5,
        value=float(parte_existente["horas_normales"]) if parte_existente else 8.0,
        key=f"{key_prefix}_horas",
    )
    horas_extra = c2.number_input(
        t("nuevo_parte.horas_extra"), min_value=0.0, max_value=24.0, step=0.5,
        value=float(parte_existente["horas_extra"]) if parte_existente else 0.0,
        key=f"{key_prefix}_extra",
    )
    dietas = c3.number_input(
        t("nuevo_parte.dietas"), min_value=0.0, max_value=10.0, step=1.0,
        value=float(parte_existente["dietas"]) if parte_existente else 0.0,
        key=f"{key_prefix}_dietas",
    )

    st.markdown(f"**{t('nuevo_parte.detalle_trabajo')}**")
    clientes = db.get_clients()
    tipos_intervencion = db.get_interventions_types()
    colegas = db.get_collegues()

    c1, c2 = st.columns(2)
    with c1:
        id_client = _selector_referencia(
            "nuevo_parte.cliente", "nuevo_parte.sin_cliente", clientes,
            parte_existente["id_client"] if parte_existente else None,
            key=f"{key_prefix}_cliente",
        )
    with c2:
        id_intervention = _selector_referencia(
            "nuevo_parte.tipo_intervencion", "nuevo_parte.sin_intervencion", tipos_intervencion,
            parte_existente["id_intervention"] if parte_existente else None,
            key=f"{key_prefix}_intervencion",
        )

    descripcion = st.text_area(
        t("nuevo_parte.descripcion"),
        value=parte_existente["descripcion"] if parte_existente else "",
        placeholder=t("nuevo_parte.descripcion_placeholder"), height=100,
        key=f"{key_prefix}_descripcion",
    )
    observaciones = st.text_area(
        t("nuevo_parte.observaciones"),
        value=parte_existente["observaciones"] if parte_existente else "",
        placeholder=t("nuevo_parte.observaciones_placeholder"), height=100,
        key=f"{key_prefix}_observaciones",
    )
    id_collegue = _selector_referencia(
        "nuevo_parte.colega", "nuevo_parte.sin_colega", colegas,
        parte_existente["id_collegue"] if parte_existente else None,
        key=f"{key_prefix}_colega",
    )

    return {
        "tipo_jornada": tipo_jornada_valor,
        "horas_normales": horas_normales,
        "horas_extra": horas_extra,
        "dietas": dietas,
        "id_client": id_client,
        "id_intervention": id_intervention,
        "descripcion": descripcion.strip(),
        "observaciones": observaciones.strip(),
        "id_collegue": id_collegue,
    }
