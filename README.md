# 🌞 TFG — Estudio de la dinámica de los gases ionizados en la fotosfera solar

Trabajo de Fin de Grado de **Lydia Tomás Sanz** · Grado en Física (UAX).

Corroboración de la **rotación diferencial del Sol** siguiendo manchas solares
fotografiadas con un telescopio reflector (Newton) y un móvil, y midiendo cómo
cambia su velocidad de rotación con la latitud.

```
tfg-lydia-astronomia/
├── simulador_3d/     🌀  Simulador 3D de la esfera celeste (µ, π, eclíptica)
├── gestor_web/       🖥️  App + base de datos (pestañas: datos, ajuste, animación, fotos)
├── codigo_calculo/   🧮  Código de cálculo (píxel → coordenadas heliográficas, ajuste)
└── figuras/          📊  Scripts que generan las figuras del TFG
```

---

## 🌀 1. Simulador 3D — `simulador_3d/`

Simulador interactivo de la **esfera celeste**: muestra el ecuador celeste, la
eclíptica, el polo de la eclíptica **π**, el punto Aries **γ** y el ángulo **µ**
(entre el meridiano cenit–Sol y el arco ⊙π).

▶️ **Para verlo:** abre `simulador_3d/simulador_muu_v3_standalone.html` en
cualquier navegador (doble clic). No necesita instalar nada.

---

## 🖥️ 2. Gestor web + base de datos — `gestor_web/`

La aplicación principal (Streamlit) para introducir, calcular y visualizar las
manchas. La base de datos con **mis medidas reales** está aquí mismo:
`gestor_web/manchas_tfg.db`.

▶️ **Para arrancarlo:**
```bash
cd gestor_web
streamlit run gestor_web.py
```

Tiene **6 pestañas**:

| Pestaña | Qué muestra |
|---|---|
| **Tabla: Observaciones (Fotos)** | cada foto con su fecha, centro, radio, λ☉, β… |
| **Tabla: Mediciones (Manchas)** | cada mancha medida y sus coordenadas heliográficas |
| **Resultados Calculados** | velocidad ω y periodo de cada mancha, y el ajuste ω(Φ)=A+B·sin²Φ |
| **Animación Solar** | animación de la rotación de las manchas (+ vídeo real de abril) |
| **Errores (±σ)** | propagación de incertidumbres |
| **Fotos (galería)** | galería de fotos: con ejes, limpias y las de agosto 2024 |

> Las fotos y el vídeo se leen de la carpeta del proyecto; en el repositorio no
> se incluyen por su tamaño, así que esas dos pestañas saldrán vacías si lo
> ejecutas fuera de mi ordenador.

---

## 🧮 3. Código de cálculo — `codigo_calculo/`

El núcleo de la transformación **píxel → coordenadas heliográficas**: el ángulo
µ, la corrección óptica β_opt, la proyección ortográfica inversa, el triángulo
del polo solar y el ajuste de la rotación diferencial.

---

## 📊 4. Figuras — `figuras/`

Scripts de Python que generan las figuras del TFG (B₀ a lo largo del año, los
pasos de µ, el dínamo, la rotación diferencial, las cuadrículas heliográficas…).

---

## 🎯 Resultado principal

Ajustando ω(Φ) = A + B·sin²Φ a las 27 manchas seguidas:

> **A = +14,10 ± 0,28 °/día,  B = −2,21 ± 2,47 °/día**  (χ²_ν ≈ 0,94)

El coeficiente **B < 0** confirma la rotación diferencial: el ecuador gira más
rápido que los polos, descartando el giro rígido. El periodo ecuatorial sale
en ~25 días sidéreos, casi igual que el valor clásico de Faye.

---

## ⚙️ Requisitos

```bash
pip install streamlit numpy opencv-python matplotlib imageio-ffmpeg pandas
```

---

Autora: **Lydia Tomás Sanz** · TFG, Grado en Física (UAX).
