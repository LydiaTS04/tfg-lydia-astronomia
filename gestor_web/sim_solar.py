# -*- coding: utf-8 -*-
"""
Simulacion 3D INTERACTIVA de la rotacion solar (pestana "Animacion" del gestor).

- Es una BOLA (esfera) que puedes girar con el raton.
- Al principio: solo las manchas, SIN rastro.
- Le das a PLAY -> se forma el rastro y se anima la rotacion.
- Al terminar la vuelta se PARA con el rastro marcado; puedes girar la esfera
  para verlo a tu gusto.
- Si vuelves a dar a PLAY, empieza de nuevo (rastro desde cero).
- Las manchas giran en el sentido fisico real (verificado con los datos).

import sim_solar; sim_solar.render_animacion(RUTA_BD)
"""
import os, math, sqlite3
import numpy as np
import pandas as pd

PHI_ZERO     = math.radians(82.0 + 44.0/60.0 + 53.56/3600.0)
LAMBDA_NORTH = math.radians(-13.0 - 52.0/60.0 - 21.41/3600.0)
LN_DEG       = math.degrees(LAMBDA_NORTH)

def omega_syn(phi_deg):
    pr = math.radians(abs(float(phi_deg)))
    return 14.370 - 0.9856 - 2.300 * math.sin(pr) ** 2   # grados/dia (sinodico)

# paleta de colores MUY distintos (Material, brillantes sobre fondo oscuro)
COLORES = ['#FF1744', '#00E676', '#2979FF', '#FFEA00', '#D500F9',
           '#00E5FF', '#FF9100', '#FFFFFF', '#76FF03', '#FF4081',
           '#1DE9B6', '#FFC400', '#651FFF', '#F50057', '#C6FF00',
           '#18FFFF', '#FF3D00', '#E040FB', '#00B0FF', '#AEEA00',
           '#FF6E40', '#B388FF', '#64FFDA', '#EEFF41']


def _pos3(phi_deg, cmd_deg, r=1.0):
    """Posicion 3D en la esfera. Y=norte solar, Z=hacia el observador (frente>0)."""
    pr = math.radians(phi_deg); cr = math.radians(cmd_deg)
    return (r*math.cos(pr)*math.sin(cr), r*math.sin(pr), r*math.cos(pr)*math.cos(cr))


def render_animacion(ruta_bd, video_path=None, excluir_fechas=('22-04-2026 10:19',)):
    import streamlit as st
    try:
        import plotly.graph_objects as go
    except Exception:
        st.error("Instala plotly:  pip install plotly"); return

    if video_path is None:
        base = os.path.dirname(os.path.abspath(ruta_bd))
        video_path = os.path.join(base, 'fotos abril 2026', 'fotos_con_ejes_TODAS',
                                  'CON_EJES_CURVOS', 'video', 'video_manchas.mp4')

    st.header("Animacion: Rotacion Solar")

    con = sqlite3.connect(ruta_bd)
    df = pd.read_sql_query("""
        SELECT m.id_grupo, m.latitud_phi, m.longitud_L, o.lambda_sol, o.fecha_hora
        FROM Mediciones m JOIN Observaciones o ON m.id_observacion=o.id_observacion
        WHERE m.excluida=0 ORDER BY o.fecha_hora, m.id_grupo
    """, con); con.close()
    if excluir_fechas:
        df = df[~df['fecha_hora'].isin(list(excluir_fechas))]
    if df.empty:
        st.info("No hay datos de manchas."); return

    FMTS = ['%d-%m-%Y %H:%M', '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%d-%m-%Y']
    def pdt(s):
        for f in FMTS:
            try: return pd.to_datetime(s, format=f)
            except Exception: pass
        return pd.NaT
    df['dt'] = df['fecha_hora'].apply(pdt)
    df = df.dropna(subset=['dt']).reset_index(drop=True)
    if df.empty:
        st.warning("No se pudieron leer las fechas."); return

    df['_per'] = df['dt'].dt.strftime('%Y-%m')
    pers = sorted(df['_per'].unique())
    if len(pers) > 1:
        _def = '2026-04' if '2026-04' in pers else pers[-1]   # por defecto: abril (mis fotos)
        sel = st.multiselect("Periodo a simular", pers, default=[_def], key="sim_per")
        if not sel:
            st.warning("Selecciona al menos un periodo."); return
        df = df[df['_per'].isin(sel)].reset_index(drop=True)

    t_ref = df['dt'].min()
    df['t_obs'] = (df['dt'] - t_ref).dt.total_seconds() / 86400.0
    df['cmd0'] = df.apply(
        lambda r: (((float(r['longitud_L']) - (float(r['lambda_sol']) + 180.0) + LN_DEG) + 180) % 360) - 180
        if pd.notnull(r['lambda_sol']) else 0.0, axis=1)

    # ---------- trayectoria REAL medida de cada mancha (1a a ultima foto) ----------
    grupos = sorted(df['id_grupo'].unique())
    cmap = {g: COLORES[i % len(COLORES)] for i, g in enumerate(grupos)}
    tracks = []
    for g in grupos:
        dg = df[df['id_grupo'] == g].sort_values('t_obs')
        pts = [(float(r.t_obs), float(r.latitud_phi), float(r.cmd0)) for r in dg.itertuples()]
        if pts:
            tracks.append(dict(g=g, pts=pts))

    t_start = min(p[0] for tr in tracks for p in tr['pts'])
    t_end   = max(p[0] for tr in tracks for p in tr['pts'])
    if t_end <= t_start: t_end = t_start + 1.0
    n_frames = 30
    steps = [round(t_start + (t_end - t_start) * i / (n_frames - 1), 4) for i in range(n_frames)]

    def interp(tr, tv):
        """phi, cmd interpolados linealmente entre fotos medidas (sin extrapolar)."""
        pts = tr['pts']
        if tv <= pts[0][0]:  return pts[0][1], pts[0][2]
        if tv >= pts[-1][0]: return pts[-1][1], pts[-1][2]
        for i in range(len(pts) - 1):
            t0, p0, c0 = pts[i]; t1, p1, c1 = pts[i + 1]
            if t0 <= tv <= t1:
                f = (tv - t0) / (t1 - t0) if t1 > t0 else 0.0
                return p0 + f * (p1 - p0), c0 + f * (c1 - c0)
        return pts[-1][1], pts[-1][2]

    # ---------- esfera con oscurecimiento de borde ----------
    nv, nu = 36, 72
    Xs, Ys, Zs, Cs = [], [], [], []
    for iv in range(nv):
        vv = math.pi * (-0.5 + iv / (nv - 1))
        rx, ry, rz, rc = [], [], [], []
        for iu in range(nu):
            uu = 2 * math.pi * iu / (nu - 1)
            xx = math.cos(vv) * math.sin(uu); yy = math.sin(vv); zz = math.cos(vv) * math.cos(uu)
            rx.append(xx); ry.append(yy); rz.append(zz)
            rc.append(0.35 + 0.65 * max(0.0, zz))
        Xs.append(rx); Ys.append(ry); Zs.append(rz); Cs.append(rc)
    sphere = go.Surface(x=Xs, y=Ys, z=Zs, surfacecolor=Cs, showscale=False, opacity=1.0,
        hoverinfo='skip', showlegend=False, cmin=0.0, cmax=1.0,
        lighting=dict(ambient=0.95, diffuse=0.15, specular=0.03, roughness=1.0),
        colorscale=[[0.0, '#5a1600'], [0.25, '#8a2a00'], [0.5, '#cc5500'],
                    [0.75, '#ff9930'], [0.92, '#ffd070'], [1.0, '#fff5c0']])

    static = [sphere]
    # Rejilla MINIMA y moderna: solo el ecuador y el meridiano central, y SOLO en la
    # cara frontal (z>0). Asi la rejilla no se cuela por detras de la esfera (eso
    # causaba las "lineas negras" finas y el hexagono raro del centro).
    def _frontal(pts):
        xs, ys, zs = [], [], []
        for (x, y, z) in pts:
            if z > 0.06:
                xs.append(x); ys.append(y); zs.append(z)
            else:
                xs.append(None); ys.append(None); zs.append(None)
        return xs, ys, zs
    _R = 1.006
    _ecu = [(_R*math.sin(t), 0.0, _R*math.cos(t))
            for t in (2*math.pi*i/240 - math.pi for i in range(241))]
    gx, gy, gz = _frontal(_ecu)
    static.append(go.Scatter3d(x=gx, y=gy, z=gz, mode='lines',
        line=dict(color='rgba(255,255,255,0.55)', width=2), showlegend=False, hoverinfo='skip'))
    _mc = [(0.0, _R*math.sin(p), _R*math.cos(p))
           for p in (math.pi*(-0.5+i/240) for i in range(241))]
    gx, gy, gz = _frontal(_mc)
    static.append(go.Scatter3d(x=gx, y=gy, z=gz, mode='lines',
        line=dict(color='rgba(125,220,255,0.5)', width=2), showlegend=False, hoverinfo='skip'))
    static.append(go.Scatter3d(x=[0, 0], y=[1.18, -1.18], z=[0, 0], mode='markers+text',
        marker=dict(color='rgba(125,220,255,0.9)', size=4), text=['N', 'S'],
        textfont=dict(color='rgba(170,235,255,0.95)', size=15, family='Arial Black'),
        textposition='top center', showlegend=False, hoverinfo='skip'))
    n_base = len(static)

    # ---------- rastro (trayectoria REAL, crece con el tiempo) + cabeza ----------
    def trail(tr, tv):
        # une las fotos medidas con t<=tv + el punto interpolado actual
        xs, ys, zs = [], [], []
        for (t, p, c) in tr['pts']:
            if t <= tv + 1e-9:
                X, Y, Z = _pos3(p, c, 1.012); xs.append(X); ys.append(Y); zs.append(Z)
        p, c = interp(tr, tv); X, Y, Z = _pos3(p, c, 1.012)
        xs.append(X); ys.append(Y); zs.append(Z)
        return go.Scatter3d(x=xs, y=ys, z=zs, mode='lines',
            line=dict(color=cmap[tr['g']], width=8),
            legendgroup='M'+str(tr['g']), showlegend=False, hoverinfo='skip')
    def head(tr, tv):
        p, c = interp(tr, tv); X, Y, Z = _pos3(p, c, 1.03)
        vis = Z > 0
        return go.Scatter3d(x=[X], y=[Y], z=[Z], mode='markers+text',
            marker=dict(color=cmap[tr['g']], size=16 if vis else 5,
                        opacity=1.0 if vis else 0.15, line=dict(color='white', width=2.5)),
            text=['M'+str(tr['g'])] if vis else [''], textposition='top center',
            textfont=dict(color='white', size=15, family='Arial Black'),
            name='M'+str(tr['g']), legendgroup='M'+str(tr['g']), showlegend=True,
            hovertemplate='<b>M'+str(tr['g'])+'</b><br>Phi=%.2f deg<extra></extra>' % tr['pts'][0][1])

    data = list(static)
    for tr in tracks:
        data.append(trail(tr, steps[0]))   # frame inicial: rastro casi vacio
        data.append(head(tr, steps[0]))
    idx_dyn = list(range(n_base, n_base + 2*len(tracks)))

    frames = []
    for tv in steps:
        fd = []
        for tr in tracks:
            fd.append(trail(tr, tv)); fd.append(head(tr, tv))
        frames.append(go.Frame(name='%.2f' % tv, data=fd, traces=idx_dyn))

    fecha_lbl = lambda tv: (t_ref + pd.Timedelta(days=tv)).strftime('%d/%m %Hh')
    cam = dict(eye=dict(x=0.0, y=0.0, z=2.2), up=dict(x=0, y=1, z=0),
               center=dict(x=0, y=0, z=0))   # vista recta de frente, norte arriba
    fig = go.Figure(data=data, frames=frames, layout=go.Layout(
        width=720, height=720, paper_bgcolor='#05040f', font=dict(color='white'),
        title=dict(text='Rotacion solar 3D (gira la bola con el raton)', x=0.5,
                   font=dict(size=17, color='white')),
        margin=dict(l=0, r=165, t=50, b=80),
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                   bgcolor='#05040f', camera=cam, aspectmode='cube',
                   dragmode='orbit'),
        legend=dict(x=1.0, y=0.95, bgcolor='rgba(4,4,16,0.96)', font=dict(size=16, color='#ffffff'),
                    itemsizing='constant', bordercolor='rgba(255,255,255,0.35)', borderwidth=1,
                    title=dict(text='Manchas (doble clic=aislar)', font=dict(size=15, color='#ffffff'))),
        updatemenus=[
            dict(type='buttons', x=0.28, y=-0.03, xanchor='center', yanchor='top', showactive=False,
                 bgcolor='#22c55e', bordercolor='rgba(0,0,0,0)', borderwidth=0,
                 pad=dict(l=10, r=10, t=6, b=6),
                 font=dict(color='white', size=14, family='Arial'),
                 buttons=[dict(label='▶  Play', method='animate',
                     args=[None, dict(frame=dict(duration=180, redraw=True),
                                      fromcurrent=True, mode='immediate',
                                      transition=dict(duration=0))])]),
            dict(type='buttons', x=0.62, y=-0.03, xanchor='center', yanchor='top', showactive=False,
                 bgcolor='#334155', bordercolor='rgba(0,0,0,0)', borderwidth=0,
                 pad=dict(l=10, r=10, t=6, b=6),
                 font=dict(color='white', size=14, family='Arial'),
                 buttons=[dict(label='⏸  Pausa', method='animate',
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')])])],
        sliders=[dict(active=0, x=0, len=1.0, pad=dict(b=8, t=40),
            bgcolor='#1a1a4a', font=dict(color='white'),
            currentvalue=dict(prefix='Fecha: ', font=dict(size=14, color='white')),
            steps=[dict(method='animate', label=fecha_lbl(tv),
                args=[['%.2f' % tv], dict(mode='immediate',
                      frame=dict(duration=0, redraw=True))]) for tv in steps])]))

    # ---------- render: April => video + simulacion ; Jose Luis => solo simulacion ----------
    hay_abril = any(str(p).startswith('2026-04') for p in df['_per'].unique())
    gif = os.path.splitext(video_path)[0] + '.gif'
    if hay_abril and (os.path.exists(gif) or os.path.exists(video_path)):
        col_v, col_s = st.columns([1, 1])
        with col_v:
            st.markdown("#### 🎬 Video real (fotos de abril)")
            if os.path.exists(video_path):
                # MP4 H.264: reproductor con boton Play; se para al ultimo dia (sin bucle)
                try: st.video(open(video_path, 'rb').read(), format='video/mp4')
                except Exception: st.video(video_path)
                st.caption("Fotos reales alineadas (Sol centrado, norte arriba). Dale al ▶ Play.")
            elif os.path.exists(gif):
                st.image(gif, use_container_width=True)
        with col_s:
            st.markdown("#### 🖥️ Simulacion 3D")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "**▶ PLAY** (verde): se forma el rastro y gira la rotacion; **se para al terminar** "
        "y el rastro se queda marcado. Entonces **arrastra para girar la bola** y verlo a tu gusto. "
        "Vuelve a dar PLAY para empezar de nuevo. En la leyenda: clic para ocultar, "
        "**doble clic para ver solo una**. Las manchas a distinta latitud giran a distinta "
        "velocidad (rotacion diferencial)."
    )
