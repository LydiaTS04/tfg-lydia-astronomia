# 🌞 TFG — Estudio de la dinámica de los gases ionizados en la fotosfera solar

Repositorio del Trabajo de Fin de Grado de **Lydia Tomás Sanz** (Grado en Física, UAX).

El trabajo corrobora la **rotación diferencial del Sol** mediante el seguimiento de
manchas solares fotografiadas con un telescopio reflector (Newton) y un teléfono
móvil, midiendo cómo varía la velocidad angular con la latitud heliográfica.

```
tfg-lydia-astronomia/
├── simulador_3d/     Simulador 3D de la esfera celeste (µ, π, eclíptica)
├── gestor_web/       Aplicación + base de datos (datos, ajuste, animación, resultado)
├── codigo_calculo/   Código de cálculo (píxel → coordenadas heliográficas, ajuste)
└── figuras/          Generación de figuras (ejes/meridianos y gráfica de Faye)
```

---

## Cómo acceder

**Opción 1 — Aplicación en línea (recomendada).** No requiere instalar nada; se
abre en el navegador:

> **https://tfg-lydia-astronomia-gdan89vjq3jvfdgtdy8bez.streamlit.app/**

En el menú lateral se elige el apartado: **Inicio**, **Gestor de manchas** o
**Simulador 3D**.

**Opción 2 — Ejecutar en local.** Requiere Python 3:

```bash
pip install -r requirements.txt
cd gestor_web
streamlit run Inicio.py
```

El simulador 3D también puede abrirse por separado haciendo doble clic en
`simulador_3d/simulador_muu_v3_standalone.html`.

---

## 1. Simulador 3D — `simulador_3d/`

Simulador interactivo de la esfera celeste. Muestra el ecuador celeste, la
eclíptica, el polo de la eclíptica π, el punto Aries γ y el ángulo µ (entre el
meridiano cenit–Sol y el arco ⊙π). No necesita instalación.

## 2. Aplicación y base de datos — `gestor_web/`

Aplicación principal (Streamlit) para introducir, calcular y visualizar las
manchas. La base de datos con las medidas tomadas por la autora se encuentra en
`gestor_web/manchas_tfg.db`.

En la barra lateral se ofrecen **dos modos**:

- **Ver los datos de Lydia (solo lectura).** Permite explorar las observaciones,
  los resultados y las gráficas. Los datos no se pueden modificar (las tablas
  están bloqueadas y se trabaja sobre una copia temporal).
- **Medir mis propios datos.** Parte de una base de datos vacía con la misma
  estructura, donde el usuario introduce sus propias observaciones y manchas y
  obtiene su ajuste ω(Φ) = A + B·sin²Φ con su gráfica.

La aplicación se organiza en pestañas:

| Pestaña | Contenido |
|---|---|
| Observaciones (Fotos) | cada fotografía con su fecha, centro, radio, λ☉ y β |
| Mediciones (Manchas) | cada mancha medida y sus coordenadas heliográficas |
| Resultados Calculados | velocidad ω y periodo de cada mancha, y el ajuste ω(Φ) |
| Animación Solar | animación de la rotación de las manchas (con el vídeo de abril) |
| Errores (±σ) | propagación de incertidumbres |
| Fotos (galería) | fotografías con ejes, limpias y las de agosto de 2024 |
| Resultado final | gráfica interactiva (ω y periodo frente a la latitud) y comparación con Carrington y Faye |

## 3. Código de cálculo — `codigo_calculo/`

- **`calculo_principal.py`** — núcleo del trabajo: transformación píxel →
  coordenadas heliográficas (ángulo µ, corrección óptica β_opt, proyección
  ortográfica inversa y triángulo del polo solar) y ajuste de la rotación
  diferencial. Su «modo i» abre directamente la aplicación.
- **`calcular_fit_sin_22manana.py`** — cálculo de los coeficientes A y B.
- **`gen_tablas.py`** — generación de las tablas en LaTeX a partir de la base de datos.
- **`video_alineado.py`, `alinear_video_manchas.py`** — preparación del vídeo de
  las manchas alineadas que se muestra en la pestaña «Animación».

## 4. Figuras — `figuras/`

- **`dibujar_ejes_TODAS_limpias.py`, `dibujar_cuadricula_curva.py`,
  `dibujar_cuadricula_limpia.py`** — dibujan los ejes y meridianos heliográficos
  sobre las fotografías del Sol, a partir de los datos de cada observación.
- **`rotacion_solar.html` / `rotacion_solar.png`** — gráfica de Faye–Carrington:
  velocidad angular ω y periodo frente a la latitud heliográfica Φ.

---

## Resultado principal

Ajustando ω(Φ) = A + B·sin²Φ a las 27 manchas seguidas:

> **A = +14,10 ± 0,28 °/día,  B = −2,21 ± 2,47 °/día**  (χ²_ν ≈ 0,94)

El coeficiente **B < 0** confirma la rotación diferencial: el ecuador gira más
rápido que los polos, lo que descarta el giro rígido. El periodo ecuatorial
resulta de unos **25 días sidéreos**, en buen acuerdo con los valores clásicos de
Carrington y Faye.

---

## Requisitos

La aplicación necesita: `streamlit`, `pandas`, `numpy`, `plotly` (ver
`requirements.txt`). Los scripts de figuras y vídeo requieren además
`opencv-python`, `matplotlib` e `imageio-ffmpeg`.

---
Autora: **Lydia Tomás Sanz** · Trabajo de Fin de Grado, Grado en Física (UAX).
