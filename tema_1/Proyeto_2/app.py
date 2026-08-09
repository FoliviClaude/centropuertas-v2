"""Interfaz Streamlit para Snap (acortador de URLs)."""
import streamlit as st

from src.database import init_db
from src.snap import get_all_urls, resolve_short_code, shorten_url

init_db()

st.set_page_config(page_title="Snap", page_icon="✂️")

codigo_visitado = st.query_params.get("code")

if codigo_visitado:
    try:
        url_destino = resolve_short_code(codigo_visitado)
        st.markdown(
            f'<meta http-equiv="refresh" content="0; url={url_destino}">',
            unsafe_allow_html=True,
        )
        st.info(f"🔀 Redirigiendo a {url_destino}...")
        st.markdown(f"[Haz clic aquí si no eres redirigido]({url_destino})")
    except ValueError as exc:
        st.error(f"⚠️ {exc}")
    st.stop()

st.title("✂️ Snap")

if "short_code" not in st.session_state:
    st.session_state.short_code = None
if "error" not in st.session_state:
    st.session_state.error = None

url_larga = st.text_input("URL larga", placeholder="https://ejemplo.com/pagina-muy-larga")

if st.button("🔗 Acortar", use_container_width=True):
    try:
        st.session_state.short_code = shorten_url(url_larga)
        st.session_state.error = None
    except ValueError as exc:
        st.session_state.short_code = None
        st.session_state.error = str(exc)

st.divider()

if st.session_state.error:
    st.error(f"⚠️ {st.session_state.error}")
elif st.session_state.short_code:
    st.success(f"✅ Código generado: {st.session_state.short_code}")
    st.code(f"?code={st.session_state.short_code}")
else:
    st.info("Introduce una URL y pulsa Acortar.")

st.divider()
st.subheader("📋 URLs creadas")

urls = get_all_urls()
if urls:
    st.table(
        [
            {"Código": fila["short_code"], "URL": fila["long_url"], "Creado": fila["created_at"]}
            for fila in urls
        ]
    )
else:
    st.info("Todavía no hay URLs acortadas.")
