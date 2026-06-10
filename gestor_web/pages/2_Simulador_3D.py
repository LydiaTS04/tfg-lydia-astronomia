import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Simulador 3D", page_icon="\U0001F300")

st.title("\U0001F300 Simulador 3D del ángulo µ")
st.caption("Ecuador celeste, eclíptica, polo de la eclíptica π, punto Aries γ y el ángulo µ.")

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HTML = os.path.join(_ROOT, "simulador_3d", "simulador_muu_v3_standalone.html")

if os.path.exists(_HTML):
    components.html(open(_HTML, encoding="utf-8").read(), height=920, scrolling=True)
else:
    st.error("No encuentro el simulador en simulador_3d/.")
