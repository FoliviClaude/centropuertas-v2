"""
pages_app/visualizar_mes.py
=============================
Pagina "Visualizar Mes": lista los partes de un mes como tarjetas (en
vez de una cuadricula de Excel), permite editarlos en el momento desde
un modal, buscar/filtrar en todo el historico y exportar el parte
mensual a PDF o a Excel.
"""

from __future__ import annotations

import datetime as dt
import sqlite3

import streamlit as st

from database import db
from pages_app._campos_parte import campos_parte
from utils.calculos import resumen_de_partes
from utils.excel_export import generar_excel_mensual
from utils.pdf_export import generar_pdf_mensual
from utils.styling import encabezado_pagina


@st.dialog("✏️ Editar parte del día", width="large")
def _dialogo_editar(parte: sqlite3.Row) -> None:
    """
    Modal de edicion en linea: se abre sobre la propia tarjeta, con los
    campos ya rellenados con los datos reales guardados ese dia. Guardar
    aqui hace un UPSERT sobre la misma fecha, asi que no crea partes
    duplicados.
    """
    fecha = dt.date.fromisoformat(parte["fecha"])
    dia_semana = db.DIAS_ES[fecha.weekday()]
    st.caption(f"{dia_semana} {fecha.strftime('%d/%m/%Y')}")

    valores = campos_parte(parte, key_prefix=f"edit_{parte['id']}")

    c1, c2 = st.columns(2)
    if c1.button("💾 Guardar cambios", type="primary", use_container_width=True):
        db.guardar_parte(fecha=parte["fecha"], **valores)
        st.success("Parte actualizado.", icon="✅")
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.rerun()


def _tarjeta_parte(parte: sqlite3.Row, key_prefix: str) -> None:
    """
    Dibuja un unico parte diario como tarjeta, con acciones de editar/eliminar.

    `key_prefix` distingue las claves de los widgets segun la pestaña
    donde se dibuja la tarjeta ("mes" o "busqueda"): Streamlit renderiza
    el contenido de todas las pestañas a la vez (solo oculta con CSS la
    que no esta activa), asi que si el mismo parte apareciera en las dos
    pestañas a la vez sin un prefijo distinto, sus botones colisionarian
    por tener la misma `key`.
    """
    fecha = dt.date.fromisoformat(parte["fecha"])
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            dia_semana = db.DIAS_ES[fecha.weekday()]
            st.markdown(f"**📅 {dia_semana} {fecha.strftime('%d/%m/%Y')}** · {parte['tipo_jornada']}")
            if parte["cliente"]:
                linea_cliente = f"🏢 **{parte['cliente']}**"
                if parte["direccion"]:
                    linea_cliente += f" — {parte['direccion']}"
                st.markdown(linea_cliente)
            if parte["trabajo_realizado"]:
                st.markdown(f"🔧 {parte['trabajo_realizado']}")
            if parte["observaciones"]:
                st.markdown(f"⚠️ *{parte['observaciones']}*")
            detalles = []
            if parte["numero_trabajo"]:
                detalles.append(f"Nº trabajo: {parte['numero_trabajo']}")
            if parte["companero"]:
                detalles.append(f"Compañero: {parte['companero']}")
            if detalles:
                st.caption(" · ".join(detalles))
        with c2:
            st.metric("Horas", f'{parte["horas_jornada"]:g}')
            if parte["horas_extra"]:
                st.caption(f'+ {parte["horas_extra"]:g} h extra')
            if parte["dietas"]:
                st.caption(f'{parte["dietas"]:g} dieta(s)')
            if st.button("✏️ Editar", key=f"edit_{key_prefix}_{parte['id']}", use_container_width=True):
                _dialogo_editar(parte)
            if st.button("🗑️ Eliminar", key=f"del_{key_prefix}_{parte['id']}", use_container_width=True):
                db.eliminar_parte(parte["id"])
                st.rerun()


def render() -> None:
    encabezado_pagina(
        "📅 Visualizar Mes",
        "Consulta, edita y exporta los partes de trabajo guardados.",
    )

    tab_mes, tab_buscador = st.tabs(["Vista mensual", "🔎 Buscador / historial"])

    # ------------------------------------------------------------------
    # TAB 1: vista mensual + exportacion a PDF / Excel
    # ------------------------------------------------------------------
    with tab_mes:
        hoy = dt.date.today()
        anios_disponibles = sorted(set(db.get_anios_disponibles() + [hoy.year]), reverse=True)

        col_anio, col_mes = st.columns(2)
        anio = col_anio.selectbox("Año", anios_disponibles, index=anios_disponibles.index(hoy.year) if hoy.year in anios_disponibles else 0)
        mes = col_mes.selectbox(
            "Mes", options=list(range(1, 13)),
            index=hoy.month - 1,
            format_func=lambda m: db.MESES_ES[m - 1],
        )

        partes_mes = db.get_partes_mes(anio, mes)

        if not partes_mes:
            st.info("Todavía no hay partes guardados para este mes.", icon="🗓️")
        else:
            resumen = resumen_de_partes(partes_mes)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Horas trabajadas", f'{resumen["horas_totales"]:g} h')
            k2.metric("Horas extra", f'{resumen["horas_extra"]:g} h')
            k3.metric("Dietas", f'{resumen["dietas"]:g}')
            k4.metric("Vacaciones / Bajas / Guardias",
                      f'{resumen["dias_vacaciones"]} / {resumen["dias_baja"]} / {resumen["dias_guardia"]}')

            perfil = db.get_perfil()
            nombre_archivo = f"parte_{db.MESES_ES[mes - 1].lower()}_{anio}"

            col_pdf, col_excel = st.columns(2)
            with col_pdf:
                pdf_bytes = generar_pdf_mensual(anio, mes, perfil["nombre_trabajador"], partes_mes)
                st.download_button(
                    "📄 Exportar a PDF",
                    data=pdf_bytes,
                    file_name=f"{nombre_archivo}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            with col_excel:
                excel_bytes = generar_excel_mensual(anio, mes, perfil["nombre_trabajador"], partes_mes)
                st.download_button(
                    "📊 Exportar a Excel",
                    data=excel_bytes,
                    file_name=f"{nombre_archivo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            st.divider()
            for parte in partes_mes:
                _tarjeta_parte(parte, key_prefix="mes")

    # ------------------------------------------------------------------
    # TAB 2: buscador libre en todo el historico
    # ------------------------------------------------------------------
    with tab_buscador:
        st.caption(
            "Busca, por ejemplo, todas las instalaciones hechas para un cliente "
            "o con un compañero concreto, o un problema recurrente por palabra clave."
        )
        texto = st.text_input("Palabra clave (trabajo u observaciones)", placeholder="Ej. fotocélula, cruce de cuerdas...")
        c1, c2, c3 = st.columns(3)
        clientes = ["(todos)"] + db.get_clientes()
        cliente_filtro = c1.selectbox("Cliente", clientes)
        companeros = ["(todos)"] + db.get_companeros()
        companero_filtro = c2.selectbox("Compañero", companeros)
        anios_filtro = ["(todos)"] + [str(a) for a in db.get_anios_disponibles()]
        anio_filtro = c3.selectbox("Año", anios_filtro)

        if st.button("Buscar"):
            resultados = db.buscar_partes(
                anio=int(anio_filtro) if anio_filtro != "(todos)" else None,
                texto=texto.strip(),
                companero="" if companero_filtro == "(todos)" else companero_filtro,
                cliente="" if cliente_filtro == "(todos)" else cliente_filtro,
            )
            st.session_state["resultados_busqueda"] = resultados

        resultados = st.session_state.get("resultados_busqueda", [])
        if resultados:
            st.success(f"{len(resultados)} resultado(s) encontrado(s).")
            for parte in resultados:
                _tarjeta_parte(parte, key_prefix="busqueda")
