"""
pages_app/_campos_parte.py
============================
Bloque de campos del formulario de un parte diario (tipo de jornada,
horas, dietas, trabajo realizado, observaciones y compañero).

Se extrae a un modulo aparte porque se usa en dos sitios que antes
duplicaban el mismo formulario:
    - pages_app/nuevo_parte.py      (pagina completa)
    - pages_app/visualizar_mes.py   (modal de edicion rapida por tarjeta)

El prefijo `key` evita colisiones de `st.session_state` cuando el
formulario de edicion (dentro de un `st.dialog`) coexiste con el
formulario de la pagina "Nuevo Parte Diario".
"""

from __future__ import annotations

import sqlite3

import streamlit as st

from database import db


def campos_parte(parte_existente: sqlite3.Row | None, key_prefix: str) -> dict:
    """
    Dibuja los widgets del formulario y devuelve un diccionario con los
    valores introducidos, listo para pasar a `database.db.guardar_parte`
    (junto con la fecha, que se gestiona fuera de este helper).
    """
    tipo_default = parte_existente["tipo_jornada"] if parte_existente else "Trabajo"
    tipo_jornada = st.selectbox(
        "Tipo de jornada", db.TIPOS_JORNADA,
        index=db.TIPOS_JORNADA.index(tipo_default),
        key=f"{key_prefix}_tipo",
    )

    st.markdown("**⏱️ Horas y dietas**")
    c1, c2, c3 = st.columns(3)
    horas_jornada = c1.number_input(
        "Horas de jornada", min_value=0.0, max_value=24.0, step=0.5,
        value=float(parte_existente["horas_jornada"]) if parte_existente else 8.0,
        key=f"{key_prefix}_horas",
    )
    horas_extra = c2.number_input(
        "Horas extra", min_value=0.0, max_value=24.0, step=0.5,
        value=float(parte_existente["horas_extra"]) if parte_existente else 0.0,
        key=f"{key_prefix}_extra",
    )
    dietas = c3.number_input(
        "Dietas (nº)", min_value=0.0, max_value=10.0, step=1.0,
        value=float(parte_existente["dietas"]) if parte_existente else 0.0,
        key=f"{key_prefix}_dietas",
    )

    st.markdown("**🏢 Datos del cliente**")
    clientes_previos = db.get_clientes()
    cliente_actual = parte_existente["cliente"] if parte_existente else ""
    opciones_cliente = ["(sin cliente)"] + clientes_previos
    if cliente_actual and cliente_actual not in clientes_previos:
        opciones_cliente.append(cliente_actual)

    modo_cliente = st.radio(
        "Cliente", ["Elegir de la lista", "Escribir nuevo"],
        horizontal=True, label_visibility="collapsed",
        key=f"{key_prefix}_modo_cliente",
    )
    if modo_cliente == "Elegir de la lista":
        indice_cliente = opciones_cliente.index(cliente_actual) if cliente_actual in opciones_cliente else 0
        seleccion_cliente = st.selectbox(
            "Cliente", opciones_cliente, index=indice_cliente,
            key=f"{key_prefix}_cliente_lista",
        )
        cliente = "" if seleccion_cliente == "(sin cliente)" else seleccion_cliente
    else:
        cliente = st.text_input(
            "Nombre del cliente nuevo", value=cliente_actual,
            placeholder="Ej. Comunidad de Propietarios Av. Andalucía 12",
            key=f"{key_prefix}_cliente_nuevo",
        )
    direccion = st.text_input(
        "Dirección / ubicación del trabajo",
        value=parte_existente["direccion"] if parte_existente else "",
        placeholder="Ej. Calle Mayor 24, Nave 3 - Sevilla",
        key=f"{key_prefix}_direccion",
    )

    st.markdown("**🔧 Detalle del trabajo**")
    numero_trabajo = st.text_input(
        "Nº de trabajo / obra",
        value=parte_existente["numero_trabajo"] if parte_existente else "",
        placeholder="Ej. OT-2026-0143",
        key=f"{key_prefix}_numtrabajo",
    )
    trabajo_realizado = st.text_area(
        "Trabajo realizado",
        value=parte_existente["trabajo_realizado"] if parte_existente else "",
        placeholder="Ej. Instalación de puerta seccional en nave 3, ajuste de fotocélulas...",
        height=100,
        key=f"{key_prefix}_trabajo",
    )
    observaciones = st.text_area(
        "Observaciones / Problemas",
        value=parte_existente["observaciones"] if parte_existente else "",
        placeholder="Ej. Cruce de cuerdas en el eje, motor con ruido anómalo, pendiente de recambio...",
        height=100,
        key=f"{key_prefix}_observaciones",
    )

    companeros_previos = db.get_companeros()
    companero_actual = parte_existente["companero"] if parte_existente else ""
    opciones_companero = ["(sin compañero)"] + companeros_previos
    if companero_actual and companero_actual not in companeros_previos:
        opciones_companero.append(companero_actual)

    modo_companero = st.radio(
        "Compañero asignado", ["Elegir de la lista", "Escribir nuevo"],
        horizontal=True, label_visibility="collapsed",
        key=f"{key_prefix}_modo_companero",
    )
    if modo_companero == "Elegir de la lista":
        indice = opciones_companero.index(companero_actual) if companero_actual in opciones_companero else 0
        seleccion = st.selectbox(
            "Compañero asignado", opciones_companero, index=indice,
            key=f"{key_prefix}_companero_lista",
        )
        companero = "" if seleccion == "(sin compañero)" else seleccion
    else:
        companero = st.text_input(
            "Nombre del nuevo compañero", value=companero_actual,
            key=f"{key_prefix}_companero_nuevo",
        )

    return {
        "tipo_jornada": tipo_jornada,
        "horas_jornada": horas_jornada,
        "horas_extra": horas_extra,
        "dietas": dietas,
        "cliente": cliente.strip(),
        "direccion": direccion.strip(),
        "numero_trabajo": numero_trabajo.strip(),
        "trabajo_realizado": trabajo_realizado.strip(),
        "observaciones": observaciones.strip(),
        "companero": companero.strip(),
    }
