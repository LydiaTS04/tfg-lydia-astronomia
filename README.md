# TFG — Estudio de la dinámica de los gases ionizados en la fotosfera solar

Repositorio del Trabajo de Fin de Grado de **Lydia Tomás Sanz** (Grado en Física, UAX).

Corroboración de la **rotación diferencial del Sol** a partir del seguimiento de
manchas solares fotografiadas con un telescopio reflector (Newton) y un móvil.

## Contenido

- **`codigo/`** — código de cálculo: transformación (píxel → coordenadas
  heliográficas), ángulo µ, corrección óptica β_opt y ajuste ω(Φ) = A + B·sin²Φ.
- **`gestor_web.py`** — gestor web (Streamlit) para introducir y analizar las manchas.
- **`sim_solar.py`** — simulación/animación de la rotación de las manchas.
- **`simulador_muu_v3_standalone.html`** — simulador 3D de la esfera celeste
  (µ, π, eclíptica, ecuador celeste).
- **`galeria.py`, `video_alineado.py`, `alinear_video_manchas.py`** — galería de
  fotos y vídeo del movimiento de las manchas.
- **`fig_*.py`, `dibujo_*.py`, `fig24_*.py`** — scripts que generan las figuras del TFG.
- **`manchas_tfg.db`** — base de datos (SQLite) con las medidas reales de las manchas
  (abril 2026 + agosto 2024 de José Luis).

## Resultado principal

Ajustando ω(Φ) = A + B·sin²Φ a las 27 manchas seguidas:

> **A = +14,10 ± 0,28 °/día,  B = −2,21 ± 2,47 °/día**  (χ²_ν ≈ 0,94)

El coeficiente **B < 0** confirma la rotación diferencial: el ecuador gira más
rápido que los polos.

## Requisitos

Python 3 con: `streamlit`, `numpy`, `opencv-python`, `matplotlib`, `imageio-ffmpeg`, `pandas`.

```bash
pip install streamlit numpy opencv-python matplotlib imageio-ffmpeg pandas
streamlit run gestor_web.py
```

---
Autora: Lydia Tomás Sanz · TFG, Grado en Física (UAX).
