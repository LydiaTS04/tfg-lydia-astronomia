
import streamlit as st
import pandas as pd
import sqlite3
import math
import os
try:
    import plotly.graph_objects as go
    TIENE_PLOTLY = True
except ImportError:
    TIENE_PLOTLY = False

def clip(x, lo, hi): return max(lo, min(hi, x))

PHI_ZERO_W    = 1.4442287340242443
LAMBDA_NORTH_W= -0.24212278821900593

def fmt_dms(deg_val):
    sign = '-' if deg_val < 0 else ''
    val = abs(deg_val); d = int(val); rem = (val-d)*60.0; m = int(rem); s = (rem-m)*60.0
    return "{}{:02d}d {:02d}m {:06.3f}s".format(sign, d, m, s)

def solve_mancha_heliografica(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol):
    dx = xm - xc
    dy = -(ym - yc)
    r = math.sqrt(dx**2 + dy**2)
    rho = r / (R_s if R_s != 0 else 1.0)
    theta_m = math.atan2(dy, dx)
    ang_tot = theta_m + mu_s + beta_o
    sin_phi_M = rho * math.sin(ang_tot)
    phi_M = math.asin(clip(sin_phi_M, -1.0, 1.0))
    cos_phi_M = math.cos(phi_M)
    sin_lambda_M = (rho * math.cos(ang_tot)) / cos_phi_M if cos_phi_M != 0.0 else 0.0
    lambda_M = math.asin(clip(sin_lambda_M, -1.0, 1.0))
    lambda_T = l_sol + math.pi
    L = lambda_T + lambda_M - LAMBDA_NORTH_W
    sin_Phi = math.sin(PHI_ZERO_W)*math.sin(phi_M) + math.cos(PHI_ZERO_W)*math.cos(phi_M)*math.cos(L)
    lat_rad = math.asin(clip(sin_Phi, -1.0, 1.0))
    y_num = math.cos(phi_M) * math.sin(L) / math.cos(lat_rad)
    x_den = (math.sin(phi_M) - math.sin(PHI_ZERO_W) * math.sin(lat_rad)) / (math.cos(PHI_ZERO_W) * math.cos(lat_rad))
    alpha_rad = math.atan2(y_num, x_den)
    lon_rad = math.pi - alpha_rad
    return lat_rad, lon_rad, rho, r, theta_m

def calcular_norte(mu_s, R_s, xc, yc, beta_o, l_sol=0.0):
    import math
    # Polo norte solar (Phi=90): en el disco esta en phi_M=PHI_ZERO,
    # lambda_M = LAMBDA_NORTH - (l_sol + pi).  (Antes faltaba el termino l_sol.)
    lam_M_n = LAMBDA_NORTH_W - (l_sol + math.pi)
    yv = math.sin(PHI_ZERO_W)                      # = rho*sin(A)
    xv = math.cos(PHI_ZERO_W) * math.sin(lam_M_n)  # = rho*cos(A)
    A_norte = math.atan2(yv, xv)
    rho_norte = math.hypot(xv, yv)
    theta_norte = A_norte - mu_s - beta_o
    x_norte = xc + rho_norte * math.cos(theta_norte) * R_s
    y_norte = yc - rho_norte * math.sin(theta_norte) * R_s
    return x_norte, y_norte

st.set_page_config(layout="wide", page_title="Gestor BD Manchas")
st.title("Gestor de Base de Datos - Manchas Solares")

RUTA_BD = r"C:\Users\lydia\Downloads\tfg\manchas_tfg.db"

def get_connection():
    return sqlite3.connect(RUTA_BD)

# Parseo de fecha_hora (texto -> datetime) para ordenar correctamente
FMTS_FECHA = ['%d-%m-%Y %H:%M', '%d/%m/%Y %H:%M',
              '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
              '%d-%m-%Y', '%d/%m/%Y']
def parsear_fecha(s):
    if s is None:
        return pd.NaT
    try:
        if pd.isna(s):
            return pd.NaT
    except Exception:
        pass
    for f in FMTS_FECHA:
        try:
            return pd.to_datetime(s, format=f)
        except Exception:
            continue
    return pd.NaT

# Obliquidad de la ecliptica J2000.0
EPSILON_RAD = math.radians(23.0 + 26.0/60.0 + 21.4/3600.0)

def horas_sideral_a_grados(s):
    """Convierte texto 'HH:MM:SS' o 'HH:MM' o decimal a grados de ascension recta."""
    if s is None: return None
    try:
        if pd.isna(s): return None
    except Exception:
        pass
    try:
        t = str(s).strip()
        if ':' in t:
            partes = t.split(':')
            h = float(partes[0])
            m = float(partes[1]) if len(partes) > 1 else 0.0
            sec = float(partes[2]) if len(partes) > 2 else 0.0
            sign = -1.0 if t.startswith('-') else 1.0
            horas = sign * (abs(h) + m/60.0 + sec/3600.0)
        else:
            horas = float(t)
        return horas * 15.0   # 1h = 15 grados
    except Exception:
        return None

def num(v):
    """Convierte a float o None robustamente."""
    if v is None: return None
    try:
        if pd.isna(v): return None
    except Exception:
        pass
    try: return float(v)
    except Exception: return None

def recomputar_mu(phi_obs_deg, theta_str, delta_sol_deg, alfa_sol_deg, mu_antiguo_deg=None):
    """Mu (grados) con MISMO criterio que el simulador 'Fisica Universal de mu':
       1) Recomputa h_sol desde theta, phi, delta, alfa (no usa h guardado en BD).
          sin(h) = sin(delta)*sin(phi) + cos(delta)*cos(phi)*cos(H),  H = theta - alfa
       2) cos(mu) = (sin(phi)*cos(eps) - cos(phi)*sin(eps)*sin(theta)) / cos(h)
       3) Az_sol = atan2(sin(H), sin(phi)*cos(H) - tan(delta)*cos(phi))     [modo B]
       4) Az_pi  = atan2(-cos(theta)*sin(eps),
                          cos(eps)*cos(phi) + sin(eps)*sin(phi)*sin(theta))  [modo E]
       5) Signo: Az_pi < Az_sol  ->  pi a la izquierda del Sol  ->  mu POSITIVO
                 Az_pi > Az_sol  ->  pi a la derecha   del Sol  ->  mu NEGATIVO
    Devuelve None si falta algun dato."""
    phi   = num(phi_obs_deg)
    delta = num(delta_sol_deg)
    alfa  = num(alfa_sol_deg)
    theta_deg = horas_sideral_a_grados(theta_str)
    if phi is None or delta is None or alfa is None or theta_deg is None:
        return None
    phi_r   = math.radians(phi)
    theta_r = math.radians(theta_deg)
    delta_r = math.radians(delta)
    alfa_r  = math.radians(alfa)
    # (1) Recomputar h_sol
    H_r = theta_r - alfa_r
    sin_h = (math.sin(delta_r)*math.sin(phi_r)
             + math.cos(delta_r)*math.cos(phi_r)*math.cos(H_r))
    h_r = math.asin(clip(sin_h, -1.0, 1.0))
    if abs(math.cos(h_r)) < 1e-9:
        return None
    # (2) mu absoluto
    cos_mu = (math.sin(phi_r)*math.cos(EPSILON_RAD)
              - math.cos(phi_r)*math.sin(EPSILON_RAD)*math.sin(theta_r)) / math.cos(h_r)
    mu_abs = math.degrees(math.acos(clip(cos_mu, -1.0, 1.0)))
    # (3) Az_sol (modo B)
    az_sol = math.degrees(math.atan2(
        math.sin(H_r),
        math.sin(phi_r)*math.cos(H_r) - math.tan(delta_r)*math.cos(phi_r)
    ))
    # (4) Az_pi (modo E del codigo original)
    az_pi = math.degrees(math.atan2(
        -math.cos(theta_r)*math.sin(EPSILON_RAD),
        math.cos(EPSILON_RAD)*math.cos(phi_r) + math.sin(EPSILON_RAD)*math.sin(phi_r)*math.sin(theta_r)
    ))
    # (5) Signo segun criterio del simulador
    # Az_pi < Az_sol -> pi a la izquierda (W) del Sol -> mu POSITIVO
    if az_pi < az_sol:
        return  mu_abs
    else:
        return -mu_abs

# ─── PANEL AMARILLO DE CAMBIOS RECIENTES ────────────────────────────
if 'ultimo_cambio' in st.session_state and st.session_state.get('ultimo_cambio'):
    _uc = st.session_state['ultimo_cambio']
    _det = _uc.get('detalle', []) or []
    _c1, _c2 = st.columns([6, 1])
    with _c1:
        st.warning("Ultimo recalculo ({}): {} mancha(s) actualizadas. Celdas modificadas resaltadas en AMARILLO."
                   .format(_uc.get('tipo','?'), _uc.get('n', 0)))
    with _c2:
        st.write("")
        if st.button("Ocultar", key="cerrar_panel_cambios"):
            st.session_state['ultimo_cambio'] = None
            st.rerun()
    if _det:
        _df_diff = pd.DataFrame(_det)
        def _hl_amarillo(v):
            try:
                return 'background-color: #fff3a0; font-weight: bold' if abs(float(v)) > 1e-9 else ''
            except Exception:
                return ''
        _fmt = {}
        for _c in ('dPhi','dL','drho','Phi_antes','Phi_despues','L_antes','L_despues'):
            if _c in _df_diff.columns:
                _fmt[_c] = '{:+.4f}' if _c.startswith('d') or 'Phi' in _c else '{:.4f}'
        _sty = _df_diff.style.format(_fmt, na_rep='-')
        _resaltar = [c for c in ('dPhi','dL','drho') if c in _df_diff.columns]
        if _resaltar:
            try:
                _sty = _sty.map(_hl_amarillo, subset=_resaltar)
            except Exception:
                _sty = _sty.applymap(_hl_amarillo, subset=_resaltar)
        st.dataframe(_sty, use_container_width=True, hide_index=True)
        st.caption("Las celdas AMARILLAS son las cantidades que cambiaron.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Tabla: Observaciones (Fotos)", "Tabla: Mediciones (Manchas)", "Resultados Calculados", "Animacion Solar", "Errores (+-sigma)", "Fotos (galeria)"])

with tab1:
    st.header("Observaciones (Datos de la Imagen y Sol)")
    st.info("Para eliminar una fila: selecciona la casilla y presiona Supr/Delete.")
    conn = get_connection()
    df_obs = pd.read_sql_query("SELECT * FROM Observaciones", conn)
    # ORDENAR por fecha+hora reales (no por texto)
    if 'fecha_hora' in df_obs.columns:
        df_obs['_dt_orden'] = df_obs['fecha_hora'].apply(parsear_fecha)
        df_obs = df_obs.sort_values('_dt_orden', kind='mergesort',
                                    na_position='last').reset_index(drop=True)
        df_obs = df_obs.drop(columns=['_dt_orden'])
    # OCULTAMOS hora_sideral del editor (sigue en la BD, solo no se muestra)
    columnas_eliminar = [c for c in ['P_angulo', 'B0_latitud', 'id_observacion', 'hora_sideral']
                         if c in df_obs.columns]
    df_obs_display = df_obs.drop(columns=columnas_eliminar)
    cfg_obs = {
        "fecha_hora":     "Fecha (DD/MM/AAAA HH:MM)",
        "archivo_img":    "Nombre de Foto (ID)",
        "lat_observador": st.column_config.NumberColumn(
                              "Lat. observador (deg)",
                              help="Latitud del observador en grados decimales (p.ej. 40.4325)."),
        "mu_angulo":      st.column_config.NumberColumn(
                              "mu (grados)",
                              help="Editable a mano. Al guardar se propaga a todas las manchas de la foto."),
        "beta_optica":    "beta optica (grados)",
        "b_pi":           "B_pi (grados)",
        "h_sol":          "Altura Sol h (grados)",
        "az_sol":         "Azimut Sol Az (grados)",
        "lambda_sol":     "Longitud Solar lambda (grados)",
        "declinacion_sol":"Declinacion Sol (grados)",
        "alfa_sol":       "AR Sol (grados)",
        "radio_sol":      "Radio Sol (px)",
        "centro_x":       "Centro X (px)",
        "centro_y":       "Centro Y (px)"
    }
    edited_obs = st.data_editor(df_obs_display, num_rows="dynamic", key="editor_obs", use_container_width=True, column_config=cfg_obs)
    st.caption("Al guardar se propagan mu y beta a las manchas y se recalculan automaticamente Phi, Lambda y rho. "
               "Despues del guardado veras un panel con las celdas modificadas resaltadas.")
    if st.button("Guardar Cambios en Observaciones"):
        # Mantener hora_sideral que esta en BD (no se ha mostrado, no se debe borrar)
        if 'hora_sideral' in df_obs.columns and 'hora_sideral' not in edited_obs.columns:
            edited_obs['hora_sideral'] = df_obs['hora_sideral']
        edited_obs['id_observacion'] = df_obs['id_observacion']
        edited_obs = edited_obs.dropna(subset=['archivo_img'])
        edited_obs = edited_obs[edited_obs['archivo_img'].astype(str).str.strip() != '']
        edited_obs['id_observacion'] = edited_obs['id_observacion'].apply(
            lambda x: int(x) if pd.notnull(x) else None)

        # SNAPSHOT antes (para detectar cambios y resaltar)
        df_obs_prev = df_obs.copy(deep=True).set_index('id_observacion', drop=False)

        cursor = conn.cursor()
        cursor.execute("DELETE FROM Observaciones")
        conn.commit()
        edited_obs.to_sql("Observaciones", conn, if_exists="append", index=False)

        # RECALCULAR mediciones afectadas
        obs_nuevas = {}
        for _, orow in edited_obs.iterrows():
            id_o = orow['id_observacion']
            if pd.notnull(id_o):
                obs_nuevas[int(id_o)] = orow.to_dict()
        df_med_all = pd.read_sql_query("SELECT * FROM Mediciones", conn)
        df_med_prev = df_med_all.copy(deep=True)   # snapshot mediciones
        n_recalc = 0
        cambios_manchas = []
        for idx, mrow in df_med_all.iterrows():
            id_obs = mrow.get('id_observacion')
            if pd.isnull(id_obs): continue
            id_obs = int(id_obs)
            if id_obs not in obs_nuevas: continue
            obs_data = obs_nuevas[id_obs]
            try:
                xm = float(mrow['pixel_x']); ym = float(mrow['pixel_y'])
            except (TypeError, ValueError):
                continue
            mu_deg   = obs_data.get('mu_angulo')
            beta_deg = obs_data.get('beta_optica')
            if pd.notnull(mu_deg):
                df_med_all.at[idx, 'mu_angulo'] = float(mu_deg)
            if pd.notnull(beta_deg):
                df_med_all.at[idx, 'beta_optica'] = float(beta_deg)
            phi_prev = df_med_prev.at[idx, 'latitud_phi']
            lon_prev = df_med_prev.at[idx, 'longitud_L']
            rho_prev = df_med_prev.at[idx, 'rho']
            try:
                mu_r   = math.radians(float(mu_deg))   if pd.notnull(mu_deg)   else 0.0
                beta_r = math.radians(float(beta_deg)) if pd.notnull(beta_deg) else 0.0
                R_s = float(obs_data['radio_sol'])
                xc  = float(obs_data['centro_x']);  yc = float(obs_data['centro_y'])
                l_sol = math.radians(float(obs_data['lambda_sol'])) if pd.notnull(obs_data.get('lambda_sol')) else 0.0
                lat_r, lon_r, rho_c, _r, _th = solve_mancha_heliografica(mu_r, R_s, xm, ym, xc, yc, beta_r, l_sol)
                phi_new = math.degrees(lat_r); lon_new = math.degrees(lon_r)
                df_med_all.at[idx, 'latitud_phi'] = phi_new
                df_med_all.at[idx, 'longitud_L']  = lon_new
                df_med_all.at[idx, 'rho']         = rho_c
                n_recalc += 1
                dphi = phi_new - (float(phi_prev) if pd.notnull(phi_prev) else phi_new)
                dlon = lon_new - (float(lon_prev) if pd.notnull(lon_prev) else lon_new)
                drho = rho_c   - (float(rho_prev) if pd.notnull(rho_prev) else rho_c)
                if abs(dphi) > 1e-6 or abs(dlon) > 1e-6 or abs(drho) > 1e-9:
                    cambios_manchas.append({
                        "Mancha":   "M" + str(mrow.get('id_grupo','?')),
                        "Fecha":    str(obs_data.get('fecha_hora',''))[:16],
                        "mu":       "{:+.3f}".format(float(mu_deg)) if pd.notnull(mu_deg) else "-",
                        "beta":     "{:+.3f}".format(float(beta_deg)) if pd.notnull(beta_deg) else "-",
                        "Phi_antes":   float(phi_prev) if pd.notnull(phi_prev) else 0.0,
                        "Phi_despues": phi_new,
                        "dPhi":     dphi,
                        "L_antes":     float(lon_prev) if pd.notnull(lon_prev) else 0.0,
                        "L_despues":   lon_new,
                        "dL":       dlon,
                        "drho":     drho,
                    })
            except Exception:
                pass
        if n_recalc > 0:
            for _col in ('id_medicion', 'id_observacion'):
                if _col in df_med_all.columns:
                    df_med_all[_col] = df_med_all[_col].apply(
                        lambda x: int(x) if pd.notnull(x) else None)
            cursor.execute("DELETE FROM Mediciones")
            conn.commit()
            df_med_all.to_sql("Mediciones", conn, if_exists="append", index=False)

        # Guardar el resumen en session_state para el panel amarillo
        st.session_state['ultimo_cambio'] = {
            "tipo":    "observaciones",
            "n":       n_recalc,
            "detalle": cambios_manchas,
        }
        st.success("Observaciones guardadas. {} mancha(s) recalculadas.".format(n_recalc))
        st.rerun()
    conn.close()

with tab2:
    st.header("Mediciones (Datos de las Manchas)")
    st.info(
        "**mu y beta** son propiedades de la FOTO (no de cada mancha), por eso aparecen aqui en gris (solo lectura). "
        "Para cambiarlos, edita la pestaña **Observaciones** -> al guardar alli se recalculan TODAS las manchas de esa foto. "
        "Aqui en Mediciones solo se editan **pixel_x** y **pixel_y**: al guardar se recalculan Phi, Lambda y rho de las manchas editadas."
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Mediciones WHERE id_observacion IS NULL")
    conn.commit()
    df_med = pd.read_sql_query("""
        SELECT m.*, o.fecha_hora
        FROM Mediciones m
        LEFT JOIN Observaciones o ON m.id_observacion = o.id_observacion
    """, conn)
    cols = ['id_medicion', 'id_observacion', 'fecha_hora', 'id_grupo', 'pixel_x', 'pixel_y',
            'rho', 'latitud_phi', 'longitud_L', 'mu_angulo', 'beta_optica']
    cols = [c for c in cols if c in df_med.columns]
    df_med = df_med[cols]
    # ORDENAR por fecha+hora reales (manana antes que tarde), luego por id_grupo
    if 'fecha_hora' in df_med.columns:
        df_med['_dt_orden'] = df_med['fecha_hora'].apply(parsear_fecha)
        sort_cols = ['_dt_orden']
        if 'id_grupo' in df_med.columns:
            sort_cols.append('id_grupo')
        df_med = df_med.sort_values(sort_cols, kind='mergesort',
                                    na_position='last').reset_index(drop=True)
        df_med = df_med.drop(columns=['_dt_orden'])
    df_med_display = df_med.drop(columns=['id_medicion', 'id_observacion'])
    cfg_med = {
        "fecha_hora":   st.column_config.TextColumn("Fecha y Hora", disabled=True),
        "id_grupo":     "ID Mancha",
        # mu y beta son propiedades de la FOTO, no de cada mancha:
        # se editan SOLO desde la pestaña Observaciones (que recalcula todo)
        "mu_angulo":    st.column_config.NumberColumn(
                            "mu (grados) [solo lectura]", disabled=True,
                            help="Para cambiar mu, editalo en la pestaña Observaciones (se recalculan todas las manchas de la foto)."),
        "beta_optica":  st.column_config.NumberColumn(
                            "beta (grados) [solo lectura]", disabled=True,
                            help="Para cambiar beta, editalo en la pestaña Observaciones (se recalculan todas las manchas de la foto)."),
        "rho":          st.column_config.NumberColumn("rho [calculado]", disabled=True),
        "latitud_phi":  st.column_config.NumberColumn("Phi (grados) [calculado]", disabled=True),
        "longitud_L":   st.column_config.NumberColumn("Lambda (grados) [calculado]", disabled=True),
    }
    edited_med = st.data_editor(df_med_display, num_rows="dynamic", key="editor_med",
                                use_container_width=True, column_config=cfg_med)
    if st.button("Guardar Cambios en Mediciones"):
        edited_med['id_medicion'] = df_med['id_medicion']
        edited_med['id_observacion'] = df_med['id_observacion']
        edited_med = edited_med.dropna(subset=['id_observacion'])
        # Convertir IDs a int o None — pandas los guarda como float64
        edited_med['id_medicion']   = edited_med['id_medicion'].apply(
            lambda x: int(x) if pd.notnull(x) else None)
        edited_med['id_observacion'] = edited_med['id_observacion'].apply(
            lambda x: int(x) if pd.notnull(x) else None)
        df_obs_ref = pd.read_sql_query(
            "SELECT id_observacion, radio_sol, centro_x, centro_y, lambda_sol FROM Observaciones", conn)
        obs_dict = df_obs_ref.set_index('id_observacion').to_dict('index')
        for idx, row in edited_med.iterrows():
            id_obs = row['id_observacion']
            if id_obs in obs_dict and pd.notnull(row['pixel_x']) and pd.notnull(row['pixel_y']):
                obs_data = obs_dict[id_obs]
                xm = float(row['pixel_x']); ym = float(row['pixel_y'])
                mu_s   = math.radians(float(row['mu_angulo']))   if pd.notnull(row['mu_angulo'])   else 0.0
                beta_o = math.radians(float(row['beta_optica'])) if pd.notnull(row['beta_optica']) else 0.0
                R_s = float(obs_data['radio_sol'])
                xc  = float(obs_data['centro_x']);  yc = float(obs_data['centro_y'])
                l_sol = math.radians(float(obs_data['lambda_sol'])) if pd.notnull(obs_data['lambda_sol']) else 0.0
                lat_rad, lon_rad, rho, _r, _th = solve_mancha_heliografica(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol)
                edited_med.at[idx, 'latitud_phi'] = math.degrees(lat_rad)
                edited_med.at[idx, 'longitud_L']  = math.degrees(lon_rad)
                edited_med.at[idx, 'rho']          = rho
        if 'fecha_hora' in edited_med.columns:
            edited_med = edited_med.drop(columns=['fecha_hora'])
        cursor.execute("DELETE FROM Mediciones")
        conn.commit()
        edited_med.to_sql("Mediciones", conn, if_exists="append", index=False)
        st.success("Tabla Mediciones guardada y recalculada.")
        st.rerun()
    conn.close()

with tab3:
    st.header("Resultados Calculados por Mancha")
    st.info("Solo lectura. Se recomputan en VIVO con los valores actuales de Observaciones y Mediciones (no hay boton de guardar).")
    conn = get_connection()
    # LEFT JOIN para no perder mediciones; ordenamos en Python por datetime real
    df_res = pd.read_sql_query("""
        SELECT
            o.fecha_hora, o.archivo_img,
            m.id_medicion, m.id_observacion, m.id_grupo,
            o.h_sol, o.az_sol, o.lambda_sol,
            COALESCE(o.mu_angulo,  m.mu_angulo)  AS mu_angulo,
            COALESCE(m.beta_optica, 0.0)         AS beta_optica,
            o.centro_x, o.centro_y, o.radio_sol,
            m.pixel_x, m.pixel_y,
            m.rho, m.latitud_phi, m.longitud_L
        FROM Mediciones m
        LEFT JOIN Observaciones o ON m.id_observacion = o.id_observacion
    """, conn)
    n_med_total = pd.read_sql_query("SELECT COUNT(*) AS n FROM Mediciones", conn).iloc[0]['n']
    n_obs_total = pd.read_sql_query("SELECT COUNT(*) AS n FROM Observaciones", conn).iloc[0]['n']
    conn.close()

    # ORDENAR por fecha+hora REALES (no por texto)
    if 'fecha_hora' in df_res.columns:
        df_res['_dt_orden'] = df_res['fecha_hora'].apply(parsear_fecha)
        df_res = df_res.sort_values(['_dt_orden', 'id_grupo'], kind='mergesort',
                                    na_position='last').reset_index(drop=True)
        df_res = df_res.drop(columns=['_dt_orden'])

    if df_res.empty:
        st.info("No hay datos en la base de datos.")
    else:
        st.success("Mostrando **{}** medicion(es) de {} totales, agrupadas en **{}** observacion(es) de {} totales.".format(
            len(df_res), n_med_total, df_res['id_observacion'].nunique(), n_obs_total))
        n_huerfanas = df_res['fecha_hora'].isna().sum()
        if n_huerfanas > 0:
            st.warning("{} medicion(es) sin observacion asociada - aparecen al final.".format(n_huerfanas))

        # Filtro por dia (los 153 expanders abiertos colapsan el navegador)
        df_res['_dia_str'] = df_res['fecha_hora'].apply(
            lambda s: (parsear_fecha(s).strftime('%Y-%m-%d')
                       if pd.notnull(parsear_fecha(s)) else 'Sin fecha'))
        dias_disponibles = ['(Todos)'] + sorted(df_res['_dia_str'].unique())
        dia_sel = st.selectbox("Filtrar por dia", dias_disponibles, index=0, key="tab3_dia")
        if dia_sel != '(Todos)':
            df_res_view = df_res[df_res['_dia_str'] == dia_sel].reset_index(drop=True)
            st.info("Mostrando {} medicion(es) del dia {}.".format(len(df_res_view), dia_sel))
        else:
            df_res_view = df_res
        expandido_por_defecto = (dia_sel != '(Todos)') and (len(df_res_view) <= 20)

        for _, row in df_res_view.iterrows():
            fh_safe   = row['fecha_hora']   if pd.notnull(row['fecha_hora'])   else 'sin fecha'
            arch_safe = row['archivo_img']  if pd.notnull(row['archivo_img'])  else 'sin foto'
            titulo = "📍 Mancha **{}** | {} | {}".format(
                row['id_grupo'], fh_safe, arch_safe)
            with st.expander(titulo, expanded=expandido_por_defecto):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**--- CALCULOS DEL CIELO ---**")
                    h    = row['h_sol']
                    az   = row['az_sol']
                    lam  = row['lambda_sol']
                    mu   = row['mu_angulo']
                    st.text("Altura Sol (h):              {}".format(fmt_dms(float(h))          if pd.notnull(h)   else "N/A"))
                    st.text("Azimut Sol (Az):             {}".format(fmt_dms(float(az))         if pd.notnull(az)  else "N/A"))
                    st.text("Longitud Solar (lambda):     {}".format(fmt_dms(float(lam) % 360) if pd.notnull(lam) else "N/A"))
                    st.text("Angulo Mu (CON SIGNO):       {}".format(fmt_dms(float(mu))         if pd.notnull(mu)  else "N/A"))

                with col2:
                    st.markdown("**--- CALCULOS IMAGEN ---**")
                    try:
                        xm   = float(row['pixel_x']);    ym   = float(row['pixel_y'])
                        xc   = float(row['centro_x']);   yc   = float(row['centro_y'])
                        R_s  = float(row['radio_sol'])
                        mu_r = math.radians(float(row['mu_angulo']))   if pd.notnull(row['mu_angulo'])   else 0.0
                        be_r = math.radians(float(row['beta_optica'])) if pd.notnull(row['beta_optica']) else 0.0
                        ls_r = math.radians(float(row['lambda_sol']))  if pd.notnull(row['lambda_sol'])  else 0.0
                        lat_r, lon_r, rho_c, r_c, th_c = solve_mancha_heliografica(mu_r, R_s, xm, ym, xc, yc, be_r, ls_r)
                        xn, yn = calcular_norte(mu_r, R_s, xc, yc, be_r, ls_r)
                        lon_360 = math.degrees(lon_r) % 360.0
                        lon_pm  = (math.degrees(lon_r) + 180.0) % 360.0 - 180.0
                        st.text("Distancia r:                 {:.2f} px".format(r_c))
                        st.text("Valor Rho:                   {:.6f}".format(rho_c))
                        st.text("Angulo Mancha (theta_m):     {}".format(fmt_dms(math.degrees(th_c))))
                        st.text("Norte Solar en foto (X,Y):   ({:.2f}, {:.2f})".format(xn, yn))
                        st.markdown("---")
                        st.text("LATITUD HELIOGRAF. (Phi):    {}".format(fmt_dms(math.degrees(lat_r))))
                        st.text("LONGITUD HELIOGRAF. [0,360]: {}".format(fmt_dms(lon_360)))
                        st.text("LONGITUD HELIOGRAF. [+-180]: {}".format(fmt_dms(lon_pm)))
                        if rho_c > 1.0:
                            st.warning("Rho > 1: la mancha esta fuera del disco solar.")
                    except Exception as e:
                        st.error("Error calculando: {}".format(e))

with tab4:
    import sim_solar
    sim_solar.render_animacion(RUTA_BD)


# =====================================================================
# PESTAÑA: ERRORES
# Muestra sigma_T, sigma_omega, sigma_Phi para cada par de observaciones
# =====================================================================
# (tab5 en la declaracion de tabs)

# Necesitamos recalcular los pares aqui para mostrar los errores
import math as _math

DELTA_PX_W   = 5.0
FAYE_A_W     = 14.370
FAYE_B_W     = -2.300

def _omega_syn_w(phi_deg):
    pr = _math.radians(abs(float(phi_deg)))
    return FAYE_A_W + FAYE_B_W * _math.sin(pr)**2

def _delta_L_real(L1, L2, dt):
    dL_raw   = (L2 - L1) % 360.0
    k        = int(FAYE_A_W * dt / 360.0)
    dL_real  = dL_raw + k * 360.0
    dL_alt   = dL_raw + (k + 1) * 360.0
    if abs(dL_alt / dt - FAYE_A_W) < abs(dL_real / dt - FAYE_A_W):
        dL_real = dL_alt
    return dL_real

# Necesitamos tab5 — declarada arriba como tab5
# El gestor web regenera este bloque; aqui va el contenido

# (Buscar declaracion de tab5 para añadir contenido)
try:
    _tab5_obj = tab5
except NameError:
    _tab5_obj = None

if _tab5_obj is not None:
    with _tab5_obj:
        st.header("Errores por Mancha (UN punto por mancha)")
        st.info("Solo lectura. Los sigmas (sigma_Phi, sigma_Lambda, sigma_T, sigma_omega) se calculan en VIVO con propagacion numerica (delta = 5 px) usando los valores actuales de mu, beta, centro y radio.")
        st.markdown("""
        **Una fila por mancha** (no por par de observaciones).
        - Phi : media + desviacion tipica muestral de las observaciones, comparada con la propagacion (δ = 5 px). Se usa el MAX.
        - T   : Metodo 1 mejorado (extremos para omega + residuos para S_Lambda) si N >= 3.
                Propagacion analitica desde 5 px si N = 2.
        Estos son exactamente los valores que van a la grafica del modo i.
        """)
        conn_e = get_connection()
        df_e = pd.read_sql_query("""
            SELECT m.id_grupo, o.fecha_hora, m.latitud_phi, m.longitud_L,
                   m.pixel_x, m.pixel_y,
                   COALESCE(o.mu_angulo, m.mu_angulo)   AS mu_angulo,
                   COALESCE(m.beta_optica, 0.0)         AS beta_optica,
                   o.lambda_sol, o.radio_sol, o.centro_x, o.centro_y,
                   o.archivo_img
            FROM Mediciones m
            JOIN Observaciones o ON m.id_observacion = o.id_observacion
            ORDER BY m.id_grupo, o.fecha_hora
        """, conn_e)
        conn_e.close()

        FMTS_E = ['%d-%m-%Y %H:%M','%d/%m/%Y %H:%M','%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M','%d-%m-%Y']
        def _parse_e(s):
            for f in FMTS_E:
                try: return pd.to_datetime(s, format=f)
                except: pass
            return pd.NaT

        df_e['dt_obj'] = df_e['fecha_hora'].apply(_parse_e)
        grupos_e = df_e.groupby('id_grupo')

        # --- sigma_Phi y sigma_Lambda por observacion (propagacion 5 px) ---
        def _sigma_phi_obs(obs_r):
            try:
                px=float(obs_r['pixel_x']); py=float(obs_r['pixel_y'])
                mu_r=_math.radians(float(obs_r['mu_angulo']))   if pd.notnull(obs_r['mu_angulo'])   else 0.0
                be_r=_math.radians(float(obs_r['beta_optica'])) if pd.notnull(obs_r['beta_optica']) else 0.0
                ls_r=_math.radians(float(obs_r['lambda_sol']))  if pd.notnull(obs_r['lambda_sol'])  else 0.0
                rs=float(obs_r['radio_sol']); cx=float(obs_r['centro_x']); cy=float(obs_r['centro_y'])
                d=DELTA_PX_W
                def _smh(xm,ym):
                    return solve_mancha_heliografica(mu_r,rs,xm,ym,cx,cy,be_r,ls_r)
                Phxp,_,_,_,_=_smh(px+d,py); Phxm,_,_,_,_=_smh(px-d,py)
                Phyp,_,_,_,_=_smh(px,py+d); Phym,_,_,_,_=_smh(px,py-d)
                return 0.5*_math.sqrt((_math.degrees(Phxp)-_math.degrees(Phxm))**2 +
                                      (_math.degrees(Phyp)-_math.degrees(Phym))**2)
            except Exception:
                return None

        def _sigma_lambda_obs(obs_r):
            try:
                px=float(obs_r['pixel_x']); py=float(obs_r['pixel_y'])
                mu_r=_math.radians(float(obs_r['mu_angulo']))   if pd.notnull(obs_r['mu_angulo'])   else 0.0
                be_r=_math.radians(float(obs_r['beta_optica'])) if pd.notnull(obs_r['beta_optica']) else 0.0
                ls_r=_math.radians(float(obs_r['lambda_sol']))  if pd.notnull(obs_r['lambda_sol'])  else 0.0
                rs=float(obs_r['radio_sol']); cx=float(obs_r['centro_x']); cy=float(obs_r['centro_y'])
                d=DELTA_PX_W
                def _smh(xm,ym):
                    return solve_mancha_heliografica(mu_r,rs,xm,ym,cx,cy,be_r,ls_r)
                _,Lxp,_,_,_=_smh(px+d,py);  _,Lxm,_,_,_=_smh(px-d,py)
                _,Lyp,_,_,_=_smh(px,py+d);  _,Lym,_,_,_=_smh(px,py-d)
                return 0.5*_math.sqrt((_math.degrees(Lxp)-_math.degrees(Lxm))**2 +
                                      (_math.degrees(Lyp)-_math.degrees(Lym))**2)
            except Exception:
                return None

        filas_mancha = []
        for grp_id, gdf in grupos_e:
            gdf = gdf.sort_values('dt_obj').reset_index(drop=True)
            n_g = len(gdf)
            if n_g < 2:
                continue
            # Phi: media + desv. tipica muestral + propagacion media
            phis = [float(v) for v in gdf['latitud_phi'].tolist()]
            phi_med = sum(phis) / n_g
            S_phi_mu = _math.sqrt(sum((p-phi_med)**2 for p in phis)/(n_g-1)) if n_g >= 2 else 0.0
            sPhi_props = [_sigma_phi_obs(gdf.iloc[i]) for i in range(n_g)]
            sPhi_props = [v for v in sPhi_props if v is not None]
            S_phi_pr = (sum(sPhi_props)/len(sPhi_props)) if sPhi_props else 0.0
            S_phi_fin = max(S_phi_mu, S_phi_pr)

            tiempos = gdf['dt_obj'].tolist()
            if any(pd.isnull(t) for t in tiempos):
                continue
            t1 = tiempos[0]; tN = tiempos[-1]
            dt_tot = (tN - t1).total_seconds() / 86400.0
            if dt_tot < 0.05:
                continue
            Ls = [float(v) for v in gdf['longitud_L'].tolist()]
            L1 = Ls[0]; LN = Ls[-1]
            dL_tot = _delta_L_real(L1, LN, dt_tot)
            if abs(dL_tot) < 0.1:
                continue
            omega_g = dL_tot / dt_tot
            T_g     = 360.0 / omega_g

            sigma_T_g = None; S_L_resid = None; metodo = None
            if n_g >= 3:
                # residuos respecto a la recta extremos
                ts_d = [(tiempos[j]-t1).total_seconds()/86400.0 for j in range(n_g)]
                L_unw = [L1]
                for j in range(1, n_g):
                    dL_j = _delta_L_real(L1, Ls[j], ts_d[j]) if ts_d[j] > 0 else 0.0
                    L_unw.append(L1 + dL_j)
                residuos = [L_unw[j] - (omega_g*ts_d[j] + L1) for j in range(n_g)]
                S_L_resid = _math.sqrt(sum(r*r for r in residuos) / (n_g - 2))
                sigma_T_g = T_g * _math.sqrt(2.0) * S_L_resid / abs(dL_tot)
                metodo = "M1 mejorado"
            else:
                sL1 = _sigma_lambda_obs(gdf.iloc[0])
                sL2 = _sigma_lambda_obs(gdf.iloc[1])
                if sL1 is not None and sL2 is not None:
                    sdL = _math.sqrt(sL1**2 + sL2**2)
                    sigma_T_g = T_g * sdL / abs(dL_tot)
                    metodo = "M1 puro (N=2)"

            sigma_om_g = abs(omega_g)*sigma_T_g/T_g if sigma_T_g is not None else None

            filas_mancha.append(dict(
                grp=str(grp_id), n_obs=n_g,
                f1=str(gdf.iloc[0]['fecha_hora'])[:16],
                fN=str(gdf.iloc[-1]['fecha_hora'])[:16],
                dt_tot=dt_tot, dL_tot=dL_tot,
                phi_med=phi_med,
                S_phi_mu=S_phi_mu, S_phi_pr=S_phi_pr, S_phi_fin=S_phi_fin,
                S_L_resid=S_L_resid,
                omega_g=omega_g, T_g=T_g,
                sigma_T_g=sigma_T_g, sigma_om_g=sigma_om_g,
                metodo=metodo or "sin datos"))

        if filas_mancha:
            st.caption("Total: {} mancha(s) -> {} punto(s) en el grafico.".format(
                len(filas_mancha), len(filas_mancha)))
            for f in sorted(filas_mancha, key=lambda x: int(x['grp'])):
                st.markdown("---")
                st.markdown("### Mancha {}  ·  {} obs  ·  metodo: **{}**".format(
                    f['grp'], f['n_obs'], f['metodo']))
                st.markdown(
                    "**Primera obs:** {}  &emsp;  **Ultima obs:** {}  &emsp;  "
                    "Δt = **{:.3f}** d &emsp; ΔΛ = **{:.3f}°**".format(
                        f['f1'], f['fN'], f['dt_tot'], f['dL_tot']))
                st.markdown(
                    "**Phi media:** {:+.4f}° &emsp;±&emsp; **{:.4f}°**  "
                    "&nbsp;(muestral = {:.4f}°, propagacion = {:.4f}° → se usa el MAX)".format(
                        f['phi_med'], f['S_phi_fin'], f['S_phi_mu'], f['S_phi_pr']))
                if f['S_L_resid'] is not None:
                    st.markdown(
                        "**S_Lambda (residuos):** {:.4f}°".format(f['S_L_resid']))
                sT_s  = "± **{:.4f}** d".format(f['sigma_T_g'])  if f['sigma_T_g']  is not None else "N/D"
                som_s = "± **{:.4f}** °/d".format(f['sigma_om_g']) if f['sigma_om_g'] is not None else "N/D"
                st.markdown(
                    "**ω:** {:.4f} °/d  &nbsp;{} &emsp;&emsp; **T sidéreo:** {:.3f} d &nbsp;{}".format(
                        f['omega_g'], som_s, f['T_g'], sT_s))
        else:
            st.info("No hay manchas con 2 o mas observaciones todavia.")
        _OLD_TAB5_DESACTIVADO = False

# Bloque antiguo desactivado por la actualizacion (un punto por mancha)
if False:
        filas_err = []
        for grp_id, gdf in grupos_e:
            gdf = gdf.sort_values('dt_obj').reset_index(drop=True)
            if len(gdf) < 2:
                continue
            for i in range(len(gdf) - 1):
                r1 = gdf.iloc[i];  r2 = gdf.iloc[i+1]
                if pd.isnull(r1['dt_obj']) or pd.isnull(r2['dt_obj']): continue
                dt_d = (r2['dt_obj'] - r1['dt_obj']).total_seconds() / 86400.0
                if dt_d < 0.05: continue
                L1 = float(r1['longitud_L']); L2 = float(r2['longitud_L'])
                dL = _delta_L_real(L1, L2, dt_d)
                if dL < 0.01: continue
                om   = dL / dt_d
                T    = 360.0 / om
                phi_m = (float(r1['latitud_phi']) + float(r2['latitud_phi'])) / 2.0

                # Calcular sigmas numericos
                sL1 = sL2 = sPh1 = sPh2 = None
                for obs_r, tag in [(r1,'1'),(r2,'2')]:
                    try:
                        px=float(obs_r['pixel_x']); py=float(obs_r['pixel_y'])
                        mu_r  = _math.radians(float(obs_r['mu_angulo']))   if pd.notnull(obs_r['mu_angulo'])   else 0.0
                        be_r  = _math.radians(float(obs_r['beta_optica'])) if pd.notnull(obs_r['beta_optica']) else 0.0
                        ls_r  = _math.radians(float(obs_r['lambda_sol']))  if pd.notnull(obs_r['lambda_sol'])  else 0.0
                        rs    = float(obs_r['radio_sol'])
                        cx    = float(obs_r['centro_x']); cy = float(obs_r['centro_y'])
                        d = DELTA_PX_W
                        def _smh(xm,ym):
                            return solve_mancha_heliografica(mu_r,rs,xm,ym,cx,cy,be_r,ls_r)
                        _,Lxp,_,_,_=_smh(px+d,py);  _,Lxm,_,_,_=_smh(px-d,py)
                        _,Lyp,_,_,_=_smh(px,py+d);  _,Lym,_,_,_=_smh(px,py-d)
                        Phxp,_,_,_,_=_smh(px+d,py); Phxm,_,_,_,_=_smh(px-d,py)
                        Phyp,_,_,_,_=_smh(px,py+d); Phym,_,_,_,_=_smh(px,py-d)
                        sL  = 0.5*_math.sqrt((_math.degrees(Lxp)-_math.degrees(Lxm))**2+(_math.degrees(Lyp)-_math.degrees(Lym))**2)
                        sPh = 0.5*_math.sqrt((_math.degrees(Phxp)-_math.degrees(Phxm))**2+(_math.degrees(Phyp)-_math.degrees(Phym))**2)
                        if tag=='1': sL1=sL; sPh1=sPh
                        else:        sL2=sL; sPh2=sPh
                    except: pass

                sdL = _math.sqrt(sL1**2+sL2**2) if (sL1 is not None and sL2 is not None) else None
                sT  = T  * sdL / dL if sdL is not None and dL > 0 else None
                som = om * sdL / dL if sdL is not None and dL > 0 else None
                sPm = 0.5*_math.sqrt(sPh1**2+sPh2**2) if (sPh1 is not None and sPh2 is not None) else None

                filas_err.append({
                    'Mancha':     str(grp_id),
                    'Obs 1':      str(r1['fecha_hora'])[:16],
                    'Obs 2':      str(r2['fecha_hora'])[:16],
                    'Dt (dias)':  round(dt_d, 3),
                    'DeltaL (°)': round(dL, 4),
                    'Phi (°)':    round(phi_m, 4),
                    'omega (°/d)':round(om, 4),
                    '+-sigma_om': round(som, 4) if som is not None else None,
                    'T_sid (d)':  round(T, 3),
                    '+-sigma_T':  round(sT, 4)  if sT  is not None else None,
                    '+-sigma_Phi':round(sPm, 4) if sPm is not None else None,
                })

        if filas_err:
            st.caption("sigma calculado con propagacion numerica (diferencias finitas centrales, delta = 5 px)")
            # Agrupar por mancha y mostrar como texto
            from collections import defaultdict as _dd
            por_mancha = _dd(list)
            for f in filas_err:
                por_mancha[f['Mancha']].append(f)

            for mancha_id, pares in sorted(por_mancha.items(), key=lambda x: int(x[0])):
                st.markdown("---")
                st.markdown("### ☀️ Mancha {}".format(mancha_id))
                for p in pares:
                    som_str = "± {:.4f}".format(p['+-sigma_om'])   if p['+-sigma_om']  is not None else "N/D"
                    sT_str  = "± {:.4f}".format(p['+-sigma_T'])    if p['+-sigma_T']   is not None else "N/D"
                    sPh_str = "± {:.4f}°".format(p['+-sigma_Phi']) if p['+-sigma_Phi'] is not None else "N/D"
                    st.markdown(
                        "**{}  →  {}** &emsp;&emsp;&emsp;&emsp;&emsp; Δt = **{}** d (días)".format(
                            p['Obs 1'], p['Obs 2'], p['Dt (dias)']))
                    st.markdown(
                        "&emsp; "
                        "ΔΛ = **{:.4f}°** &emsp; "
                        "Φ = **{:.4f}°** &emsp; "
                        "ω = **{:.4f} °/d** &nbsp; {} &emsp; "
                        "T = **{:.3f}** d (días) &nbsp; {} &emsp; "
                        "σΦ = {}".format(
                            p['DeltaL (°)'], p['Phi (°)'],
                            p['omega (°/d)'], som_str,
                            p['T_sid (d)'],  sT_str,
                            sPh_str))
                    st.markdown("")
        else:
            st.info("No hay pares de observaciones del mismo grupo todavia.")

with tab6:
    import galeria
    galeria.render_galeria(os.path.dirname(os.path.abspath(RUTA_BD)))
