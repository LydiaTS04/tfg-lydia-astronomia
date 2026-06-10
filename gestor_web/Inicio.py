import streamlit as st

st.set_page_config(layout="wide", page_title="TFG Manchas Solares", page_icon="\U0001F31E")

st.title("\U0001F31E TFG — Estudio de la rotación del Sol")
st.subheader("Lydia Tomás Sanz · Grado en Física (UAX)")

st.markdown(
    """
Esta aplicación reúne todo el trabajo en **apartados** (menú de la izquierda \U0001F448):

- \U0001F5A5️ **Gestor de manchas** — la base de datos con las medidas del trabajo:
  observaciones, mediciones, resultados, animación, errores, galería y el
  resultado final. Se puede **ver los datos de Lydia** (solo lectura) o
  **medir datos propios** en una base nueva.
- \U0001F9ED **Ejes y meridianos** — dibuja el ecuador y los meridianos heliográficos
  sobre una foto del Sol (una de la base de datos o una propia).
- \U0001F9EE **Calculadora astronómica** — conversiones de coordenadas (horizontales,
  ecuatoriales y eclípticas), el ángulo µ del Sol y la distancia entre manchas.
- \U0001F300 **Simulador 3D del ángulo µ (signo)** — la esfera celeste interactiva:
  calcula µ con su signo, y muestra π, γ, el ecuador celeste y la eclíptica.
"""
)

st.info(
    "Resultado principal:  A = +14,10 ± 0,28 °/día,  B = −2,21 ± 2,47 °/día "
    "→ el ecuador gira más rápido que los polos (rotación diferencial)."
)

st.caption("Elige un apartado en el menú de la izquierda para empezar.")
