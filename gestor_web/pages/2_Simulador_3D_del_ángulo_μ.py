import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Simulador 3D", page_icon="\U0001F300")

st.title("\U0001F300 Simulador 3D del ángulo µ")
st.caption("Ecuador celeste, eclíptica, polo de la eclíptica π, punto Aries γ y el ángulo µ.")

_URL = "https://lydiats04.github.io/Simulador-3D/"
components.iframe(_URL, height=920, scrolling=True)
st.caption("¿No se ve bien aquí? Ábrelo a pantalla completa: " + _URL)
