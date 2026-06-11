import streamlit as st

st.set_page_config(layout="wide", page_title="TFG Manchas Solares", page_icon="🌞")

st.title("🌞 Estudio de la dinámica de los gases ionizados en la fotosfera solar")
st.markdown("**Lydia Tomás Sanz** · Grado en Física (UAX)")
st.markdown("*La rotación diferencial del Sol, medida con un telescopio amateur y un móvil.*")

st.markdown(
    "¿Gira el Sol como una bola rígida, o cada latitud lleva su propio ritmo? Este "
    "trabajo lo responde siguiendo **manchas solares** en fotografías propias y "
    "midiendo cómo cambia su velocidad de giro con la latitud. Toda la herramienta "
    "—cálculo, base de datos y simuladores— está reunida aquí. Elige un apartado en "
    "el menú 👈"
)

st.markdown(
    "- 🖥️ **Gestor de manchas** — la base de datos del trabajo: observaciones, "
    "mediciones, resultados, animación, errores, galería y el resultado final. "
    "Puedes consultar los datos de Lydia (solo lectura) o medir los tuyos en una base nueva.\n"
    "- 🌀 **Simulador 3D** — esfera celeste interactiva para entender y calcular el "
    "ángulo μ (además de otros valores como Bπ, hora sidérea, el azimut y la altura del Sol y de π),"
    "con el polo de la eclíptica π, el ecuador celeste y la eclíptica en tiempo real.\n"
    "- 🧭 **Ejes y meridianos** — superpone el ecuador y los meridianos heliográficos "
    "sobre una foto del Sol (de la base de datos o propia).\n"
    "- 🧮 **Calculadora astronómica** — conversiones entre coordenadas (horizontales, "
    "ecuatoriales y eclípticas), el ángulo µ del Sol y la distancia entre manchas."
)

st.info("💡 Si mides tus propios datos, tu ajuste y tu gráfica final aparecen en la "
        "pestaña «Resultado final».")

st.markdown("**Resultado principal:** A = +14,10 ± 0,28 °/día, B = −2,21 ± 2,47 °/día "
            "→ **coherente con la rotación diferencial** del Sol (B<0: el ecuador gira algo "
            "más rápido que los polos). El error de B es grande, por lo que el resultado la "
            "apoya sin ser concluyente.")
