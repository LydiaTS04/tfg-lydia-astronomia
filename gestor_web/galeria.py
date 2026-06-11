# -*- coding: utf-8 -*-
"""
Galeria de fotos para el gestor (pestana "Fotos").
Tres secciones EN ORDEN CRONOLOGICO: con ejes (abril), sin ejes/limpias (abril),
y Jose Luis (agosto 2024).

NOTA: las fotos ya estan guardadas giradas 180 grados respecto a la original
(para que coincidan con la realidad). Se muestran TAL CUAL, sin girar nada.

Se importa:  import galeria; galeria.render_galeria(BASE_DIR)
"""
import os, glob, re

MESES = {1:'ene',2:'feb',3:'mar',4:'abr',5:'may',6:'jun',
         7:'jul',8:'ago',9:'sep',10:'oct',11:'nov',12:'dic'}


def _parse_abril(fn):
    """Devuelve (dia, mes, anio, hh, mm) desde el nombre, o None."""
    b = os.path.splitext(os.path.basename(fn))[0]
    b = re.sub(r'^limpia\s+', '', b)
    b = re.sub(r'^nºmanchas_', '', b)
    b = re.sub(r'_EJES$', '', b)
    b = re.sub(r'\s*-\s*copia$', '', b)
    m = re.search(r'([a-zA-Z]+)_(\d{1,2})-(\d{1,2})-(\d{2})[_-](\d{1,2})[_-](\d{2})', b)
    if m:
        return (m.group(1), int(m.group(2)), int(m.group(3)),
                2000 + int(m.group(4)), int(m.group(5)), int(m.group(6)))
    return None


def _label_abril(fn):
    p = _parse_abril(fn)
    if p:
        dia = p[0].lower(); dia = dia[0].upper() + dia[1:]
        return "%s %d %s · %02d:%02d" % (dia, p[1], MESES.get(p[2], '?'), p[4], p[5])
    return os.path.splitext(os.path.basename(fn))[0]


def _key_abril(fn):
    p = _parse_abril(fn)
    if p:
        return (p[3], p[2], p[1], p[4], p[5])   # anio, mes, dia, hh, mm
    return (9999, 99, 99, 99, 99)


def _parse_jl(fn):
    b = os.path.splitext(os.path.basename(fn))[0]
    m = re.search(r'S(\d+)_(\d{2})(\d{2})(\d{2})', b)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), 2000 + int(m.group(4)))
    return None


def _label_jl(fn):
    p = _parse_jl(fn)
    if p:
        return "%d %s %d  (S%d)" % (p[1], MESES.get(p[2], '?'), p[3], p[0])
    return os.path.splitext(os.path.basename(fn))[0]


def _key_jl(fn):
    p = _parse_jl(fn)
    if p:
        return (p[3], p[2], p[1])   # anio, mes, dia
    return (9999, 99, 99)


def _grid(st, archivos, label_fn, cols=3):
    if not archivos:
        st.info("No se encontraron fotos en esta carpeta.")
        return
    for i in range(0, len(archivos), cols):
        fila = archivos[i:i+cols]
        columnas = st.columns(cols)
        for col, fn in zip(columnas, fila):
            with col:
                try:
                    st.image(fn, caption=label_fn(fn), use_container_width=True)
                except Exception as e:
                    st.warning("No se pudo abrir %s (%s)" % (os.path.basename(fn), e))


def _seccion(st, archivos, label_fn, key):
    _grid(st, archivos, label_fn)
    if archivos:
        with st.expander("🔍 Ampliar una foto"):
            labels = [label_fn(f) for f in archivos]
            idx = st.selectbox("Elige la foto a ampliar", range(len(archivos)),
                               format_func=lambda i: labels[i], key='big_' + key)
            try:
                st.image(archivos[idx], caption=labels[idx], use_container_width=True)
            except Exception as e:
                st.warning(str(e))
        st.caption("Pasa el ratón por una foto y pulsa el icono ⤢ (esquina) para verla a pantalla completa.")


def render_galeria(base_dir):
    import streamlit as st
    st.header("Fotos del Sol")
    st.info(
        "ℹ️ Las fotos se muestran **tal cual están guardadas: ya giradas 180°** "
        "respecto a la original, para que **coincidan con la realidad** "
        "(el telescopio invierte la imagen).")

    dir_ejes  = os.path.join(base_dir, 'fotos abril 2026', 'fotos_con_ejes_TODAS', 'CON_EJES_CURVOS')
    dir_limp  = os.path.join(base_dir, 'fotos abril 2026', 'fotos_con_nmanchas')
    dir_jl    = os.path.join(base_dir, 'joseluis_agosto_2024_ fotos del sol')

    ejes = glob.glob(os.path.join(dir_ejes, '*_EJES.png'))
    ejes.sort(key=_key_abril)

    limpias = glob.glob(os.path.join(dir_limp, '*.png'))
    limpias.sort(key=_key_abril)

    jl = [f for f in glob.glob(os.path.join(dir_jl, '*'))
          if f.lower().endswith(('.jpg', '.jpeg', '.png')) and 'jupiter' not in f.lower()]
    jl.sort(key=_key_jl)

    # ORDEN: primero las mias (abril), luego las de Jose Luis (agosto)
    t_ejes, t_limp, t_jl = st.tabs([
        "🟢 Con ejes (abril 2026) — %d" % len(ejes),
        "🌞 Con nº de manchas (abril 2026) — %d" % len(limpias),
        "🔭 José Luis (agosto 2024) — %d" % len(jl),
    ])
    with t_ejes:
        st.caption("Fotografías de abril 2026 con el eje N-S, el ecuador y los paralelos "
                   "dibujados (cuadrícula heliográfica curva). En orden por fecha.")
        _seccion(st, ejes, _label_abril, 'ej')
    with t_limp:
        st.caption("Fotografías de abril 2026 con las manchas numeradas. En orden por fecha.")
        _seccion(st, limpias, _label_abril, 'li')
    with t_jl:
        st.caption("Fotos cedidas por José Luis (agosto 2024), en orden por fecha. "
                   "La foto de Júpiter no se incluye.")
        _seccion(st, jl, _label_jl, 'jl')
