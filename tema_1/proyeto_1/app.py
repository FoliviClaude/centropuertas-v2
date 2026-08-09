"""Interfaz Streamlit para la calculadora."""
import streamlit as st

from src.calculator import add, subtract, multiply, divide

st.set_page_config(page_title="Calculadora", page_icon="🧮")
st.title("🧮 Calculadora")

col1, col2 = st.columns(2)
with col1:
    a = st.number_input("Valor A", value=0.0, format="%f")
with col2:
    b = st.number_input("Valor B", value=0.0, format="%f")

if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "error" not in st.session_state:
    st.session_state.error = None

col_sum, col_res, col_mul, col_div = st.columns(4)

if col_sum.button("➕ Sumar", use_container_width=True):
    st.session_state.resultado = add(a, b)
    st.session_state.error = None

if col_res.button("➖ Restar", use_container_width=True):
    st.session_state.resultado = subtract(a, b)
    st.session_state.error = None

if col_mul.button("✖️ Multiplicar", use_container_width=True):
    st.session_state.resultado = multiply(a, b)
    st.session_state.error = None

if col_div.button("➗ Dividir", use_container_width=True):
    try:
        st.session_state.resultado = divide(a, b)
        st.session_state.error = None
    except ValueError as exc:
        st.session_state.resultado = None
        st.session_state.error = str(exc)

st.divider()

if st.session_state.error:
    st.error(f"⚠️ {st.session_state.error}")
elif st.session_state.resultado is not None:
    st.markdown(
        f"<h1 style='text-align: center;'>{st.session_state.resultado}</h1>",
        unsafe_allow_html=True,
    )
else:
    st.info("Introduce dos valores y pulsa una operación.")
