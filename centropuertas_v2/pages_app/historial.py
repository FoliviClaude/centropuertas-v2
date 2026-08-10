"""
pages_app/historial.py
========================
Page "🔎 Historial & PDF" : vue mensuelle (cartes + export PDF) et
recherche/filtres dans tout l'historique (client, collègue, mot-clé).

Confidentialité : TOUTES les lectures ci-dessous (vue mensuelle,
buscador, base de conocimientos) sont filtrées par le technicien
actuellement connecté (`auth.nombre_tecnico_actual()`) -- chacun ne
voit jamais que ses propres partes, jamais ceux d'un collègue.
"""

from __future__ import annotations

import datetime as dt

import streamlit as st
from libsql_client import Row

import auth
import database as db
from locales import t, t_dia_semana, t_mes, t_tipo_jornada
from pages_app._campos_parte import campos_parte
from utils.calculos import resumen_de_partes
from utils.excel_export import generar_excel_mensual
from utils.pdf_export import generar_pdf_mensual
from utils.styling import encabezado_pagina


@st.dialog(" ", width="large")
def _dialogo_editar(parte: Row, technician_name: str) -> None:
    fecha = dt.date.fromisoformat(parte["fecha"])
    st.markdown(f"### {t('common.editar')} — {fecha.strftime('%d/%m/%Y')}")

    valores = campos_parte(parte, key_prefix=f"edit_{parte['id']}")

    c1, c2 = st.columns(2)
    if c1.button(t("common.guardar"), type="primary", width="stretch"):
        db.guardar_parte(fecha=parte["fecha"], technician_name=technician_name, **valores)
        st.success(t("nuevo_parte.guardado_ok", fecha=fecha.strftime("%d/%m/%Y")), icon="✅")
        st.rerun()
    if c2.button(t("common.cancelar"), width="stretch"):
        st.rerun()


def _tarjeta_parte(parte: Row, key_prefix: str, technician_name: str) -> None:
    """
    Affiche un parte sous forme de carte. `key_prefix` distingue les
    clés des boutons selon l'onglet (Streamlit garde en mémoire le
    contenu de tous les onglets à la fois, même ceux non visibles ;
    sans préfixe différent, un même parte affiché dans 2 onglets ferait
    planter l'app avec une erreur de clé dupliquée).

    `technician_name` est toujours celui de la session en cours (pas
    `parte["technician_name"]`) : c'est ce qui alimente les contrôles
    de propriété côté base de données (voir database.eliminar_parte /
    guardar_parte) au moment d'éditer ou de supprimer.
    """
    fecha = dt.date.fromisoformat(parte["fecha"])
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            dia_semana = t_dia_semana(fecha.weekday())
            st.markdown(f"**📅 {dia_semana} {fecha.strftime('%d/%m/%Y')}** · {t_tipo_jornada(parte['tipo_jornada'])}")
            if parte["cliente_nombre"]:
                linea = f"🏢 **{parte['cliente_nombre']}**"
                if parte["intervencion_nombre"]:
                    linea += f" — {parte['intervencion_nombre']}"
                st.markdown(linea)
            if parte["descripcion"]:
                st.markdown(f"🔧 {parte['descripcion']}")
            if parte["observaciones"]:
                st.markdown(f"⚠️ *{parte['observaciones']}*")
            if parte["collegue_nombre"]:
                st.caption(f"{t('nuevo_parte.colega')}: {parte['collegue_nombre']}")
        with c2:
            st.metric(t("historial.horas"), f'{parte["horas_normales"]:g}')
            if parte["horas_extra"]:
                st.caption(t("historial.h_extra_card", h=parte["horas_extra"]))
            if parte["dietas"]:
                st.caption(t("historial.dietas_card", n=parte["dietas"]))
            if st.button(t("common.editar"), key=f"edit_{key_prefix}_{parte['id']}", width="stretch"):
                _dialogo_editar(parte, technician_name)
            if st.button(t("common.eliminar"), key=f"del_{key_prefix}_{parte['id']}", width="stretch"):
                db.eliminar_parte(parte["id"], technician_name)
                st.rerun()


def render() -> None:
    encabezado_pagina(t("historial.titulo"), t("historial.subtitulo"), icono="history")

    technician_name = auth.nombre_tecnico_actual()

    tab_mes, tab_buscador, tab_conocimiento = st.tabs([
        t("historial.tab_mes"), t("historial.tab_buscador"), t("historial.tab_conocimiento"),
    ])

    # ------------------------------------------------------------------
    with tab_mes:
        hoy = dt.date.today()
        anios_disponibles = sorted(set(db.get_anios_disponibles(technician_name) + [hoy.year]), reverse=True)

        col_anio, col_mes = st.columns(2)
        anio = col_anio.selectbox(
            t("historial.filtro_anio"), anios_disponibles,
            index=anios_disponibles.index(hoy.year) if hoy.year in anios_disponibles else 0,
        )
        mes = col_mes.selectbox(
            t("historial.mes"), options=list(range(1, 13)),
            index=hoy.month - 1, format_func=t_mes,
        )

        partes_mes = db.get_partes_mes(anio, mes, technician_name)

        if not partes_mes:
            st.info(t("historial.sin_partes_mes"), icon="🗓️")
        else:
            resumen = resumen_de_partes(partes_mes)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(t("dashboard.horas_trabajadas"), f'{resumen["horas_normales"]:g} h')
            k2.metric(t("dashboard.horas_extra"), f'{resumen["horas_extra"]:g} h')
            k3.metric(t("dashboard.dietas"), f'{resumen["dietas"]:g}')
            k4.metric(
                f'{t("tipo.Vacaciones")} / {t("tipo.Baja")} / {t("tipo.Guardia")}',
                f'{resumen["dias_vacaciones"]} / {resumen["dias_baja"]} / {resumen["dias_guardia"]}',
            )

            config = db.get_configuracion()
            col_pdf, col_excel = st.columns(2)
            with col_pdf:
                pdf_bytes = generar_pdf_mensual(
                    anio, mes, config["nombre_trabajador"], partes_mes,
                    empresa=config["empresa"], nif_cif=config["nif_cif"],
                )
                st.download_button(
                    t("historial.generar_informe"), data=pdf_bytes,
                    file_name=f"parte_{t_mes(mes).lower()}_{anio}.pdf",
                    mime="application/pdf", type="primary", width="stretch",
                )
            with col_excel:
                excel_bytes = generar_excel_mensual(partes_mes)
                st.download_button(
                    t("historial.exportar_excel"), data=excel_bytes,
                    file_name=f"parte_{t_mes(mes).lower()}_{anio}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )

            st.divider()
            for parte in partes_mes:
                _tarjeta_parte(parte, key_prefix="mes", technician_name=technician_name)

    # ------------------------------------------------------------------
    with tab_buscador:
        texto = st.text_input(t("historial.palabra_clave"))
        c1, c2, c3 = st.columns(3)

        clientes = db.get_clients()
        etiquetas_clientes = [t("common.todos")] + [c["nombre"] for c in clientes]
        ids_clientes = [None] + [c["id"] for c in clientes]
        cliente_sel = c1.selectbox(t("historial.filtro_cliente"), etiquetas_clientes)

        colegas = db.get_collegues()
        etiquetas_colegas = [t("common.todos")] + [c["nombre"] for c in colegas]
        ids_colegas = [None] + [c["id"] for c in colegas]
        colega_sel = c2.selectbox(t("historial.filtro_colega"), etiquetas_colegas)

        anios_filtro = [t("common.todos")] + [str(a) for a in db.get_anios_disponibles(technician_name)]
        anio_filtro = c3.selectbox(t("historial.filtro_anio"), anios_filtro)

        if st.button(t("common.buscar")):
            resultados = db.buscar_partes(
                technician_name=technician_name,
                anio=int(anio_filtro) if anio_filtro != t("common.todos") else None,
                texto=texto.strip(),
                id_client=ids_clientes[etiquetas_clientes.index(cliente_sel)],
                id_collegue=ids_colegas[etiquetas_colegas.index(colega_sel)],
            )
            st.session_state["resultados_busqueda"] = resultados

        resultados = st.session_state.get("resultados_busqueda", [])
        if resultados:
            st.success(t("historial.resultados_encontrados", n=len(resultados)))
            for parte in resultados:
                _tarjeta_parte(parte, key_prefix="busqueda", technician_name=technician_name)

    # ------------------------------------------------------------------
    # Base de Conocimientos : recherche libre sur TOUT l'historique DU
    # TECHNICIEN CONNECTÉ (toutes années confondues), par mot-clé et/ou
    # type d'intervention -- pensé pour retrouver comment un problème
    # récurrent (ex. cables cruzados en sensores GEZE) qu'IL a déjà
    # rencontré a été résolu par le passé. Comme le reste de cette page,
    # elle ne montre jamais l'historique d'un autre technicien.
    # ------------------------------------------------------------------
    with tab_conocimiento:
        st.caption(t("historial.conocimiento_subtitulo"))

        texto_kb = st.text_input(t("historial.palabra_clave"), key="kb_texto")

        tipos_kb = db.get_interventions_types()
        etiquetas_tipos_kb = [t("common.todos")] + [ti["nombre"] for ti in tipos_kb]
        ids_tipos_kb = [None] + [ti["id"] for ti in tipos_kb]
        tipo_sel_kb = st.selectbox(t("historial.filtro_intervencion"), etiquetas_tipos_kb, key="kb_tipo")

        if st.button(t("common.buscar"), key="kb_buscar"):
            st.session_state["resultados_conocimiento"] = db.buscar_partes(
                technician_name=technician_name,
                texto=texto_kb.strip(),
                id_intervention=ids_tipos_kb[etiquetas_tipos_kb.index(tipo_sel_kb)],
            )

        resultados_kb = st.session_state.get("resultados_conocimiento", [])
        if resultados_kb:
            st.success(t("historial.resultados_encontrados", n=len(resultados_kb)))
            for parte in resultados_kb:
                _tarjeta_parte(parte, key_prefix="conocimiento", technician_name=technician_name)
        elif "resultados_conocimiento" not in st.session_state:
            st.info(t("historial.sin_resultados_conocimiento"), icon="🧠")
