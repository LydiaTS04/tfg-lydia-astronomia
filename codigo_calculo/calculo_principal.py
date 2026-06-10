# -*- coding: utf-8 -*-
r"""
Conversor interactivo de coordenadas astronomicas (Híbrido Texto/Símbolos)

CONSTANTES
----------
  epsilon/ε (Oblicuidad de la ecliptica J2000.0) = 23° 26' 21.4"
  phi_0/φ₀  (Polo solar ecliptica)               = 82° 44' 53.56"
  lambda_norte_Sol                                = -13° 52' 21.41"

CONVENIOS
---------
  Azimut: Sur=0°, hacia el Oeste positivo  (rango salida: ±180°)
  Angulo horario H = theta - alpha  (positivo hacia el Oeste)
  Lambda/lambda del Sol: rango [0°, 360°)
  Alpha/alpha: rango [0h, 24h)

==========================================================================
MODO A — Horizontales (Az, h) -> Ecuatoriales (alpha, delta)
==========================================================================
  (I1)  sin(delta) = sin(h)*sin(phi) - cos(h)*cos(phi)*cos(Az)
  (I2)  H          = atan2( sin(Az) , tan(h)*cos(phi) + sin(phi)*cos(Az) )
  (I3)  alpha      = theta - H
  Luego: Ecuatoriales -> Eclipticas para obtener lambda del Sol

==========================================================================
MODO B — Ecuatoriales (alpha, delta) -> Horizontales (Az, h)
==========================================================================
  (D1)  H      = theta - alpha
  (D2)  sin(h) = sin(delta)*sin(phi) + cos(delta)*cos(phi)*cos(H)
  (D3)  Az     = atan2( sin(H) , sin(phi)*cos(H) - tan(delta)*cos(phi) )

==========================================================================
MODO C — Eclipticas (lambda, beta) -> Ecuatoriales (alpha, delta)
==========================================================================
  (C1)  sin(delta) = sin(beta)*cos(eps) + cos(beta)*sin(eps)*sin(lambda)
  (C2)  alpha      = atan2( cos(beta)*sin(lambda)*cos(eps)-sin(beta)*sin(eps),
                            cos(beta)*cos(lambda) )

==========================================================================
MODO D — Ecuatoriales (alpha, delta) -> Eclipticas (lambda, beta)
==========================================================================
  (D1)  sin(beta) = sin(delta)*cos(eps) - cos(delta)*sin(eps)*sin(alpha)
  (D2)  lambda    = atan2( cos(delta)*sin(alpha)*cos(eps)+sin(delta)*sin(eps),
                           cos(delta)*cos(alpha) )

==========================================================================
MODO E — Sol: mu y Az_pi
==========================================================================
  (E1)  cos(mu)  = ( sin(phi)*cos(eps) - cos(phi)*sin(eps)*sin(theta) ) / cos(h)
  (E2)  Az_pi   = atan2( -cos(theta)*sin(eps),
                          cos(eps)*cos(phi)+sin(eps)*sin(phi)*sin(theta) )

==========================================================================
MODO F — Manchas Solares: coordenadas heliograficas (Phi, Lambda)
==========================================================================
  dx = xm-xc,  dy = -(ym-yc),  r = sqrt(dx^2+dy^2),  rho = r/R_sol
  theta_m = atan2(dy,dx)
  phi_M   = arcsin( rho*sin(theta_m+mu+beta) )
  lambda_M= arcsin( rho*cos(theta_m+mu+beta)/cos(phi_M) )
  L       = (lambda_sol+pi) + lambda_M - lambda_N
  Phi     = arcsin( sin(phi0)*sin(phi_M) + cos(phi0)*cos(phi_M)*cos(L) )
  Lambda  = pi - atan2( cos(phi_M)*sin(L)/cos(Phi),
                        (sin(phi_M)-sin(phi0)*sin(Phi))/(cos(phi0)*cos(Phi)) )

==========================================================================
MODO H — Distancia entre Manchas Solares (Triangulo Esferico)
==========================================================================
  cos(d) = sin(Phi1)*sin(Phi2) + cos(Phi1)*cos(Phi2)*cos(L2-L1)
  D = R_Sol * d   [km]

==========================================================================
MODO I — Rotacion Diferencial Solar: Periodo Sidereo vs Latitud
==========================================================================
  omega_exp  = DeltaLambda / Delta_t       [deg/dia, sidereo directo]
  T_sidereo  = 360 / omega_exp             [dias]
  Carrington: omega = 14.522 - 2.840*sin^2(Phi)
  Faye:       omega = 14.370 - 2.300*sin^2(Phi)

  ERRORES (propagacion numerica, delta_px = 5 px):
    Cadena: (px,py) -> dx,dy -> rho,theta_m -> phi_M,lambda_M -> L -> Phi,Lambda -> T
    sigma_Lambda = (1/2)*sqrt( (L(x+d)-L(x-d))^2 + (L(y+d)-L(y-d))^2 )
    sigma_Phi    = (1/2)*sqrt( (P(x+d)-P(x-d))^2 + (P(y+d)-P(y-d))^2 )
    sigma_DeltaL = sqrt(sigma_L1^2 + sigma_L2^2)
    sigma_T      = T * sigma_DeltaL / DeltaLambda
    sigma_Phi_media = (1/2)*sqrt(sigma_Phi1^2 + sigma_Phi2^2)
"""
import sys
import sqlite3
import os
import subprocess
from math import sin, cos, tan, asin, acos, atan, atan2, radians, degrees, pi, sqrt
from datetime import datetime


# matplotlib (opcional, solo para modo i)
try:
    import matplotlib
    # Intentar backend interactivo; si falla (sin display o sin Tk) usar Agg
    for _backend in ('TkAgg', 'Qt5Agg', 'Agg'):
        try:
            matplotlib.use(_backend)
            break
        except Exception:
            continue
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as mpe
    TIENE_MPL = True
except Exception:
    TIENE_MPL = False

# ==================================================
# CONSTANTES
# ==================================================
EPSILON_J2000 = radians(23.0 + 26.0/60.0 + 21.4/3600.0)
PHI_ZERO      = radians(82.0 + 44.0/60.0 + 53.56/3600.0)
LAMBDA_NORTH  = radians(-13.0 - 52.0/60.0 - 21.41/3600.0)
R_SOL_KM      = 696000.0

# Constantes rotacion diferencial
CARRINGTON_A = 14.522   # grados/dia (sidereo)
CARRINGTON_B = -2.840
FAYE_A       = 14.370   # grados/dia (sidereo)
FAYE_B       = -2.300

# Incertidumbre en pixels para propagacion de errores
DELTA_PX = 5.0

CARPETA_TFG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(CARPETA_TFG, 'gestor_web', 'manchas_tfg.db')

# ==================================================
# BASE DE DATOS
# ==================================================
def inicializar_bd():
    if not os.path.exists(CARPETA_TFG): os.makedirs(CARPETA_TFG)
    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Observaciones (
        id_observacion INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora TEXT, archivo_img TEXT UNIQUE, centro_x REAL, centro_y REAL,
        radio_sol REAL, declinacion_sol REAL)''')
    cursor.execute("PRAGMA table_info(Observaciones)")
    columnas_obs = [col[1] for col in cursor.fetchall()]
    if 'declinacion_sol' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN declinacion_sol REAL")
    if 'alfa_sol' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN alfa_sol REAL")
    if 'h_sol' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN h_sol REAL")
    if 'az_sol' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN az_sol REAL")
    if 'lambda_sol' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN lambda_sol REAL")
    if 'mu_angulo' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN mu_angulo REAL")
    if 'beta_optica' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN beta_optica REAL")
    if 'b_pi' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN b_pi REAL")
    if 'hora_sideral' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN hora_sideral TEXT")
    if 'lat_observador' not in columnas_obs:
        cursor.execute("ALTER TABLE Observaciones ADD COLUMN lat_observador REAL")
    cursor.execute('''CREATE TABLE IF NOT EXISTS Mediciones (
        id_medicion INTEGER PRIMARY KEY AUTOINCREMENT, id_observacion INTEGER,
        id_grupo TEXT, pixel_x REAL, pixel_y REAL, rho REAL, latitud_phi REAL, longitud_L REAL,
        FOREIGN KEY(id_observacion) REFERENCES Observaciones(id_observacion),
        UNIQUE(id_observacion, id_grupo))''')
    cursor.execute("PRAGMA table_info(Mediciones)")
    columnas_med = [col[1] for col in cursor.fetchall()]
    if 'mu_angulo' not in columnas_med:
        cursor.execute("ALTER TABLE Mediciones ADD COLUMN mu_angulo REAL")
    if 'beta_optica' not in columnas_med:
        cursor.execute("ALTER TABLE Mediciones ADD COLUMN beta_optica REAL")
    if 'excluida' not in columnas_med:
        cursor.execute("ALTER TABLE Mediciones ADD COLUMN excluida INTEGER DEFAULT 0")
    conn.commit()
    return conn

# ==================================================
# UTILIDADES
# ==================================================
def dms_to_deg(d, m, s):
    sign = 1.0 if d >= 0 else -1.0
    return sign * (abs(d) + m/60.0 + s/3600.0)

def hms_to_hours(h, m, s):
    sign = 1.0 if h >= 0 else -1.0
    return sign * (abs(h) + m/60.0 + s/3600.0)

def hours_to_deg(hours): return hours * 15.0
def clip(x, lo, hi): return max(lo, min(hi, x))
def wrap_pm180(deg_val): return (deg_val + 180.0) % 360.0 - 180.0
def wrap_0_360(deg_val): return deg_val % 360.0
def wrap_0_24(hours_val): return hours_val % 24.0
def wrap_pm12(hours_val): return (hours_val + 12.0) % 24.0 - 12.0

def fmt_dms(deg_val):
    sign = '-' if deg_val < 0 else ''
    val = abs(deg_val); d = int(val); rem = (val-d)*60.0; m = int(rem); s = (rem-m)*60.0
    return "{}{:02d}d {:02d}m {:06.3f}s".format(sign, d, m, s)

def fmt_hms(hours_val):
    sign = '-' if hours_val < 0 else ''
    val = abs(hours_val); h = int(val); rem = (val-h)*60.0; m = int(rem); s = (rem-m)*60.0
    return "{}{:02d}h {:02d}m {:05.2f}s".format(sign, h, m, s)

def input_dms(label):
    try:
        raw = input("   > {} (d m s): ".format(label)).strip().replace(',', '.')
        parts = list(map(float, raw.split()))
        d = parts[0]; m = parts[1] if len(parts)>1 else 0.0; s = parts[2] if len(parts)>2 else 0.0
        return radians(dms_to_deg(d, m, s))
    except: return 0.0

def input_hms(label):
    try:
        raw = input("   > {} (h m s): ".format(label)).strip().replace(',', '.')
        parts = list(map(float, raw.split()))
        h = parts[0]; m = parts[1] if len(parts)>1 else 0.0; s = parts[2] if len(parts)>2 else 0.0
        return radians(hours_to_deg(hms_to_hours(h, m, s)))
    except: return 0.0

# ==================================================
# UTILIDADES PARA MODO I
# ==================================================
def delta_longitud_abs(L1_deg, L2_deg):
    """Diferencia angular absoluta. Devuelve arco minimo [0, 180].
    NOTA: solo es correcto para dt pequeno (< ~13 dias).
    Para dt mayor usa delta_longitud_real."""
    diff = abs((L2_deg - L1_deg) % 360.0)
    if diff > 180.0:
        diff = 360.0 - diff
    return diff

def delta_longitud_real(L1_deg, L2_deg, dt_dias):
    """Diferencia de longitud correcta para cualquier intervalo de tiempo.

    La longitud L aumenta ~14.37 deg/dia (rotacion siderea).
    Para dt > 13 dias, la rotacion real puede ser > 180 grados y
    delta_longitud_abs devuelve el arco complementario equivocado.

    Este metodo usa la rotacion esperada para determinar cuantas vueltas
    completas han pasado y reconstruye el DeltaL verdadero:
        DeltaL = (L2 - L1) mod 360  +  k * 360
    donde k = floor(omega_ref * dt / 360).
    """
    omega_ref   = FAYE_A        # 14.37 deg/dia (referencia siderea ecuatorial)
    dL_raw      = (L2_deg - L1_deg) % 360.0   # [0, 360)
    k           = int(omega_ref * dt_dias / 360.0)   # vueltas completas esperadas
    dL_real     = dL_raw + k * 360.0
    # Verificar si k+1 vueltas encajan mejor (por rotacion diferencial)
    dL_alt      = dL_raw + (k + 1) * 360.0
    omega_real  = dL_real / dt_dias
    omega_alt   = dL_alt  / dt_dias
    # Elegir el candidato cuya omega este mas cerca de omega_ref
    if abs(omega_alt - omega_ref) < abs(omega_real - omega_ref):
        dL_real = dL_alt
    return dL_real

FORMATOS_FECHA = [
    '%d-%m-%Y %H:%M',
    '%d/%m/%Y %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%d-%m-%Y',
]

def fecha_a_dias(fecha_str):
    """Convierte cadena de fecha a dias desde epoca Unix."""
    for fmt in FORMATOS_FECHA:
        try:
            dt = datetime.strptime(fecha_str.strip(), fmt)
            return dt.timestamp() / 86400.0
        except ValueError:
            continue
    return None

def omega_carrington(phi_deg):
    """Velocidad angular sidereal segun Carrington [grados/dia]."""
    return CARRINGTON_A + CARRINGTON_B * sin(radians(phi_deg))**2

def omega_faye(phi_deg):
    """Velocidad angular sidereal segun Faye [grados/dia]."""
    return FAYE_A + FAYE_B * sin(radians(phi_deg))**2

# ==================================================
# FUNCIONES MATEMATICAS
# ==================================================
def solve_inverse_horizontal(phi, h, Az):
    sin_delta = sin(h)*sin(phi) - cos(h)*cos(phi)*cos(Az)
    delta = asin(clip(sin_delta, -1.0, 1.0))
    H = atan2(sin(Az), tan(h)*cos(phi) + sin(phi)*cos(Az))
    return delta, H

def solve_direct_equatorial(phi, delta, H):
    sin_h = sin(delta)*sin(phi) + cos(delta)*cos(phi)*cos(H)
    h = asin(clip(sin_h, -1.0, 1.0))
    Az = atan2(sin(H), sin(phi)*cos(H) - tan(delta)*cos(phi))
    return h, Az

def solve_equatorial_to_ecliptic(alpha, delta, eps):
    sin_beta = sin(delta)*cos(eps) - cos(delta)*sin(eps)*sin(alpha)
    beta = asin(clip(sin_beta, -1.0, 1.0))
    y = cos(delta)*sin(alpha)*cos(eps) + sin(delta)*sin(eps)
    x = cos(delta)*cos(alpha)
    lmb = atan2(y, x)
    return lmb, beta

def solve_ecliptic_to_equatorial(lmb, beta, eps):
    sin_delta = sin(beta)*cos(eps) + cos(beta)*sin(eps)*sin(lmb)
    delta = asin(clip(sin_delta, -1.0, 1.0))
    y = cos(beta)*sin(lmb)*cos(eps) - sin(beta)*sin(eps)
    x = cos(beta)*cos(lmb)
    alpha = atan2(y, x)
    return alpha, delta

def solve_mu_and_azpi(phi, theta, h_sun, eps):
    cos_mu = (sin(phi)*cos(eps) - cos(phi)*sin(eps)*sin(theta)) / cos(h_sun)
    mu = acos(clip(cos_mu, -1.0, 1.0))
    # Polo Norte de la eclitica: alpha=270°=3pi/2, delta=90°-epsilon
    # H_pi = theta - 270°  =>  sin(H_pi)=cos(theta), cos(H_pi)=-sin(theta)
    alpha_pi = 1.5 * pi          # 270 grados en radianes
    delta_pi = 0.5 * pi - eps    # 90° - epsilon
    H_pi = theta - alpha_pi
    az_pi = atan2(sin(H_pi),
                  sin(phi)*cos(H_pi) - tan(delta_pi)*cos(phi))
    return mu, az_pi

def solve_mancha_heliografica(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol):
    dx = xm - xc
    dy = -(ym - yc)
    r = sqrt(dx**2 + dy**2)
    rho = r / (R_s if R_s != 0 else 1.0)
    theta_m = atan2(dy, dx)
    ang_tot = theta_m + mu_s + beta_o
    sin_phi_M = rho * sin(ang_tot)
    phi_M = asin(clip(sin_phi_M, -1.0, 1.0))
    cos_phi_M = cos(phi_M)
    if cos_phi_M != 0.0:
        sin_lambda_M = (rho * cos(ang_tot)) / cos_phi_M
    else:
        sin_lambda_M = 0.0
    lambda_M = asin(clip(sin_lambda_M, -1.0, 1.0))
    lambda_T = l_sol + pi
    L = lambda_T + lambda_M - LAMBDA_NORTH
    sin_Phi = sin(PHI_ZERO)*sin(phi_M) + cos(PHI_ZERO)*cos(phi_M)*cos(L)
    lat_rad = asin(clip(sin_Phi, -1.0, 1.0))
    y_num = cos(phi_M) * sin(L) / cos(lat_rad)
    x_den = (sin(phi_M) - sin(PHI_ZERO)*sin(lat_rad)) / (cos(PHI_ZERO)*cos(lat_rad))
    alpha_rad = atan2(y_num, x_den)
    lon_rad = pi - alpha_rad
    return lat_rad, lon_rad, rho, r, theta_m

# ==================================================
# PROPAGACION NUMERICA DE ERRORES
# Cadena completa: (pixel_x, pixel_y)
#   -> dx, dy
#   -> rho, theta_m
#   -> phi_M, lambda_M
#   -> L
#   -> Phi (latitud), Lambda (longitud)
#   -> T (periodo)
#
# Metodo: PROPAGACION ANALITICA con derivadas parciales escritas a mano
#   sigma_r       = delta
#   sigma_rho     = delta / R_sol
#   sigma_theta_m = delta / r
#   sigma_phi_M, sigma_lambda_M, sigma_Lambda, sigma_Phi: ver PDF 6.5.5-6.5.8
# Identica a las diferencias finitas hasta O(delta^2), validada en
# modo_i_analitico.py.
# ==================================================
def _propaga_analitica(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol):
    """Devuelve (sigma_Lambda_deg, sigma_Phi_deg) por propagacion analitica.
    Usa la cadena de derivadas parciales del PDF 6.5.5 a 6.5.8."""
    delta = DELTA_PX
    # ---- Geometria base ----
    dx = xm - xc; dy = -(ym - yc)
    r = sqrt(dx*dx + dy*dy)
    if r < 1e-9 or R_s < 1e-9:
        return None, None
    rho = r / R_s
    theta_m = atan2(dy, dx)
    Aang = theta_m + mu_s + beta_o
    phi_M = asin(clip(rho*sin(Aang), -1.0, 1.0))
    cphi  = cos(phi_M)
    if abs(cphi) < 1e-9:
        return None, None
    v = (rho*cos(Aang))/cphi
    if abs(v) >= 1.0:
        return None, None
    lam_M = asin(clip(v, -1.0, 1.0))
    lam_T = l_sol + pi
    L_aux = lam_T + lam_M - LAMBDA_NORTH
    sin_Phi = sin(PHI_ZERO)*sin(phi_M) + cos(PHI_ZERO)*cphi*cos(L_aux)
    Phi = asin(clip(sin_Phi, -1.0, 1.0))
    cPhi = cos(Phi)
    if abs(cPhi) < 1e-9:
        return None, None
    # ---- Errores intermedios ----
    sigma_r     = delta
    sigma_rho   = delta / R_s
    sigma_th_m  = delta / r
    # ---- sigma_phi_M (6.5.5) ----
    den_phi = sqrt(max(1.0 - (rho*sin(Aang))**2, 1e-18))
    dphi_drho = sin(Aang) / den_phi
    dphi_dA   = rho*cos(Aang) / den_phi
    sigma_phi_M = sqrt((dphi_drho*sigma_rho)**2 + (dphi_dA*sigma_th_m)**2)
    # ---- sigma_lambda_M (6.5.6) ----
    den_lam = sqrt(max(1.0 - v*v, 1e-18))
    dv_drho = cos(Aang) / cphi
    dv_dA   = -rho*sin(Aang) / cphi
    dv_dphi = rho*cos(Aang)*sin(phi_M) / (cphi*cphi)
    inv_d   = 1.0 / den_lam
    sigma_lam_M = sqrt((inv_d*dv_drho*sigma_rho )**2 +
                       (inv_d*dv_dA  *sigma_th_m)**2 +
                       (inv_d*dv_dphi*sigma_phi_M)**2)
    # ---- sigma_Lambda = sigma_lambda_M (6.5.7) ----
    sigma_Lambda = sigma_lam_M
    # ---- sigma_Phi (6.5.8) ----
    dw_dphi = sin(PHI_ZERO)*cphi - cos(PHI_ZERO)*sin(phi_M)*cos(L_aux)
    dw_dLau = -cos(PHI_ZERO)*cphi*sin(L_aux)
    inv_cP  = 1.0 / cPhi
    sigma_Phi = sqrt((inv_cP*dw_dphi*sigma_phi_M )**2 +
                     (inv_cP*dw_dLau*sigma_Lambda)**2)
    return degrees(sigma_Lambda), degrees(sigma_Phi)

def sigma_Lambda_num(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol):
    """Incertidumbre en Lambda (longitud heliografica) [grados] por
    PROPAGACION ANALITICA (derivadas parciales escritas a mano)."""
    sL, _ = _propaga_analitica(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol)
    return sL if sL is not None else 0.0

def sigma_Phi_num(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol):
    """Incertidumbre en Phi (latitud heliografica) [grados] por
    PROPAGACION ANALITICA (derivadas parciales escritas a mano)."""
    _, sP = _propaga_analitica(mu_s, R_s, xm, ym, xc, yc, beta_o, l_sol)
    return sP if sP is not None else 0.0

# ==================================================
# DISTANCIA ENTRE MANCHAS (Triangulo Esferico)
# ==================================================
def distancia_manchas_calc(phi1_rad, lam1_rad, phi2_rad, lam2_rad):
    cos_d = (sin(phi1_rad)*sin(phi2_rad)
             + cos(phi1_rad)*cos(phi2_rad)*cos(lam2_rad - lam1_rad))
    cos_d = clip(cos_d, -1.0, 1.0)
    d_rad = acos(cos_d)
    d_deg = degrees(d_rad)
    d_km  = R_SOL_KM * d_rad
    return d_rad, d_deg, d_km

# ==================================================
# VENTANA DE EXCLUSION DE MEDICIONES (Modo I)
# Permite marcar manchas individuales para que NO entren en el calculo
# de errores, sin borrarlas de la base de datos.
# ==================================================
def pantalla_exclusion(conn):
    """Abre una ventana tkinter con una tabla de todas las mediciones.
       El usuario marca/desmarca cuales excluir; al cerrar, guarda en BD."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print("\n   [!] tkinter no disponible. Se calcularan todas las mediciones.")
        return

    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id_medicion, m.id_grupo, o.fecha_hora,
               m.latitud_phi, m.longitud_L,
               COALESCE(m.excluida, 0) AS excluida
        FROM Mediciones m
        JOIN Observaciones o ON m.id_observacion = o.id_observacion
        WHERE m.latitud_phi IS NOT NULL
        ORDER BY m.id_grupo, o.fecha_hora
    """)
    filas = cursor.fetchall()
    if not filas:
        return

    # Agrupar por mancha para calcular medias (manchas con N>=2)
    grupos = {}
    for r in filas:
        gid = r[1]
        grupos.setdefault(gid, []).append(r)
    medias = {}
    for gid, rows in grupos.items():
        # Solo usar mediciones NO excluidas para calcular media
        phis_validos = [r[3] for r in rows if r[5] == 0]
        if not phis_validos:
            phis_validos = [r[3] for r in rows]
        medias[gid] = sum(phis_validos) / len(phis_validos)

    # Crear ventana
    root = tk.Tk()
    root.title("Modo I — Filtro de mediciones (cierra cuando termines)")
    root.geometry("950x650")
    root.configure(bg='#f4f6fa')

    titulo = tk.Label(root,
        text="Selecciona las mediciones que quieres EXCLUIR del cálculo de errores",
        font=('Segoe UI', 12, 'bold'), bg='#f4f6fa', fg='#1a237e', pady=8)
    titulo.pack()

    subtit = tk.Label(root,
        text="Las observaciones con desviación > 2° respecto a la media de su mancha se marcan en rojo.\n"
             "Pulsa la casilla 'Excluir' para descartarlas. La medición NO se borra de la BD.",
        font=('Segoe UI', 9), bg='#f4f6fa', fg='#444444', pady=4)
    subtit.pack()

    # Frame con scroll
    cont = tk.Frame(root, bg='#f4f6fa')
    cont.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
    canvas = tk.Canvas(cont, bg='white', highlightthickness=1, highlightbackground='#aaa')
    scrolly = ttk.Scrollbar(cont, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=scrolly.set)
    scrolly.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)

    inner = tk.Frame(canvas, bg='white')
    canvas_window = canvas.create_window((0, 0), window=inner, anchor='nw')

    def _on_inner_config(e):
        canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.itemconfig(canvas_window, width=e.width)
    inner.bind('<Configure>', _on_inner_config)

    # Permitir scroll con la rueda del raton
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
    canvas.bind_all('<MouseWheel>', _on_mousewheel)

    # Cabecera
    headers = ['Excluir', 'Mancha', 'Fecha', 'Φ (°)', 'L (°)', 'Estado']
    widths  = [70, 90, 180, 110, 110, 320]
    for col, (h, w) in enumerate(zip(headers, widths)):
        lbl = tk.Label(inner, text=h, bg='#1a237e', fg='white',
                       font=('Segoe UI', 10, 'bold'),
                       width=max(8, w // 8), pady=6)
        lbl.grid(row=0, column=col, sticky='ew', padx=1, pady=1)

    # Filas
    checks = {}  # id_medicion -> BooleanVar
    row_idx = 1
    grupo_anterior = None
    for r in filas:
        id_med, gid, fecha, phi, L, exc = r
        media = medias[gid]
        diff = abs(phi - media)
        is_sosp = diff > 2.0

        # Banda separadora entre grupos (cambio de mancha)
        if grupo_anterior is not None and grupo_anterior != gid:
            sep = tk.Frame(inner, bg='#dddddd', height=2)
            sep.grid(row=row_idx, column=0, columnspan=6, sticky='ew')
            row_idx += 1
        grupo_anterior = gid

        # Color de fila: rojo claro para sospechosa, alterno gris para el resto
        if is_sosp:
            bg_fila = '#ffe4e4'
            fg_estado = '#b71c1c'
        else:
            bg_fila = '#f6f6f6' if row_idx % 2 else 'white'
            fg_estado = '#2e7d32'

        var = tk.BooleanVar(value=bool(exc))
        checks[id_med] = var

        cb = tk.Checkbutton(inner, variable=var, bg=bg_fila)
        cb.grid(row=row_idx, column=0, sticky='ew', padx=1)

        tk.Label(inner, text=f"M{gid}", bg=bg_fila,
                 font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=1, sticky='ew')
        tk.Label(inner, text=str(fecha), bg=bg_fila,
                 font=('Consolas', 9)).grid(row=row_idx, column=2, sticky='ew')
        tk.Label(inner, text=f"{phi:+.3f}", bg=bg_fila,
                 font=('Consolas', 10)).grid(row=row_idx, column=3, sticky='ew')
        tk.Label(inner, text=f"{L:.2f}", bg=bg_fila,
                 font=('Consolas', 10)).grid(row=row_idx, column=4, sticky='ew')

        if is_sosp:
            est = "SOSPECHOSA  dif {:.1f}° con media {:+.2f}°".format(diff, media)
        else:
            est = "OK  (media de la mancha {:+.2f}°, dif {:.1f}°)".format(media, diff)
        tk.Label(inner, text=est, bg=bg_fila, fg=fg_estado,
                 font=('Segoe UI', 9)).grid(row=row_idx, column=5, sticky='w', padx=6)
        row_idx += 1

    # Barra inferior con botones
    barra = tk.Frame(root, bg='#f4f6fa', pady=10)
    barra.pack(fill=tk.X)

    info = tk.Label(barra,
        text="Total: {} mediciones".format(len(filas)),
        bg='#f4f6fa', font=('Segoe UI', 9))
    info.pack(side='left', padx=20)

    def marcar_sospechosas():
        for r in filas:
            id_med, gid, _, phi, _, _ = r
            if abs(phi - medias[gid]) > 2.0:
                checks[id_med].set(True)

    def desmarcar_todo():
        for v in checks.values():
            v.set(False)

    def aplicar_y_cerrar():
        for id_med, var in checks.items():
            valor = 1 if var.get() else 0
            cursor.execute("UPDATE Mediciones SET excluida = ? WHERE id_medicion = ?",
                           (valor, id_med))
        conn.commit()
        n_exc = sum(1 for v in checks.values() if v.get())
        print("\n   [OK] Excluidas {} medicion(es) del calculo.".format(n_exc))
        root.destroy()

    tk.Button(barra, text="Marcar todas las sospechosas",
              command=marcar_sospechosas, bg='#ffeb99',
              font=('Segoe UI', 9, 'bold'), padx=10).pack(side='left', padx=4)
    tk.Button(barra, text="Desmarcar todo",
              command=desmarcar_todo, bg='#dddddd',
              font=('Segoe UI', 9, 'bold'), padx=10).pack(side='left', padx=4)
    tk.Button(barra, text="Aplicar y calcular  →",
              command=aplicar_y_cerrar, bg='#1a237e', fg='white',
              font=('Segoe UI', 10, 'bold'), padx=20).pack(side='right', padx=20)

    root.mainloop()


# ==================================================
# ROTACION SOLAR (Modo I)
# ==================================================
def calcular_rotacion(conn):
    # PASO 0: pantalla de exclusion (el usuario marca que mediciones omitir)
    print("\n   Abriendo ventana de filtro de mediciones...")
    print("   Marca las mediciones a EXCLUIR del calculo y cierra la ventana.")
    pantalla_exclusion(conn)

    cursor = conn.cursor()
    # Traemos tambien los datos de pixel y observacion para calcular errores
    # ADEMAS: filtramos las mediciones marcadas como excluidas
    cursor.execute("""
        SELECT m.id_grupo,
               o.fecha_hora,
               m.latitud_phi,
               m.longitud_L,
               o.archivo_img,
               m.pixel_x,
               m.pixel_y,
               COALESCE(o.mu_angulo, m.mu_angulo)   AS mu_angulo,
               COALESCE(m.beta_optica, o.beta_optica, 0.0) AS beta_optica,
               o.radio_sol,
               o.centro_x,
               o.centro_y,
               o.lambda_sol
        FROM Mediciones m
        JOIN Observaciones o ON m.id_observacion = o.id_observacion
        WHERE m.latitud_phi IS NOT NULL AND m.longitud_L IS NOT NULL
          AND COALESCE(m.excluida, 0) = 0
        ORDER BY m.id_grupo, o.fecha_hora
    """)
    filas = cursor.fetchall()

    if not filas:
        print("\n   [!] La BD esta vacia o no tiene coordenadas calculadas.")
        return

    # grupos[id_grupo] = lista de tuplas con indices:
    # 0=fecha  1=phi(deg)  2=L(deg)  3=archivo
    # 4=px     5=py        6=mu_deg  7=beta_deg
    # 8=r_sol  9=cx        10=cy     11=lsol_deg
    grupos = {}
    for row in filas:
        id_grupo = row[0]
        if id_grupo not in grupos:
            grupos[id_grupo] = []
        grupos[id_grupo].append(row[1:])   # guarda todo menos id_grupo

    # --------------------------------------------------
    # Desviacion tipica MUESTRAL de Phi por grupo
    # (variabilidad real entre observaciones del mismo grupo)
    # --------------------------------------------------
    sigma_phi_muestra_grp = {}
    n_obs_grp             = {}
    for id_grupo, obs in grupos.items():
        phis_g = [o[1] for o in obs]
        n = len(phis_g)
        n_obs_grp[id_grupo] = n
        if n >= 2:
            media_g  = sum(phis_g) / n
            varianza = sum((p - media_g)**2 for p in phis_g) / (n - 1)
            sigma_phi_muestra_grp[id_grupo] = sqrt(varianza)
        else:
            sigma_phi_muestra_grp[id_grupo] = None

    # ==================================================================
    # METODO 1 MEJORADO por grupo (extremos para omega, residuos para S_L)
    # ------------------------------------------------------------------
    # Para cada mancha con N >= 3 observaciones:
    #   1) recta entre extremos:     omega = (L_N - L_1) / (t_N - t_1)
    #   2) residuos respecto a esa recta:  r_i = L_i - (omega*t_i + L_0)
    #   3) S_Lambda = sqrt( sum(r_i^2) / (N-2) )
    #   4) sigma_T  = T * sqrt(2) * S_Lambda / |DeltaLambda|
    #
    # Devuelve UN solo T y UN solo sigma_T por mancha (no por par de obs).
    # Si N < 3 los residuos son siempre 0 -> el metodo no aporta.
    # ==================================================================
    metodo1_mej_grp = {}
    for id_grupo, obs in grupos.items():
        n = len(obs)
        if n < 3:
            metodo1_mej_grp[id_grupo] = None
            continue
        fechas_g = [o[0] for o in obs]
        Ls_g     = [o[2] for o in obs]
        ts_g     = [fecha_a_dias(f) for f in fechas_g]
        if any(t is None for t in ts_g):
            metodo1_mej_grp[id_grupo] = None
            continue
        # Ordenar por tiempo
        pares = sorted(zip(ts_g, Ls_g), key=lambda p: p[0])
        ts_s  = [p[0] for p in pares]
        Ls_s  = [p[1] for p in pares]
        # Desplegar Lambda respecto al primer punto (mismo unwrap que usa el resto)
        L_unw = [Ls_s[0]]
        ok    = True
        for j in range(1, len(Ls_s)):
            dt_j = ts_s[j] - ts_s[0]
            if dt_j <= 0:
                ok = False; break
            dL_j = delta_longitud_real(Ls_s[0], Ls_s[j], dt_j)
            L_unw.append(Ls_s[0] + dL_j)
        if not ok:
            metodo1_mej_grp[id_grupo] = None
            continue
        t1, tN = ts_s[0],  ts_s[-1]
        L1, LN = L_unw[0], L_unw[-1]
        dt_tot = tN - t1
        dL_tot = LN - L1
        if dt_tot <= 0 or abs(dL_tot) < 0.1:
            metodo1_mej_grp[id_grupo] = None
            continue
        omega_ext = dL_tot / dt_tot
        L0_int    = L1 - omega_ext * t1
        T_ext     = 360.0 / omega_ext
        # Residuos en TODOS los puntos (los dos extremos dan exactamente 0)
        residuos  = [L_unw[j] - (omega_ext * ts_s[j] + L0_int) for j in range(n)]
        # S_Lambda con (N-2) grados de libertad (la recta consume 2)
        S_L_resid = sqrt(sum(r*r for r in residuos) / (n - 2))
        sigma_T_mej = T_ext * sqrt(2.0) * S_L_resid / abs(dL_tot)
        # phi promedio del grupo (para mostrarlo junto al resultado)
        phi_media_g = sum(o[1] for o in obs) / n

        metodo1_mej_grp[id_grupo] = {
            'N'          : n,
            'phi_media'  : phi_media_g,
            'dt_tot'     : dt_tot,
            'dL_tot'     : dL_tot,
            'omega_ext'  : omega_ext,
            'T_ext'      : T_ext,
            'S_L_resid'  : S_L_resid,
            'sigma_T_mej': sigma_T_mej,
            'residuos'   : residuos,
            'ts'         : ts_s,
            'L_unw'      : L_unw,
        }

    resultados   = []
    advertencias = []

    print("\n" + "="*100)
    print("   ROTACION DIFERENCIAL SOLAR")
    print("   omega_exp = DeltaLambda/Delta_t  |  T_sid = 360/omega_exp  |  delta_px = {:.0f} px".format(DELTA_PX))
    print("   Carrington: omega = {:.3f} + ({:.3f})*sin^2(Phi)  [sidereo]".format(CARRINGTON_A, CARRINGTON_B))
    print("   Faye:       omega = {:.3f} + ({:.3f})*sin^2(Phi)  [sidereo]".format(FAYE_A, FAYE_B))
    print("="*100)
    print("   {:<8} {:<16} {:<16} {:>8} {:>8} {:>9} {:>9} {:>9} {:>9} {:>8} {:>8}".format(
        "Mancha", "Obs 1", "Obs 2",
        "Phi(deg)", "dL(deg)", "w_exp", "w_Carr", "w_Faye", "T_sid(d)",
        "sT(d)", "sPhi(d)"))
    print("   " + "-"*100)

    for id_grupo, obs in sorted(grupos.items()):
        if len(obs) < 2:
            advertencias.append("  Mancha {:>6}: solo 1 observacion (necesitas >= 2).".format(id_grupo))
            continue

        sigma_phi_g = sigma_phi_muestra_grp.get(id_grupo)
        n_obs_g     = n_obs_grp.get(id_grupo, len(obs))

        for i in range(len(obs) - 1):
            row1 = obs[i];   row2 = obs[i + 1]

            f1       = row1[0];  phi1 = row1[1];  L1 = row1[2];  arch1 = row1[3]
            px1      = row1[4];  py1  = row1[5];  mu1_deg  = row1[6];  beta1_deg = row1[7]
            rs1      = row1[8];  cx1  = row1[9];  cy1      = row1[10]; lsol1_deg = row1[11]

            f2       = row2[0];  phi2 = row2[1];  L2 = row2[2];  arch2 = row2[3]
            px2      = row2[4];  py2  = row2[5];  mu2_deg  = row2[6];  beta2_deg = row2[7]
            rs2      = row2[8];  cx2  = row2[9];  cy2      = row2[10]; lsol2_deg = row2[11]

            t1 = fecha_a_dias(f1);  t2 = fecha_a_dias(f2)
            if t1 is None or t2 is None:
                advertencias.append("  Mancha {:>6}: no se pudo leer la fecha '{}' o '{}'.".format(
                    id_grupo, f1, f2))
                continue

            dt = abs(t2 - t1)
            if dt < 0.05:
                advertencias.append("  Mancha {:>6}: observaciones demasiado cercanas ({:.2f} d).".format(
                    id_grupo, dt))
                continue

            dL = delta_longitud_real(L1, L2, dt)
            if dL < 0.1:
                advertencias.append("  Mancha {:>6}: DeltaLambda casi cero ({:.4f} deg). "
                    "Verifica que los pixeles son distintos en cada foto.".format(id_grupo, dL))
                continue

            omega_exp = dL / dt
            T_sid     = 360.0 / omega_exp
            phi_media = (phi1 + phi2) / 2.0
            w_carr    = omega_carrington(phi_media)
            w_faye    = omega_faye(phi_media)

            if T_sid < 15.0 or T_sid > 50.0:
                advertencias.append("  Mancha {:>6}: T_sid={:.1f}d fuera del rango (15-50 d). "
                    "Obs: {} -> {}. Revisa los datos.".format(id_grupo, T_sid, f1, f2))

            # --------------------------------------------------
            # PROPAGACION NUMERICA DE ERRORES
            # Verificamos que existan todos los datos de pixel y observacion
            # --------------------------------------------------
            def datos_completos(px, py, mu_d, beta_d, rs, cx, cy, lsol_d):
                return (all(v is not None for v in [px, py, mu_d, beta_d, rs, cx, cy, lsol_d])
                        and rs > 0)

            sL1_deg  = None;  sPhi1_num = None
            sL2_deg  = None;  sPhi2_num = None

            try:
                if datos_completos(px1, py1, mu1_deg, beta1_deg, rs1, cx1, cy1, lsol1_deg):
                    mu1_r    = radians(float(mu1_deg))
                    beta1_r  = radians(float(beta1_deg))
                    lsol1_r  = radians(float(lsol1_deg))
                    rs1f     = float(rs1)
                    cx1f     = float(cx1);  cy1f = float(cy1)
                    px1f     = float(px1);  py1f = float(py1)
                    sL1_deg  = sigma_Lambda_num(mu1_r, rs1f, px1f, py1f, cx1f, cy1f, beta1_r, lsol1_r)
                    sPhi1_num= sigma_Phi_num(   mu1_r, rs1f, px1f, py1f, cx1f, cy1f, beta1_r, lsol1_r)
            except Exception:
                pass

            try:
                if datos_completos(px2, py2, mu2_deg, beta2_deg, rs2, cx2, cy2, lsol2_deg):
                    mu2_r    = radians(float(mu2_deg))
                    beta2_r  = radians(float(beta2_deg))
                    lsol2_r  = radians(float(lsol2_deg))
                    rs2f     = float(rs2)
                    cx2f     = float(cx2);  cy2f = float(cy2)
                    px2f     = float(px2);  py2f = float(py2)
                    sL2_deg  = sigma_Lambda_num(mu2_r, rs2f, px2f, py2f, cx2f, cy2f, beta2_r, lsol2_r)
                    sPhi2_num= sigma_Phi_num(   mu2_r, rs2f, px2f, py2f, cx2f, cy2f, beta2_r, lsol2_r)
            except Exception:
                pass

            # sigma_DeltaLambda = sqrt(sL1^2 + sL2^2)
            # sigma_T           = T * sigma_DeltaL / DeltaL
            # sigma_omega       = omega * sigma_DeltaL / DeltaL  (= sigma_DeltaL / dt)
            sigma_dL     = None
            sigma_T_val  = None
            sigma_om_val = None
            if sL1_deg is not None and sL2_deg is not None and dL > 0:
                sigma_dL     = sqrt(sL1_deg**2 + sL2_deg**2)
                sigma_T_val  = T_sid     * sigma_dL / dL
                sigma_om_val = omega_exp * sigma_dL / dL

            # sigma_Phi_media para la barra vertical del grafico:
            # error de la media de las dos observaciones = (1/2)*sqrt(sPhi1^2+sPhi2^2)
            sigma_phi_num_media = None
            if sPhi1_num is not None and sPhi2_num is not None:
                sigma_phi_num_media = 0.5 * sqrt(sPhi1_num**2 + sPhi2_num**2)
            elif sPhi1_num is not None:
                sigma_phi_num_media = sPhi1_num
            elif sPhi2_num is not None:
                sigma_phi_num_media = sPhi2_num
            # para el grafico: usar el maximo entre el error numerico y el muestral
            # asi la barra siempre es visible y refleja la peor incertidumbre real
            if sigma_phi_num_media is None:
                sigma_phi_num_media = sigma_phi_g   # fallback si fallo el calculo
            elif sigma_phi_g is not None:
                sigma_phi_num_media = max(sigma_phi_num_media, sigma_phi_g)

            sT_str   = "{:>8.3f}".format(sigma_T_val)         if sigma_T_val         is not None else "     N/D"
            sPhi_str = "{:>8.3f}".format(sigma_phi_num_media) if sigma_phi_num_media is not None else "     N/D"

            # ------- Metodo 1 mejorado (mismo para todos los pares del grupo) -------
            m1mej = metodo1_mej_grp.get(id_grupo)
            if m1mej is not None:
                omega_ext_g   = m1mej['omega_ext']
                T_ext_g       = m1mej['T_ext']
                S_L_resid_g   = m1mej['S_L_resid']
                sigma_T_mej_g = m1mej['sigma_T_mej']
            else:
                omega_ext_g = T_ext_g = S_L_resid_g = sigma_T_mej_g = None

            resultados.append({
                'grupo'              : id_grupo,
                'phi'                : phi_media,
                'phi1'               : phi1,        'phi2'  : phi2,
                'L1'                 : L1,           'L2'   : L2,
                'omega_exp'          : omega_exp,
                'w_carr'             : w_carr,
                'w_faye'             : w_faye,
                'T_sid'              : T_sid,
                'dL'                 : dL,
                'dt'                 : dt,
                'f1'                 : f1,           'f2'   : f2,
                'arch1'              : arch1,         'arch2': arch2,
                # errores individuales por observacion
                'sL1'                : sL1_deg,
                'sL2'                : sL2_deg,
                'sPhi1_num'          : sPhi1_num,
                'sPhi2_num'          : sPhi2_num,
                # errores del par
                'sigma_dL'           : sigma_dL,
                'sigma_T'            : sigma_T_val,
                'sigma_omega'        : sigma_om_val,
                # ---- METODO 1 MEJORADO (mismo valor para todos los pares del grupo) ----
                'omega_ext_grupo'    : omega_ext_g,
                'T_ext_grupo'        : T_ext_g,
                'S_L_resid_grupo'    : S_L_resid_g,
                'sigma_T_mejorado'   : sigma_T_mej_g,
                # para la grafica
                'sigma_phi_num_media': sigma_phi_num_media,
                # informativo
                'sigma_phi_muestra'  : sigma_phi_g,
                'n_obs_g'            : n_obs_g,
            })

            print("   {:<8} {:<16} {:<16} {:>8.3f} {:>8.3f} {:>9.4f} {:>9.4f} {:>9.4f} {:>9.3f} {} {}".format(
                str(id_grupo), str(f1)[:16], str(f2)[:16],
                phi_media, dL, omega_exp, w_carr, w_faye, T_sid,
                sT_str, sPhi_str))

    if resultados:
        print()
        print("   DETALLE COMPLETO:")
        print("   " + "-"*100)
        for r in resultados:
            print()
            print("   Mancha: {}".format(r['grupo']))
            print("     Obs 1 : {}   Phi={:+.4f} deg   L={:.4f} deg   ({})".format(
                r['f1'], r['phi1'], wrap_0_360(r['L1']), r['arch1']))
            print("     Obs 2 : {}   Phi={:+.4f} deg   L={:.4f} deg   ({})".format(
                r['f2'], r['phi2'], wrap_0_360(r['L2']), r['arch2']))
            print("     Delta_t            = {:.4f} dias".format(r['dt']))
            print("     Delta_Lambda       = {:.4f} grados".format(r['dL']))
            print("     --- TU RESULTADO ---")
            print("     omega_exp          = {:.4f} grados/dia  (DeltaL / Delta_t)".format(r['omega_exp']))
            print("     T_sidereo          = {:.3f} dias        (360 / omega_exp)".format(r['T_sid']))
            print("     Latitud media      = {:+.4f} grados".format(r['phi']))
            print("     --- COMPARACION TEORICA ---")
            print("     omega_Carrington   = {:.4f} grados/dia  ({:.3f}+({:.3f})*sin^2({:.2f} deg))".format(
                r['w_carr'], CARRINGTON_A, CARRINGTON_B, r['phi']))
            print("     T_sid Carrington   = {:.3f} dias".format(360.0 / r['w_carr']))
            print("     omega_Faye         = {:.4f} grados/dia  ({:.3f}+({:.3f})*sin^2({:.2f} deg))".format(
                r['w_faye'], FAYE_A, FAYE_B, r['phi']))
            print("     T_sid Faye         = {:.3f} dias".format(360.0 / r['w_faye']))
            if r['w_carr'] != 0:
                print("     Dif. vs Carring.   = {:+.4f} grados/dia  ({:+.2f}%)".format(
                    r['omega_exp']-r['w_carr'],
                    100.0*(r['omega_exp']-r['w_carr'])/r['w_carr']))
            if r['w_faye'] != 0:
                print("     Dif. vs Faye       = {:+.4f} grados/dia  ({:+.2f}%)".format(
                    r['omega_exp']-r['w_faye'],
                    100.0*(r['omega_exp']-r['w_faye'])/r['w_faye']))
            print("     --- ERRORES (propagacion numerica +-{:.0f} px) ---".format(DELTA_PX))
            print("     Cadena: (px,py)->dx,dy->rho,theta_m->phi_M,lambda_M->L->Phi,Lambda->T")
            # sigma Lambda obs 1
            if r['sL1'] is not None:
                print("     sigma_Lambda (obs1)    = {:.4f} deg  <- (1/2)*sqrt(dLx1^2+dLy1^2)".format(r['sL1']))
            else:
                print("     sigma_Lambda (obs1)    = N/D  (faltan pixel_x/y o datos obs en BD)")
            # sigma Lambda obs 2
            if r['sL2'] is not None:
                print("     sigma_Lambda (obs2)    = {:.4f} deg".format(r['sL2']))
            else:
                print("     sigma_Lambda (obs2)    = N/D")
            # sigma DeltaLambda y sigma_T (Metodo 1 puro: prop. pixeles)
            if r['sigma_dL'] is not None:
                print("     sigma_DeltaLambda      = {:.4f} deg  <- sqrt(sL1^2+sL2^2)".format(r['sigma_dL']))
                print("     sigma_T_sidereo        = {:.4f} dias <- T*sigma_dL/DeltaL  (BARRA HORIZ. GRAFICO)".format(r['sigma_T']))
                print("     sigma_omega_exp        = {:.6f} deg/dia".format(r['sigma_omega']))
            else:
                print("     sigma_T_sidereo        = N/D")
            # --- METODO 1 MEJORADO (extremos + residuos, mismo para todo el grupo) ---
            if r.get('sigma_T_mejorado') is not None:
                print("     --- METODO 1 MEJORADO (extremos + residuos sobre {} dias del grupo) ---".format(r['n_obs_g']))
                print("     omega_extremos         = {:.4f} grados/dia  ((L_N-L_1)/(t_N-t_1))".format(r['omega_ext_grupo']))
                print("     T_sid extremos         = {:.3f} dias        (360/omega_extremos)".format(r['T_ext_grupo']))
                print("     S_Lambda residuos      = {:.4f} deg  <- desv.tip. de los residuos r_i".format(r['S_L_resid_grupo']))
                print("     sigma_T_mejorado       = {:.4f} dias <- T*sqrt(2)*S_Lambda/|DeltaLambda|".format(r['sigma_T_mejorado']))
            # sigma Phi obs 1 y 2
            if r['sPhi1_num'] is not None:
                print("     sigma_Phi (obs1)       = {:.4f} deg  <- (1/2)*sqrt(dPx1^2+dPy1^2)".format(r['sPhi1_num']))
            if r['sPhi2_num'] is not None:
                print("     sigma_Phi (obs2)       = {:.4f} deg".format(r['sPhi2_num']))
            # sigma Phi media -> barra vertical
            if r['sigma_phi_num_media'] is not None and r['sPhi1_num'] is not None:
                print("     sigma_Phi_media        = {:.4f} deg  <- (1/2)*sqrt(sPhi1^2+sPhi2^2)  (BARRA VERT. GRAFICO)".format(
                    r['sigma_phi_num_media']))
            elif r['sigma_phi_num_media'] is not None:
                print("     sigma_Phi_media        = {:.4f} deg  (BARRA VERT. GRAFICO)".format(
                    r['sigma_phi_num_media']))
            # desviacion tipica muestral (informativa)
            if r['sigma_phi_muestra'] is not None:
                print("     sigma_Phi muestral     = {:.4f} deg  <- desv.tip. de {} obs  (informativo)".format(
                    r['sigma_phi_muestra'], r['n_obs_g']))
    else:
        print()
        print("   [!] No hay manchas con 2 o mas observaciones en la BD.")
        print("       Usa el mismo ID de mancha en fotos de dias distintos (modo f).")

    # --------------------------------------------------------------
    # RESUMEN METODO 1 MEJORADO POR MANCHA (un solo T por mancha)
    # --------------------------------------------------------------
    grupos_mej = [(g, m) for g, m in metodo1_mej_grp.items() if m is not None]
    if grupos_mej:
        print()
        print("   " + "="*100)
        print("   METODO 1 MEJORADO - UN SOLO PERIODO POR MANCHA (extremos + residuos sobre todos los dias)")
        print("   " + "="*100)
        print("   {:<8} {:>4} {:>10} {:>10} {:>12} {:>12} {:>10} {:>10}".format(
            "Mancha", "N", "Phi(deg)", "DeltaL", "omega_ext", "T_ext(d)", "S_Lam(deg)", "sigT(d)"))
        print("   " + "-"*100)
        for id_grupo, m in sorted(grupos_mej):
            print("   {:<8} {:>4d} {:>+10.4f} {:>12.4f} {:>12.4f} {:>10.3f} {:>10.4f} {:>10.4f}".format(
                str(id_grupo), m['N'], m['phi_media'], m['dL_tot'],
                m['omega_ext'], m['T_ext'], m['S_L_resid'], m['sigma_T_mej']))
        print("   " + "-"*100)
        print("   Cada fila = UN punto del grafico Phi vs T (mancha unica con barra de error horizontal sigT).")

    if advertencias:
        print()
        print("   AVISOS:")
        for a in advertencias:
            print(a)

    if not resultados:
        return

    # ==================================================
    # GRAFICA DE BIGOTES (errorbar) — UN PUNTO POR MANCHA
    # Eje X = periodo o velocidad angular
    # Eje Y = latitud heliografica (Phi media)
    # Barras horizontales = sigma_T (Metodo 1 mejorado si N>=3, propag. pixeles si N=2)
    # Barras verticales   = sigma_Phi muestral (desviacion tipica de las Phi del grupo)
    # ==================================================
    if not TIENE_MPL:
        print("\n   [!] matplotlib no instalado: pip install matplotlib")
        return

    # Umbrales fisicos del Sol: rota en 22-32 dias en cualquier latitud
    # (ecuador ~25 d, polos ~32 d). Fuera de ese rango = mancha mal medida.
    T_SOSPECHOSO_MAX = 32.0   # dias
    T_SOSPECHOSO_MIN = 22.0   # dias

    # ----------------------------------------------------------------
    # Construir UN punto por mancha (15 manchas -> 15 puntos)
    # ----------------------------------------------------------------
    def _sigma_T_grupo(id_grupo):
        m = metodo1_mej_grp.get(id_grupo)
        if m is not None and m.get('sigma_T_mej') is not None:
            return m['sigma_T_mej']
        pares_g = [r for r in resultados if r['grupo'] == id_grupo]
        if pares_g and pares_g[0]['sigma_T'] is not None:
            return pares_g[0]['sigma_T']
        return None

    # sigma_Phi promediado por propagacion de pixeles para cada grupo
    # (recolecta los sPhi1_num y sPhi2_num de todos los pares del grupo)
    sigma_phi_prop_grp = {}
    for r in resultados:
        g = r['grupo']
        sigma_phi_prop_grp.setdefault(g, [])
        if r.get('sPhi1_num') is not None:
            sigma_phi_prop_grp[g].append(r['sPhi1_num'])
        if r.get('sPhi2_num') is not None:
            sigma_phi_prop_grp[g].append(r['sPhi2_num'])
    sigma_phi_prop_avg = {}
    for g, vals in sigma_phi_prop_grp.items():
        sigma_phi_prop_avg[g] = (sum(vals) / len(vals)) if vals else None

    puntos_mancha = []
    for id_grupo, obs in sorted(grupos.items()):
        n_g = len(obs)
        if n_g < 2:
            continue
        # Phi media + S_phi (desviacion tipica muestral)
        phis_g  = [o[1] for o in obs]
        phi_med = sum(phis_g) / n_g
        S_phi_muestral = sigma_phi_muestra_grp.get(id_grupo) or 0.0
        S_phi_propaga  = sigma_phi_prop_avg.get(id_grupo)   or 0.0
        # Usamos el MAX de los dos (mas conservador y siempre visible en el grafico)
        S_phi = max(S_phi_muestral, S_phi_propaga)
        # T y omega por extremos (con unwrap de Lambda)
        fechas_g = [o[0] for o in obs]
        Ls_g     = [o[2] for o in obs]
        ts_g     = [fecha_a_dias(f) for f in fechas_g]
        if any(t is None for t in ts_g):
            continue
        pares_t = sorted(zip(ts_g, Ls_g), key=lambda p: p[0])
        t1_g, tN_g = pares_t[0][0],  pares_t[-1][0]
        L1_g, LN_g = pares_t[0][1],  pares_t[-1][1]
        dt_g = tN_g - t1_g
        if dt_g <= 0:
            continue
        dL_g = delta_longitud_real(L1_g, LN_g, dt_g)
        if abs(dL_g) < 0.1:
            continue
        omega_g = dL_g / dt_g
        T_g     = 360.0 / omega_g
        sigma_T_g = _sigma_T_grupo(id_grupo)
        if sigma_T_g is None:
            sigma_T_g = 0.0
        sigma_omega_g = abs(omega_g) * sigma_T_g / T_g if T_g != 0 else 0.0

        puntos_mancha.append({
            'grupo'      : id_grupo,
            'N'          : n_g,
            'phi'        : phi_med,
            'T_sid'      : T_g,
            'omega_exp'  : omega_g,
            'sigma_T'    : sigma_T_g,
            'sigma_omega': sigma_omega_g,
            'sigma_phi_num_media' : S_phi,
            'S_phi_muestral'      : S_phi_muestral,
            'S_phi_propaga'       : S_phi_propaga,
            'metodo'     : 'M1 mejorado' if n_g >= 3 else 'M1 puro (N=2)',
        })

    if not puntos_mancha:
        print("\n   [!] No hay manchas validas para el grafico (necesitas al menos 2 obs).")
        return

    print("\n   " + "="*100)
    print("   GRAFICO Phi vs T : {} mancha(s) -> {} punto(s)".format(
        len(puntos_mancha), len(puntos_mancha)))
    print("   " + "="*100)
    for p in puntos_mancha:
        print("     M{:<4} N={:<2}  Phi={:+7.3f}+-{:.3f} deg  (S_muestral={:.3f}, S_prop={:.3f})   T={:7.3f}+-{:.3f} d   ({})".format(
            p['grupo'], p['N'], p['phi'], p['sigma_phi_num_media'],
            p['S_phi_muestral'], p['S_phi_propaga'],
            p['T_sid'], p['sigma_T'], p['metodo']))

    def _v(lst, key, fallback=0.0):
        return [x[key] if x[key] is not None else fallback for x in lst]

    def es_sospechoso(r):
        t = r['T_sid']
        return t > T_SOSPECHOSO_MAX or t < T_SOSPECHOSO_MIN

    # ================================================================
    # AJUSTE PROPIO POR MINIMOS CUADRADOS PONDERADOS
    # Modelo: omega(Phi) = A + B * sin^2(Phi)
    #   Cambio de variable: x_i = sin^2(Phi_i), y_i = omega_i
    #   Pesos: w_i = 1 / sigma_omega_i^2
    #   Solucion cerrada (Bevington):
    #     S    = sum(w_i)
    #     S_x  = sum(w_i * x_i)
    #     S_y  = sum(w_i * y_i)
    #     S_xx = sum(w_i * x_i^2)
    #     S_xy = sum(w_i * x_i * y_i)
    #     Delta = S * S_xx - S_x^2
    #     A      = (S_xx * S_y - S_x * S_xy) / Delta
    #     B      = (S * S_xy - S_x * S_y)   / Delta
    #     sigA   = sqrt( S_xx / Delta )
    #     sigB   = sqrt( S    / Delta )
    #   Solo se usan manchas con sigma_omega > 0 y T en rango fisico.
    # ================================================================
    A_fit = B_fit = sigA_fit = sigB_fit = chi2_red = None
    N_fit_used = 0
    fit_aplicado = False

    # ----------------------------------------------------------------
    # AJUSTE MINIMOS CUADRADOS NO PONDERADO (todos los puntos pesan igual)
    #
    # Por que NO ponderado:
    #   - Las sigma_T_mej son artificialmente pequenas en grupos con muchas
    #     observaciones bien alineadas (residuos ~ 0). Eso les daria peso
    #     1/sigma^2 enorme y dominarian el ajuste, sesgando A y B.
    #   - Las sigma de N=2 son por propagacion de +-5 px y son mas grandes,
    #     asi que pesan poco. Las manchas con mas datos NO son "mas precisas"
    #     en sentido fisico, solo estan mejor ajustadas a una recta.
    #   - Conclusion: el ajuste no ponderado es el correcto cuando las
    #     incertidumbres reales no estan calibradas.
    # ----------------------------------------------------------------
    puntos_fit = [r for r in puntos_mancha if not es_sospechoso(r)]
    N_fit_used = len(puntos_fit)

    if N_fit_used >= 2:
        N    = N_fit_used
        Sx   = 0.0; Sy = 0.0; Sxx = 0.0; Sxy = 0.0
        for r in puntos_fit:
            xi = sin(radians(r['phi']))**2
            yi = r['omega_exp']
            Sx  += xi
            Sy  += yi
            Sxx += xi * xi
            Sxy += xi * yi
        Delta = N * Sxx - Sx * Sx
        if abs(Delta) > 1e-15:
            A_fit = (Sxx * Sy  - Sx * Sxy) / Delta
            B_fit = (N   * Sxy - Sx * Sy ) / Delta
            # Errores estandar (Bevington para no ponderado): sigma^2 viene
            # de los residuos:
            #   s^2 = sum((yi - A - B*xi)^2) / (N-2)
            #   sigA = sqrt(s^2 * Sxx / Delta)
            #   sigB = sqrt(s^2 * N   / Delta)
            if N - 2 > 0:
                ss = 0.0
                for r in puntos_fit:
                    xi   = sin(radians(r['phi']))**2
                    pred = A_fit + B_fit * xi
                    ss  += (r['omega_exp'] - pred) ** 2
                s2       = ss / (N - 2)
                sigA_fit = sqrt(s2 * Sxx / Delta)
                sigB_fit = sqrt(s2 * N   / Delta)
                chi2_red = s2   # con pesos uniformes, chi^2/dof = s^2
            else:
                # N=2: ajuste pasa exactamente por los 2 puntos, sin errores
                sigA_fit = 0.0
                sigB_fit = 0.0
                chi2_red = None
            fit_aplicado = True

    print()
    print("   " + "="*100)
    print("   AJUSTE PROPIO POR MINIMOS CUADRADOS NO PONDERADO")
    print("   omega(Phi) = A + B * sin^2(Phi)   (omega SIDEREO)")
    print("   " + "="*100)
    if fit_aplicado:
        print("   N = {} manchas usadas (incluyendo todas las no sospechosas)".format(N_fit_used))
        print("   A_exp = {:+.4f} +- {:.4f}  grados/dia".format(A_fit, sigA_fit))
        print("   B_exp = {:+.4f} +- {:.4f}  grados/dia".format(B_fit, sigB_fit))
        if chi2_red is not None:
            cal = ("OK (cerca de 1)" if 0.5 < chi2_red < 2.0
                   else ("subestimacion de errores" if chi2_red > 2 else "sobreestimacion de errores"))
            print("   chi^2 reducido = {:.3f}   [{}]".format(chi2_red, cal))
        else:
            print("   chi^2 no calculable (N = 2, 0 grados de libertad).")
    else:
        print("   [!] No hay datos suficientes para el ajuste (necesitas >= 2 manchas validas).")
    print()
    # Tabla de comparacion con la literatura
    print("   {:<18} {:>14} {:>16}".format("Modelo", "A (grad/dia)", "B (grad/dia)"))
    print("   " + "-"*52)
    print("   {:<18} {:>14.3f} {:>16.3f}".format("Carrington (1863)", CARRINGTON_A, CARRINGTON_B))
    print("   {:<18} {:>14.3f} {:>16.3f}".format("Faye (1865)",       FAYE_A,       FAYE_B))
    if fit_aplicado:
        print("   {:<18} {:>5.3f} +- {:5.3f}  {:>7.3f} +- {:5.3f}".format(
            "Tu ajuste", A_fit, sigA_fit, B_fit, sigB_fit))
        # Interpretacion automatica
        print()
        difA_carr = abs(A_fit - CARRINGTON_A); difA_faye = abs(A_fit - FAYE_A)
        difB_carr = abs(B_fit - CARRINGTON_B); difB_faye = abs(B_fit - FAYE_B)
        cerca_A = "Carrington" if difA_carr < difA_faye else "Faye"
        cerca_B = "Carrington" if difB_carr < difB_faye else "Faye"
        print("   Interpretacion automatica:")
        print("     A_exp esta mas cerca de {} (diferencia {:.3f} grad/dia)".format(
            cerca_A, min(difA_carr, difA_faye)))
        print("     B_exp esta mas cerca de {} (diferencia {:.3f} grad/dia)".format(
            cerca_B, min(difB_carr, difB_faye)))
        # Compatibilidad estadistica (2-sigma)
        comp_A_carr = difA_carr < 2 * sigA_fit
        comp_A_faye = difA_faye < 2 * sigA_fit
        comp_B_carr = difB_carr < 2 * sigB_fit
        comp_B_faye = difB_faye < 2 * sigB_fit
        if comp_A_carr or comp_A_faye:
            print("     A_exp es COMPATIBLE con la literatura dentro de 2*sigma.")
        else:
            print("     A_exp DIFIERE de ambos modelos clasicos en mas de 2*sigma.")
        if comp_B_carr or comp_B_faye:
            print("     B_exp es COMPATIBLE con la literatura dentro de 2*sigma.")
        else:
            print("     B_exp DIFIERE de ambos modelos clasicos en mas de 2*sigma.")
    print("   " + "="*100)

    # Una fila por mancha (no por par) -> normales vs sospechosos
    normales    = [r for r in puntos_mancha if not es_sospechoso(r)]
    sospechosos = [r for r in puntos_mancha if     es_sospechoso(r)]

    if sospechosos:
        print("\n   [AVISO] {} mancha(s) sospechosa(s) (T < {:.0f} d o T > {:.0f} d):".format(
              len(sospechosos), T_SOSPECHOSO_MIN, T_SOSPECHOSO_MAX))
        for r in sospechosos:
            print("     Mancha {} : T={:.1f} d  omega={:.3f} deg/d  ({})".format(
                r['grupo'], r['T_sid'], r['omega_exp'], r['metodo']))

    # Listas para errorbar
    T_n   = _v(normales,    'T_sid');     ph_n  = _v(normales,    'phi')
    om_n  = _v(normales,    'omega_exp'); lbl_n = [str(r['grupo']) for r in normales]
    sT_n  = _v(normales,    'sigma_T');   som_n = _v(normales,    'sigma_omega')
    sp_n  = _v(normales,    'sigma_phi_num_media')

    T_s   = _v(sospechosos, 'T_sid');     ph_s  = _v(sospechosos, 'phi')
    om_s  = _v(sospechosos, 'omega_exp'); lbl_s = [str(r['grupo']) for r in sospechosos]
    sT_s  = _v(sospechosos, 'sigma_T');   som_s = _v(sospechosos, 'sigma_omega')
    sp_s  = _v(sospechosos, 'sigma_phi_num_media')

    # Curvas teoricas sidereas directas: T = 360/omega
    phi_ref  = [p * 0.5 for p in range(-120, 121)]
    w_carr_r = [omega_carrington(p) for p in phi_ref]
    w_faye_r = [omega_faye(p)       for p in phi_ref]
    Tsid_c   = [360.0 / w for w in w_carr_r]
    Tsid_f   = [360.0 / w for w in w_faye_r]

    # Curva del ajuste propio: omega(Phi) = A_fit + B_fit * sin^2(Phi)
    if fit_aplicado:
        w_fit_r = [A_fit + B_fit * sin(radians(p))**2 for p in phi_ref]
        Tsid_fit = [360.0 / w for w in w_fit_r]
    else:
        w_fit_r = None
        Tsid_fit = None

    # Limites de ejes BALANCEADOS: ejes simetricos en torno al centro de
    # las manchas normales. Si una mancha extrema (M8 con omega=273) estira
    # el eje hacia un lado, se extiende lo mismo hacia el otro para que las
    # curvas teoricas (Carrington/Faye) queden en el centro del plot.
    todos_T   = [r['T_sid']     for r in puntos_mancha]
    todos_om  = [r['omega_exp'] for r in puntos_mancha]
    todos_phi = [r['phi']       for r in puntos_mancha]
    todos_sP  = [r['sigma_phi_num_media'] for r in puntos_mancha]
    # Centro = midpoint de las manchas normales (donde estan las curvas teoricas)
    _norm_T  = [r['T_sid']     for r in normales] if normales else todos_T
    _norm_om = [r['omega_exp'] for r in normales] if normales else todos_om
    T_center  = (min(_norm_T)  + max(_norm_T))  / 2.0
    om_center = (min(_norm_om) + max(_norm_om)) / 2.0
    # Half-width = la mayor distancia desde el centro a CUALQUIER mancha
    T_half  = max(abs(t - T_center)  for t in todos_T)  + 2.0
    om_half = max(abs(o - om_center) for o in todos_om) + 2.0
    T_xmin, T_xmax   = T_center  - T_half,  T_center  + T_half
    om_xmin, om_xmax = om_center - om_half, om_center + om_half
    # Y balanceado tambien: simetrico en torno a 0
    phi_max_dist = max(abs(p) for p in todos_phi) + max(todos_sP + [0]) + 15
    if phi_max_dist < 50: phi_max_dist = 50
    phi_lo, phi_hi = -phi_max_dist, phi_max_dist

    # Tamaño de figura grande para apreciar bien las curvas
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 11))
    fig.patch.set_facecolor('#f8f9ff')
    fig.subplots_adjust(wspace=0.18, left=0.06, right=0.98, bottom=0.08, top=0.92)

    # ---- SUBPLOT 1: Periodo T (X) vs Latitud Phi (Y) ----
    ax1.set_facecolor('#f0f4ff')
    ax1.plot(Tsid_c, phi_ref, 'k--', linewidth=2.6, alpha=0.65,
             label='Carrington ({:.3f}{:+.3f}sin² Φ)'.format(CARRINGTON_A, CARRINGTON_B))
    ax1.plot(Tsid_f, phi_ref, color='#c62828', linestyle=':',
             linewidth=2.6, alpha=0.85,
             label='Faye ({:.3f}{:+.3f}sin² Φ)'.format(FAYE_A, FAYE_B))
    if fit_aplicado:
        # Linea amarilla fuerte con contorno negro
        ax1.plot(Tsid_fit, phi_ref, color='#FFFF00', linestyle='-',
                 linewidth=4.5, alpha=1.0,
                 path_effects=[mpe.Stroke(linewidth=7.0, foreground='#000000'),
                               mpe.Normal()],
                 label='Tu ajuste  ({:+.3f}±{:.3f}) + ({:+.3f}±{:.3f})·sin² Φ'.format(
                     A_fit, sigA_fit, B_fit, sigB_fit))
    # Bbox blanco para que los numeros M1, M2... se lean siempre
    _BBOX_N = dict(boxstyle='round,pad=0.20', facecolor='white',
                   edgecolor='#1565c0', linewidth=0.8, alpha=0.92)
    _BBOX_S = dict(boxstyle='round,pad=0.20', facecolor='white',
                   edgecolor='#e65100', linewidth=0.8, alpha=0.92)
    if normales:
        ax1.errorbar(T_n, ph_n, xerr=sT_n, yerr=sp_n,
                     fmt='o', color='#1565c0', ecolor='#1565c0',
                     capsize=10, elinewidth=2.8, capthick=2.8,
                     markersize=12, zorder=6,
                     label='Tus manchas (1 punto/mancha, ±σ)')
        for T, phi, lbl in zip(T_n, ph_n, lbl_n):
            ax1.annotate('M'+str(lbl), (T, phi), textcoords="offset points",
                         xytext=(12, 12), fontsize=11, color='#1565c0',
                         fontweight='bold', zorder=10, bbox=_BBOX_N)
    if sospechosos:
        ax1.errorbar(T_s, ph_s, xerr=sT_s, yerr=sp_s,
                     fmt='D', color='#e65100', ecolor='#e65100',
                     capsize=10, elinewidth=2.8, capthick=2.8,
                     markersize=13, zorder=6,
                     label='Imposibles (T < {:.0f} ó T > {:.0f} d)'.format(
                         T_SOSPECHOSO_MIN, T_SOSPECHOSO_MAX))
        for T, phi, lbl in zip(T_s, ph_s, lbl_s):
            ax1.annotate('M'+str(lbl), (T, phi), textcoords="offset points",
                         xytext=(12, 12), fontsize=11, color='#e65100',
                         fontweight='bold', zorder=10, bbox=_BBOX_S)
    ax1.axhline(0, color='#888', linewidth=1.0, linestyle=':', alpha=0.6)
    ax1.set_xlabel('Periodo Sidéreo  (días)', fontsize=15, fontweight='bold')
    ax1.set_ylabel('Latitud Heliográfica  Φ  (grados)', fontsize=15, fontweight='bold')
    ax1.set_title('Periodo Sidéreo vs Latitud\n(1 punto por mancha — Método 1 mejorado)',
                  fontsize=15, fontweight='bold', color='#1a237e')
    ax1.legend(fontsize=11, loc='upper right', framealpha=0.95)
    ax1.grid(True, alpha=0.4, color='white', linewidth=1.2)
    ax1.tick_params(axis='both', which='major', labelsize=12, length=6, width=1.2)
    ax1.set_ylim(phi_lo, phi_hi)
    ax1.set_xlim(T_xmin, T_xmax)

    # ---- SUBPLOT 2: omega (X) vs Latitud Phi (Y) ----
    ax2.set_facecolor('#f0f4ff')
    ax2.plot(w_carr_r, phi_ref, 'k--', linewidth=2.6, alpha=0.65,
             label='Carrington ({:.3f}{:+.3f}sin² Φ)'.format(CARRINGTON_A, CARRINGTON_B))
    ax2.plot(w_faye_r, phi_ref, color='#c62828', linestyle=':',
             linewidth=2.6, alpha=0.85,
             label='Faye ({:.3f}{:+.3f}sin² Φ)'.format(FAYE_A, FAYE_B))
    if fit_aplicado:
        ax2.plot(w_fit_r, phi_ref, color='#FFFF00', linestyle='-',
                 linewidth=4.5, alpha=1.0,
                 path_effects=[mpe.Stroke(linewidth=7.0, foreground='#000000'),
                               mpe.Normal()],
                 label='Tu ajuste  ({:+.3f}±{:.3f}) + ({:+.3f}±{:.3f})·sin² Φ'.format(
                     A_fit, sigA_fit, B_fit, sigB_fit))
    _BBOX_N2 = dict(boxstyle='round,pad=0.20', facecolor='white',
                    edgecolor='#2e7d32', linewidth=0.8, alpha=0.92)
    if normales:
        ax2.errorbar(om_n, ph_n, xerr=som_n, yerr=sp_n,
                     fmt='o', color='#2e7d32', ecolor='#2e7d32',
                     capsize=10, elinewidth=2.8, capthick=2.8,
                     markersize=12, zorder=6,
                     label='Tus manchas (1 punto/mancha, ±σ)')
        for w, phi, lbl in zip(om_n, ph_n, lbl_n):
            ax2.annotate('M'+str(lbl), (w, phi), textcoords="offset points",
                         xytext=(12, 12), fontsize=11, color='#2e7d32',
                         fontweight='bold', zorder=10, bbox=_BBOX_N2)
    if sospechosos:
        ax2.errorbar(om_s, ph_s, xerr=som_s, yerr=sp_s,
                     fmt='D', color='#e65100', ecolor='#e65100',
                     capsize=10, elinewidth=2.8, capthick=2.8,
                     markersize=13, zorder=6,
                     label='Imposibles')
        for w, phi, lbl in zip(om_s, ph_s, lbl_s):
            ax2.annotate('M'+str(lbl), (w, phi), textcoords="offset points",
                         xytext=(12, 12), fontsize=11, color='#e65100',
                         fontweight='bold', zorder=10, bbox=_BBOX_S)
    ax2.axhline(0, color='#888', linewidth=1.0, linestyle=':', alpha=0.6)
    ax2.set_xlabel('Velocidad Angular  ω  (grados/día)', fontsize=15, fontweight='bold')
    ax2.set_ylabel('Latitud Heliográfica  Φ  (grados)', fontsize=15, fontweight='bold')
    ax2.set_title('Velocidad Angular vs Latitud\n(1 punto por mancha — Ley de Faye / Carrington)',
                  fontsize=15, fontweight='bold', color='#1a237e')
    ax2.legend(fontsize=11, loc='upper right', framealpha=0.95)
    ax2.grid(True, alpha=0.4, color='white', linewidth=1.2)
    ax2.tick_params(axis='both', which='major', labelsize=12, length=6, width=1.2)
    ax2.set_ylim(phi_lo, phi_hi)
    ax2.set_xlim(om_xmin, om_xmax)

    ruta_grafica = os.path.join(CARPETA_TFG, 'figuras', 'rotacion_solar.png')
    plt.savefig(ruta_grafica, dpi=150, bbox_inches='tight')
    print("\n   [OK] Grafica PNG guardada en: {}".format(ruta_grafica))

    # ================================================================
    # GRAFICA INTERACTIVA con Plotly (HTML que se abre en el navegador)
    # Zoom con la rueda, arrastras para mover, doble-click reset,
    # pasas el raton por cada mancha para ver sus datos.
    # ================================================================
    try:
        import plotly.graph_objects as _pgo
        from plotly.subplots import make_subplots as _msp
        _fig_html = _msp(rows=1, cols=2,
                         subplot_titles=('Periodo Sidereo vs Latitud',
                                         'Velocidad Angular vs Latitud'),
                         horizontal_spacing=0.10)
        # ---- Curvas teoricas ----
        _fig_html.add_trace(_pgo.Scatter(
            x=Tsid_c, y=phi_ref, mode='lines',
            line=dict(color='black', dash='dash', width=2.5),
            name='Carrington ({:.3f}{:+.3f}sin²Φ)'.format(CARRINGTON_A, CARRINGTON_B),
            legendgroup='carr'), row=1, col=1)
        _fig_html.add_trace(_pgo.Scatter(
            x=Tsid_f, y=phi_ref, mode='lines',
            line=dict(color='#c62828', dash='dot', width=2.5),
            name='Faye ({:.3f}{:+.3f}sin²Φ)'.format(FAYE_A, FAYE_B),
            legendgroup='faye'), row=1, col=1)
        if fit_aplicado:
            _fig_html.add_trace(_pgo.Scatter(
                x=Tsid_fit, y=phi_ref, mode='lines',
                line=dict(color='#FFCC00', width=5),
                name='Tu ajuste ({:+.3f}±{:.3f}) + ({:+.3f}±{:.3f})·sin²Φ'.format(
                    A_fit, sigA_fit, B_fit, sigB_fit),
                legendgroup='fit'), row=1, col=1)
        _fig_html.add_trace(_pgo.Scatter(
            x=w_carr_r, y=phi_ref, mode='lines',
            line=dict(color='black', dash='dash', width=2.5),
            name='Carrington', legendgroup='carr', showlegend=False),
            row=1, col=2)
        _fig_html.add_trace(_pgo.Scatter(
            x=w_faye_r, y=phi_ref, mode='lines',
            line=dict(color='#c62828', dash='dot', width=2.5),
            name='Faye', legendgroup='faye', showlegend=False),
            row=1, col=2)
        if fit_aplicado:
            _fig_html.add_trace(_pgo.Scatter(
                x=w_fit_r, y=phi_ref, mode='lines',
                line=dict(color='#FFCC00', width=5),
                name='Tu ajuste', legendgroup='fit', showlegend=False),
                row=1, col=2)

        # ---- Manchas normales con hovertext detallado ----
        def _hov(r):
            return ("<b>M" + str(r['grupo']) + "</b><br>"
                    "Φ = {:+.3f}°<br>"
                    "ω = {:.4f} °/d<br>"
                    "T = {:.3f} d<br>"
                    "N_obs = {}<br>"
                    "σ_T = ±{:.3f} d<br>"
                    "σ_Φ = ±{:.3f}°"
                    .format(r['phi'], r['omega_exp'], r['T_sid'], r['N'],
                            r['sigma_T'] or 0, r['sigma_phi_num_media'] or 0))
        if normales:
            _hovN = [_hov(r) for r in normales]
            _fig_html.add_trace(_pgo.Scatter(
                x=T_n, y=ph_n, mode='markers+text',
                marker=dict(color='#1565c0', size=12,
                            line=dict(color='white', width=1.5)),
                error_x=dict(type='data', array=sT_n, color='#1565c0', thickness=2),
                error_y=dict(type='data', array=sp_n, color='#1565c0', thickness=2),
                text=['M'+str(l) for l in lbl_n],
                textposition='top center',
                textfont=dict(color='#1565c0', size=11),
                hovertext=_hovN, hoverinfo='text',
                name='Tus manchas (±σ)'), row=1, col=1)
            _fig_html.add_trace(_pgo.Scatter(
                x=om_n, y=ph_n, mode='markers+text',
                marker=dict(color='#2e7d32', size=12,
                            line=dict(color='white', width=1.5)),
                error_x=dict(type='data', array=som_n, color='#2e7d32', thickness=2),
                error_y=dict(type='data', array=sp_n, color='#2e7d32', thickness=2),
                text=['M'+str(l) for l in lbl_n],
                textposition='top center',
                textfont=dict(color='#2e7d32', size=11),
                hovertext=_hovN, hoverinfo='text',
                name='Tus manchas (±σ)', showlegend=False), row=1, col=2)
        if sospechosos:
            _hovS = [_hov(r) for r in sospechosos]
            _fig_html.add_trace(_pgo.Scatter(
                x=T_s, y=ph_s, mode='markers+text',
                marker=dict(color='#e65100', size=14, symbol='diamond',
                            line=dict(color='white', width=1.5)),
                error_x=dict(type='data', array=sT_s, color='#e65100', thickness=2),
                error_y=dict(type='data', array=sp_s, color='#e65100', thickness=2),
                text=['M'+str(l) for l in lbl_s],
                textposition='top center',
                textfont=dict(color='#e65100', size=11),
                hovertext=_hovS, hoverinfo='text',
                name='Imposibles (T<{:.0f} o T>{:.0f}d)'.format(
                    T_SOSPECHOSO_MIN, T_SOSPECHOSO_MAX)), row=1, col=1)
            _fig_html.add_trace(_pgo.Scatter(
                x=om_s, y=ph_s, mode='markers+text',
                marker=dict(color='#e65100', size=14, symbol='diamond',
                            line=dict(color='white', width=1.5)),
                error_x=dict(type='data', array=som_s, color='#e65100', thickness=2),
                error_y=dict(type='data', array=sp_s, color='#e65100', thickness=2),
                text=['M'+str(l) for l in lbl_s],
                textposition='top center',
                textfont=dict(color='#e65100', size=11),
                hovertext=_hovS, hoverinfo='text',
                name='Imposibles', showlegend=False), row=1, col=2)

        # ============================================================
        # RANGOS POR DEFECTO: ajustados al CLUSTER de manchas normales
        # para que la CURVATURA de Carrington/Faye se vea bien desde el
        # principio. Las manchas imposibles (M8 con omega=273) caen fuera
        # pero el usuario puede alejarse con la rueda para verlas.
        #
        # IMPORTANTE: cada eje se puede estirar/encoger por separado:
        #   - Arrastra DENTRO de la grafica = mueve toda la vista
        #   - Arrastra sobre el EJE X (linea de abajo) = estira solo X
        #   - Arrastra sobre el EJE Y (linea de la izq.) = estira solo Y
        #   - Doble-click = reset
        # ============================================================
        _norm_T_  = [r['T_sid']     for r in normales] if normales else todos_T
        _norm_om_ = [r['omega_exp'] for r in normales] if normales else todos_om
        _norm_ph_ = [r['phi']       for r in normales] if normales else todos_phi
        _T_def_min  = min(_norm_T_) - 2.0
        _T_def_max  = max(_norm_T_) + 2.0
        _om_def_min = min(_norm_om_) - 0.8
        _om_def_max = max(_norm_om_) + 0.8
        _ph_def_min = min(_norm_ph_) - 8.0
        _ph_def_max = max(_norm_ph_) + 8.0
        if _ph_def_min > -35: _ph_def_min = -35
        if _ph_def_max <  35: _ph_def_max =  35

        _AX_KW = dict(gridcolor='#dddddd', showspikes=True,
                      spikecolor='#aaa', spikethickness=1, spikedash='dot',
                      automargin=True)
        _fig_html.update_xaxes(title_text='<b>Periodo Sidereo  T  (dias)</b>',
                               range=[_T_def_min, _T_def_max], row=1, col=1,
                               zeroline=False, **_AX_KW)
        _fig_html.update_xaxes(title_text='<b>Velocidad Angular  ω  (grados/dia)</b>',
                               range=[_om_def_min, _om_def_max], row=1, col=2,
                               zeroline=False, **_AX_KW)
        _fig_html.update_yaxes(title_text='<b>Latitud Heliografica  Φ  (grados)</b>',
                               range=[_ph_def_min, _ph_def_max], row=1, col=1,
                               zeroline=True, zerolinecolor='#888', **_AX_KW)
        _fig_html.update_yaxes(title_text='<b>Latitud Heliografica  Φ  (grados)</b>',
                               range=[_ph_def_min, _ph_def_max], row=1, col=2,
                               zeroline=True, zerolinecolor='#888', **_AX_KW)
        _fig_html.update_layout(
            title=dict(
                text=('<b>Rotacion Diferencial Solar</b><br>'
                      '<sub>Rueda = zoom · Arrastra DENTRO = mover · '
                      '<b>Arrastra sobre el EJE X o Y = estira solo ese eje</b> · '
                      'Doble-click = reset · '
                      'Hover sobre manchas = ver datos</sub>'),
                x=0.5, font=dict(size=16, color='#1a237e')),
            plot_bgcolor='#fafbff', paper_bgcolor='#ffffff',
            font=dict(family='Arial', size=12),
            height=820, hovermode='closest',
            dragmode='pan',   # Por defecto arrastra para mover (en vez de zoom-rectangulo)
            legend=dict(orientation='h', yanchor='bottom', y=-0.22,
                        xanchor='center', x=0.5,
                        bgcolor='rgba(255,255,255,0.9)',
                        bordercolor='#bbbbbb', borderwidth=1))
        # Activar zoom con rueda en AMBOS ejes de los dos subplots
        _fig_html.update_xaxes(fixedrange=False, row=1, col=1)
        _fig_html.update_xaxes(fixedrange=False, row=1, col=2)
        _fig_html.update_yaxes(fixedrange=False, row=1, col=1)
        _fig_html.update_yaxes(fixedrange=False, row=1, col=2)

        # Configuracion explicita de los botones interactivos
        _config_html = {
            'scrollZoom'           : True,       # <-- ZOOM CON LA RUEDA
            'displayModeBar'       : True,       # Barra siempre visible
            'displaylogo'          : False,
            'modeBarButtonsToAdd'  : ['drawline', 'drawopenpath', 'drawrect',
                                       'eraseshape'],
            'toImageButtonOptions' : {'format': 'png',
                                      'filename': 'rotacion_solar',
                                      'height': 800, 'width': 1600,
                                      'scale': 2},
        }
        ruta_html = os.path.join(CARPETA_TFG, 'figuras', 'rotacion_solar.html')
        _fig_html.write_html(ruta_html, include_plotlyjs='cdn',
                             auto_open=True, config=_config_html)
        print("   [OK] Grafica INTERACTIVA guardada en: {}".format(ruta_html))
        print("        Rueda = zoom  ·  Arrastra = mover  ·  Doble-click = reset")
        print("        Iconos arriba-derecha: lupa, casa (reset), camara (descargar PNG)")
    except ImportError:
        print("   [!] plotly no instalado (pip install plotly) -> sin version interactiva")
    except Exception as _e:
        print("   [!] No se pudo generar la grafica interactiva: {}".format(_e))

    plt.show()

# ==================================================
# MENU
# ==================================================
def ask_mode():
    print("\n" + "="*40)
    print("      CALCULO PRINCIPAL - TFG (MANCHAS SOLARES)")
    print("="*40)
    print("a) Horizontales -> Ecuatoriales")
    print("b) Ecuatoriales -> Horizontales")
    print("c) Eclipticas -> Ecuatoriales")
    print("d) Ecuatoriales -> Eclipticas")
    print("e) Sol (mu y Az_pi)")
    print("f) Manchas Solares (Calculo Detallado + BD)")
    print("g) Gestor Base de Datos (Modo Web UI)")
    print("h) Distancia entre Manchas (Triangulo Esferico)")
    print("i) Rotacion Solar (Periodo Sidereo vs Latitud + Grafica)")
    print("q) Salir")
    res = input("Tu eleccion: ").strip().lower()
    return res[:1] if len(res) > 0 else ""

# ==================================================
# MAIN
# ==================================================
def main():
    conn = inicializar_bd()
    while True:
        mode = ask_mode()
        if mode == 'q' or mode == '': break

        if mode == 'a':
            phi   = input_dms("Latitud Observador (phi)")
            Az    = input_dms("Azimut (Sur=0, Oeste+)")
            h     = input_dms("Altura (h)")
            theta = input_hms("Hora Siderea Local (theta)")
            delta, H = solve_inverse_horizontal(phi, h, Az)
            alpha = theta - H
            l_sol, _ = solve_equatorial_to_ecliptic(alpha, delta, EPSILON_J2000)
            print("\n=== RESULTADOS MODO A ===")
            print("1. Altura (h):                  {}".format(fmt_dms(degrees(h))))
            print("2. Azimut (Az):                 {}".format(fmt_dms(degrees(Az))))
            print("3. Angulo Horario (H):           {}".format(fmt_hms(degrees(H)/15.0)))
            print("4. Ascension Recta (alpha):      {}".format(fmt_hms(wrap_0_24(degrees(alpha)/15.0))))
            print("5. Declinacion (delta):          {}".format(fmt_dms(degrees(delta))))
            print("6. Long. Eclipt. Sol (lambda):   {}".format(fmt_dms(wrap_0_360(degrees(l_sol)))))

        elif mode == 'b':
            phi   = input_dms("Latitud Observador (phi)")
            alpha = input_hms("Ascension Recta (alpha)")
            delta = input_dms("Declinacion (delta)")
            theta = input_hms("Hora Siderea Local (theta)")
            H = theta - alpha
            h_out, Az_out = solve_direct_equatorial(phi, delta, H)
            l_sol, _ = solve_equatorial_to_ecliptic(alpha, delta, EPSILON_J2000)
            print("\n=== RESULTADOS MODO B ===")
            print("1. Angulo Horario (H):           {}".format(fmt_hms(degrees(H)/15.0)))
            print("2. Altura calculada (h):         {}".format(fmt_dms(degrees(h_out))))
            print("3. Azimut (Az) [+-180]:          {}".format(fmt_dms(wrap_pm180(degrees(Az_out)))))
            print("4. Long. Eclipt. Sol (lambda):   {}".format(fmt_dms(wrap_0_360(degrees(l_sol)))))

        elif mode == 'c':
            lmb  = input_dms("Longitud Eclipt. (lambda)")
            beta = input_dms("Latitud Eclipt. (beta)")
            alpha, delta = solve_ecliptic_to_equatorial(lmb, beta, EPSILON_J2000)
            print("\n=== RESULTADOS MODO C ===")
            print("1. Ascension Recta (alpha):  {}".format(fmt_hms(wrap_0_24(degrees(alpha)/15.0))))
            print("2. Declinacion (delta):      {}".format(fmt_dms(degrees(delta))))

        elif mode == 'd':
            alpha = input_hms("Ascension Recta (alpha)")
            delta = input_dms("Declinacion (delta)")
            lmb, beta = solve_equatorial_to_ecliptic(alpha, delta, EPSILON_J2000)
            print("\n=== RESULTADOS MODO D ===")
            print("1. Long. Eclipt. (lambda) [0,360]:  {}".format(fmt_dms(wrap_0_360(degrees(lmb)))))
            print("2. Long. Eclipt. (lambda) [+-180]:  {}".format(fmt_dms(wrap_pm180(degrees(lmb)))))
            print("3. Latitud Eclipt. (beta):          {}".format(fmt_dms(degrees(beta))))

        elif mode == 'e':
            phi_obs = input_dms("Latitud Observador (phi)")
            dec_e   = input_dms("Declinacion Sol (delta)")
            alpha_e = input_hms("Ascension Recta Sol (alpha)")
            theta   = input_hms("Hora Siderea Local (theta)")
            H_e = theta - alpha_e
            h_c, az_s_e = solve_direct_equatorial(phi_obs, dec_e, H_e)
            mu_v, az_p = solve_mu_and_azpi(phi_obs, theta, h_c, EPSILON_J2000)
            l_sol_e, _ = solve_equatorial_to_ecliptic(alpha_e, dec_e, EPSILON_J2000)
            api = wrap_pm180(degrees(az_p))
            az_sun = wrap_pm180(degrees(az_s_e))
            # Transformacion simulador: Api>0 (Oeste) -> Bpi negativo; Api<0 (Este) -> Bpi positivo
            if api > 0:
                bpi = -(180.0 - api)
            elif api < 0:
                bpi = 180.0 + api
            else:
                bpi = 0.0
            if bpi > az_sun:
                mu_signed = -abs(mu_v)
                signo_txt = "Negativo (-): Pi a la derecha (Este) del Sol"
            elif bpi < az_sun:
                mu_signed = abs(mu_v)
                signo_txt = "Positivo (+): Pi a la izquierda (Oeste) del Sol"
            else:
                mu_signed = 0.0
                signo_txt = "Cero (0): alineados en el mismo meridiano"
            print("\n=== RESULTADOS MODO E ===")
            print("1. Altura Sol (h):                  {}".format(fmt_dms(degrees(h_c))))
            print("2. Azimut Sol (Az) [+-180]:         {}".format(fmt_dms(az_sun)))
            print("3. Azimut Pi (Az_pi) [0,360]:       {}".format(fmt_dms(wrap_0_360(degrees(az_p)))))
            print("4. Azimut Pi (Az_pi) [+-180]:       {}".format(fmt_dms(api)))
            print("\n   => ANALISIS DE SIGNO DE mu:")
            print("      * B_pi calculado:             {}".format(fmt_dms(bpi)))
            print("      * Decision (B_pi vs Az_Sol):  {}".format(signo_txt))
            print("      * Mu (CON SIGNO):             {}".format(fmt_dms(degrees(mu_signed))))
            print("\n5. Long. Eclipt. Sol (lambda):      {}".format(fmt_dms(wrap_0_360(degrees(l_sol_e)))))

        elif mode == 'f':
            # ---------------------------------------------------------
            # Sub-opcion: anadir mancha rapida a observacion existente
            # ---------------------------------------------------------
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_observacion, fecha_hora, archivo_img, mu_angulo, beta_optica "
                "FROM Observaciones ORDER BY fecha_hora ASC")
            obs_guardadas = cursor.fetchall()
            print("\n   ======================================")
            print("   MODO F: REGISTRAR MANCHA SOLAR")
            print("   ======================================")
            if obs_guardadas:
                print("\n   0) Anadir mancha a observacion ya guardada (rapido)")
            print("   1) Nueva observacion completa (calcular mu, beta, etc.)")
            sub = input("\n   Tu eleccion: ").strip()

            if sub == '0' and obs_guardadas:
                print("\n   Observaciones guardadas:")
                for i, (oid, fh, img, mu_g, beta_g) in enumerate(obs_guardadas, 1):
                    mu_g_f   = float(mu_g)   if mu_g   is not None else None
                    beta_g_f = float(beta_g) if beta_g is not None else None
                    mu_txt   = "{:.3f}".format(mu_g_f)   if mu_g_f   is not None else "N/A"
                    beta_txt = "{:.3f}".format(beta_g_f) if beta_g_f is not None else "N/A"
                    print("   {:2d}) [ID={}] {} | mu={} beta={}".format(i, oid, fh or img, mu_txt, beta_txt))
                print("   (Escribe el numero de la lista, no el ID)")
                while True:
                    try:
                        idx = int(input("   Selecciona numero (1-{}): ".format(len(obs_guardadas))).strip()) - 1
                        if 0 <= idx < len(obs_guardadas):
                            break
                        print("   [!] Numero fuera de rango. Elige entre 1 y {}.".format(len(obs_guardadas)))
                    except ValueError:
                        print("   [!] Introduce un numero entero.")
                id_o_sel, fh_sel, img_sel, mu_g_sel, beta_g_sel = obs_guardadas[idx]

                # Recuperar todos los datos de la observacion seleccionada
                cursor.execute(
                    "SELECT centro_x, centro_y, radio_sol, lambda_sol "
                    "FROM Observaciones WHERE id_observacion=?", (id_o_sel,))
                row_obs = cursor.fetchone()
                xc_r       = float(row_obs[0]) if row_obs[0] is not None else 0.0
                yc_r       = float(row_obs[1]) if row_obs[1] is not None else 0.0
                r_sol_r    = float(row_obs[2]) if row_obs[2] is not None else 1.0
                l_sol_deg_r = float(row_obs[3]) if row_obs[3] is not None else 0.0
                mu_g_sel   = float(mu_g_sel)   if mu_g_sel   is not None else 0.0
                beta_g_sel = float(beta_g_sel) if beta_g_sel is not None else 0.0
                l_sol_r    = radians(l_sol_deg_r)
                mu_r       = radians(mu_g_sel)
                beta_r     = radians(beta_g_sel)

                print("\n   Observacion: [{}] {} | Img: {}".format(id_o_sel, fh_sel or '', img_sel or ''))
                print("   Centro=({}, {})  Radio={}px  mu={:.3f}  beta={:.3f}".format(
                    xc_r, yc_r, r_sol_r, mu_g_sel, beta_g_sel))

                grupo = input("\n   > ID Mancha: ").strip()

                # Comprobar si ya existe
                cursor.execute(
                    "SELECT pixel_x, pixel_y FROM Mediciones "
                    "WHERE id_observacion=? AND id_grupo=?", (id_o_sel, grupo))
                res = cursor.fetchone()
                if res:
                    print("\n   [!] Ya existe esta mancha. X={}, Y={}".format(res[0], res[1]))
                    if input("   Reemplazar? (s/n): ").lower() != 's':
                        continue

                xm_r = float(input("   > X Mancha (pixel): "))
                ym_r = float(input("   > Y Mancha (pixel): "))

                phi_res_r, L_res_r, rho_r, dist_r, th_m_r = solve_mancha_heliografica(
                    mu_r, r_sol_r, xm_r, ym_r, xc_r, yc_r, beta_r, l_sol_r)

                cursor.execute('''INSERT OR REPLACE INTO Mediciones
                    (id_observacion, id_grupo, pixel_x, pixel_y, rho,
                     latitud_phi, longitud_L, mu_angulo, beta_optica)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                    (id_o_sel, grupo, xm_r, ym_r, rho_r,
                     degrees(phi_res_r), degrees(L_res_r),
                     mu_g_sel, beta_g_sel))
                conn.commit()

                print("\n=== MANCHA ANADIDA ===")
                print("Observacion:             [{}] {}".format(id_o_sel, fh_sel or img_sel))
                print("ID Mancha:               {}".format(grupo))
                print("Pixel (X, Y):            ({:.1f}, {:.1f})".format(xm_r, ym_r))
                print("Rho:                     {:.6f}".format(rho_r))
                print("Angulo theta_m:          {}".format(fmt_dms(degrees(th_m_r))))
                if rho_r > 1.0:
                    print("AVISO: Rho > 1 (mancha fuera del disco solar)")
                print("LATITUD  (Phi):          {}".format(fmt_dms(degrees(phi_res_r))))
                print("LONGITUD (L) [0-360]:    {}".format(fmt_dms(wrap_0_360(degrees(L_res_r)))))
                print("LONGITUD (L) [+-180]:    {}".format(fmt_dms(wrap_pm180(degrees(L_res_r)))))
                continue   # volver al menu principal

            # else: nueva observacion completa (sub == '1' o cualquier otra cosa)
            phi_obs = input_dms("Latitud Observador (phi)")
            dec_sol = input_dms("Declinacion Sol (delta)")
            alpha   = input_hms("Ascension Recta Sol (alpha)")
            theta   = input_hms("Hora Siderea Local (theta)")
            H = theta - alpha
            print("   -> Angulo Horario (H) calc:    {}".format(fmt_hms(wrap_pm12(degrees(H)/15.0))))
            h_c, az_s = solve_direct_equatorial(phi_obs, dec_sol, H)
            print("   -> Altura Sol (h) calc:        {}".format(fmt_dms(degrees(h_c))))
            az_sun_deg = wrap_pm180(degrees(az_s))
            print("   -> Azimut Sol (Az) calc:       {}".format(fmt_dms(az_sun_deg)))
            l_sol, _ = solve_equatorial_to_ecliptic(alpha, dec_sol, EPSILON_J2000)
            print("   -> Long. Eclipt. Sol (lambda): {}".format(fmt_dms(wrap_0_360(degrees(l_sol)))))
            mu_v, az_p = solve_mu_and_azpi(phi_obs, theta, h_c, EPSILON_J2000)
            az_pi_deg = wrap_pm180(degrees(az_p))
            print("   -> Azimut Pi (Az_pi) calc:     {}".format(fmt_dms(az_pi_deg)))
            # Transformacion simulador: Api>0 (Oeste) -> Bpi negativo; Api<0 (Este) -> Bpi positivo
            if az_pi_deg > 0:
                bpi = -(180.0 - az_pi_deg)
            elif az_pi_deg < 0:
                bpi = 180.0 + az_pi_deg
            else:
                bpi = 0.0
            if bpi > az_sun_deg:
                mu_signed = -abs(mu_v)
                signo_txt = "Negativo (-): Pi a la derecha (Este) del Sol"
            elif bpi < az_sun_deg:
                mu_signed = abs(mu_v)
                signo_txt = "Positivo (+): Pi a la izquierda (Oeste) del Sol"
            else:
                mu_signed = abs(mu_v)
                signo_txt = "Cero (0): alineados en el mismo meridiano"
            print("\n   => ANALISIS DE SIGNO DE mu:")
            print("      * B_pi calculado:             {}".format(fmt_dms(bpi)))
            print("      * Decision (B_pi vs Az_Sol):  {}".format(signo_txt))
            print("      * MU FINAL (CON SIGNO):       {}".format(fmt_dms(degrees(mu_signed))))

            fecha    = input("\n   > Fecha y Hora (DD-MM-AAAA HH:MM): ")
            foto     = input("   > Nombre de Foto: ")
            grupo    = input("   > ID Mancha: ")

            cursor = conn.cursor()
            cursor.execute(
                "SELECT m.pixel_x, m.pixel_y FROM Mediciones m "
                "JOIN Observaciones o ON m.id_observacion = o.id_observacion "
                "WHERE o.archivo_img = ? AND m.id_grupo = ?", (foto, grupo))
            res = cursor.fetchone()
            if res:
                print("\n[!] Ya existe. X={}, Y={}".format(res[0], res[1]))
                if input("Reemplazar? (s/n): ").lower() != 's': continue

            r_sol    = float(input("   > Radio Sol (px): "))
            xc       = float(input("   > X Centro Sol: "))
            yc       = float(input("   > Y Centro Sol: "))
            xm       = float(input("   > X Mancha: "))
            ym       = float(input("   > Y Mancha: "))
            beta_opt = input_dms("Beta Optica")

            # Polo norte solar (Phi=90): en el disco esta en phi_M=PHI_ZERO,
            # lambda_M = LAMBDA_NORTH - (l_sol + pi).  (Antes faltaba el termino l_sol.)
            lam_M_norte = LAMBDA_NORTH - (l_sol + pi)
            yv_n = sin(PHI_ZERO)                        # = rho*sin(A)
            xv_n = cos(PHI_ZERO) * sin(lam_M_norte)     # = rho*cos(A)
            theta_norte = atan2(yv_n, xv_n) - mu_signed - beta_opt
            rho_norte = sqrt(xv_n*xv_n + yv_n*yv_n)
            x_norte = xc + rho_norte * cos(theta_norte) * r_sol
            y_norte = yc - rho_norte * sin(theta_norte) * r_sol

            phi_res, L_res, rho, dist, th_m = solve_mancha_heliografica(
                mu_signed, r_sol, xm, ym, xc, yc, beta_opt, l_sol)

            cursor.execute('''INSERT OR IGNORE INTO Observaciones
                (fecha_hora, archivo_img, centro_x, centro_y, radio_sol,
                 declinacion_sol, alfa_sol, h_sol, az_sol, lambda_sol, mu_angulo, beta_optica, b_pi)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (fecha, foto, xc, yc, r_sol,
                 degrees(dec_sol), degrees(alpha), degrees(h_c), az_sun_deg, degrees(l_sol),
                 degrees(mu_signed), degrees(beta_opt), bpi))
            cursor.execute('''UPDATE Observaciones SET
                centro_x=?, centro_y=?, radio_sol=?, declinacion_sol=?,
                alfa_sol=?, h_sol=?, az_sol=?, lambda_sol=?, mu_angulo=?, beta_optica=?, b_pi=?
                WHERE archivo_img=?''',
                (xc, yc, r_sol, degrees(dec_sol),
                 degrees(alpha), degrees(h_c), az_sun_deg, degrees(l_sol),
                 degrees(mu_signed), degrees(beta_opt), bpi, foto))
            cursor.execute("SELECT id_observacion FROM Observaciones WHERE archivo_img=?", (foto,))
            id_o = cursor.fetchone()[0]
            cursor.execute('''INSERT OR REPLACE INTO Mediciones
                (id_observacion, id_grupo, pixel_x, pixel_y, rho,
                 latitud_phi, longitud_L, mu_angulo, beta_optica)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (id_o, grupo, xm, ym, rho,
                 degrees(phi_res), degrees(L_res), degrees(mu_signed), degrees(beta_opt)))
            conn.commit()

            print("\n=== RESULTADO MODO F (DETALLADO) ===")
            print("--- CALCULOS DEL CIELO ---")
            print("Altura Sol (h):                  {}".format(fmt_dms(degrees(h_c))))
            print("Azimut Sol (Az):                 {}".format(fmt_dms(az_sun_deg)))
            print("Long. Eclipt. Sol (lambda):      {}".format(fmt_dms(wrap_0_360(degrees(l_sol)))))
            print("Angulo Mu (CON SIGNO):           {}".format(fmt_dms(degrees(mu_signed))))
            print("--- CALCULOS IMAGEN ---")
            print("Distancia r:                     {:.2f} px".format(dist))
            print("Valor Rho:                       {:.6f}".format(rho))
            print("Angulo Mancha (theta_m):         {}".format(fmt_dms(degrees(th_m))))
            print("Coord Norte Solar en foto (X,Y): ({:.2f}, {:.2f})".format(x_norte, y_norte))
            if rho > 1.0:
                print("AVISO: Rho mancha > 1. La mancha esta fuera del disco solar.")
            if rho_norte > 1.0:
                print("AVISO: Rho norte > 1. El polo solar esta fuera del disco visible.")
            print("-------------------------")
            print("LATITUD HELIOGRAF. (Phi):        {}".format(fmt_dms(degrees(phi_res))))
            print("LONGITUD HELIOGRAF. (L) [0,360]: {}".format(fmt_dms(wrap_0_360(degrees(L_res)))))
            print("LONGITUD HELIOGRAF. (L) [+-180]: {}".format(fmt_dms(wrap_pm180(degrees(L_res)))))

        elif mode == 'h':
            print("\n   DISTANCIA ENTRE MANCHAS SOLARES (TRIANGULO ESFERICO)")
            print("   -------------------------------------------------------")
            print("   1) Introducir coordenadas manualmente")
            print("   2) Leer coordenadas desde la Base de Datos")
            opc = input("   Tu eleccion (1/2): ").strip()
            if opc == '2':
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.id_grupo, m.latitud_phi, m.longitud_L, o.archivo_img, o.fecha_hora
                    FROM Mediciones m
                    JOIN Observaciones o ON m.id_observacion = o.id_observacion
                    ORDER BY o.fecha_hora, m.id_grupo
                """)
                filas = cursor.fetchall()
                if len(filas) < 2:
                    print("\n[!] Necesitas al menos 2 manchas guardadas en la BD.")
                else:
                    print("\n   Manchas disponibles en la BD:")
                    print("   {:<4} {:<15} {:<22} {:<18} {:<18}".format(
                        "#", "ID Mancha", "Foto", "Latitud Phi", "Longitud L [0,360]"))
                    print("   " + "-"*80)
                    for i, fila in enumerate(filas):
                        print("   {:<4} {:<15} {:<22} {:<18} {:<18}".format(
                            i+1, str(fila[0]), str(fila[3]),
                            fmt_dms(fila[1]), fmt_dms(wrap_0_360(fila[2]))))
                    try:
                        n1 = int(input("\n   > Numero de la primera mancha:  ")) - 1
                        n2 = int(input("   > Numero de la segunda mancha: ")) - 1
                        if n1 < 0 or n2 < 0 or n1 >= len(filas) or n2 >= len(filas):
                            print("[!] Numero fuera de rango.")
                        elif n1 == n2:
                            print("[!] Debes elegir dos manchas distintas.")
                        else:
                            phi1_rad = radians(filas[n1][1])
                            lam1_rad = radians(filas[n1][2])
                            phi2_rad = radians(filas[n2][1])
                            lam2_rad = radians(filas[n2][2])
                            print("\n   Mancha 1: {}  (Foto: {})".format(filas[n1][0], filas[n1][3]))
                            print("     Phi = {}   L = {}".format(
                                fmt_dms(filas[n1][1]), fmt_dms(wrap_0_360(filas[n1][2]))))
                            print("   Mancha 2: {}  (Foto: {})".format(filas[n2][0], filas[n2][3]))
                            print("     Phi = {}   L = {}".format(
                                fmt_dms(filas[n2][1]), fmt_dms(wrap_0_360(filas[n2][2]))))
                            d_rad, d_deg, d_km = distancia_manchas_calc(
                                phi1_rad, lam1_rad, phi2_rad, lam2_rad)
                            print("\n=== RESULTADO DISTANCIA ENTRE MANCHAS ===")
                            print("Distancia angular (d) [radianes]: {:.8f} rad".format(d_rad))
                            print("Distancia angular (d) [grados]:   {}".format(fmt_dms(d_deg)))
                            print("Distancia fisica  (D) [km]:       {:.2f} km".format(d_km))
                            print("  (usando R_Sol = {:,} km)".format(int(R_SOL_KM)))
                    except ValueError:
                        print("[!] Entrada no valida.")
            else:
                print("\n   --- MANCHA 1 ---")
                phi1_rad = input_dms("Latitud heliografica Phi_1")
                lam1_rad = input_dms("Longitud heliografica L_1")
                print("   --- MANCHA 2 ---")
                phi2_rad = input_dms("Latitud heliografica Phi_2")
                lam2_rad = input_dms("Longitud heliografica L_2")
                d_rad, d_deg, d_km = distancia_manchas_calc(
                    phi1_rad, lam1_rad, phi2_rad, lam2_rad)
                print("\n=== RESULTADO DISTANCIA ENTRE MANCHAS ===")
                print("Distancia angular (d) [radianes]: {:.8f} rad".format(d_rad))
                print("Distancia angular (d) [grados]:   {}".format(fmt_dms(d_deg)))
                print("Distancia fisica  (D) [km]:       {:.2f} km".format(d_km))
                print("  (usando R_Sol = {:,} km)".format(int(R_SOL_KM)))

        elif mode == 'i':
            print("\n   ROTACION DIFERENCIAL SOLAR (Periodo Sidereo vs Latitud)")
            print("   -------------------------------------------------------")
            print("   Buscando manchas con >= 2 observaciones en la BD...")
            calcular_rotacion(conn)

        elif mode == 'g':
            codigo_streamlit = f'''
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

PHI_ZERO_W    = {PHI_ZERO}
LAMBDA_NORTH_W= {LAMBDA_NORTH}

def fmt_dms(deg_val):
    sign = '-' if deg_val < 0 else ''
    val = abs(deg_val); d = int(val); rem = (val-d)*60.0; m = int(rem); s = (rem-m)*60.0
    return "{{}}{{:02d}}d {{:02d}}m {{:06.3f}}s".format(sign, d, m, s)

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

import shutil, tempfile
_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_AQUI)
_BD_LYDIA = os.path.join(_AQUI, "manchas_tfg.db")

st.sidebar.header("Base de datos")
_MODO = st.sidebar.radio("Que quieres hacer?", ["Ver los datos de Lydia (solo lectura)", "Crear una base de datos nueva (meter mis datos)"])

def _crear_bd_vacia(origen, destino):
    shutil.copy(origen, destino)
    con = sqlite3.connect(destino); cur = con.cursor()
    for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
        cur.execute('DELETE FROM "%s"' % t)
    con.commit(); con.close()

@st.cache_resource
def _preparar_bd(modo):
    base = os.path.join(tempfile.gettempdir(), "gestor_manchas_tfg")
    os.makedirs(base, exist_ok=True)
    if modo.startswith("Ver"):
        dst = os.path.join(base, "lydia_solo_lectura.db")
        shutil.copy(_BD_LYDIA, dst)
        return dst
    dst = os.path.join(base, "mis_datos.db")
    if not os.path.exists(dst):
        _crear_bd_vacia(_BD_LYDIA, dst)
    return dst

RUTA_BD = _preparar_bd(_MODO)
if _MODO.startswith("Ver"):
    st.sidebar.info("Estas viendo los datos reales de Lydia. Trabajas sobre una copia temporal, asi que el original no se toca.")
else:
    st.sidebar.success("Base de datos nueva y vacia. Mete tus observaciones y manchas y ve a la pestana Resultados Calculados para el ajuste y la grafica.")

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
        st.warning("Ultimo recalculo ({{}}): {{}} mancha(s) actualizadas. Celdas modificadas resaltadas en AMARILLO."
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
        _fmt = {{}}
        for _c in ('dPhi','dL','drho','Phi_antes','Phi_despues','L_antes','L_despues'):
            if _c in _df_diff.columns:
                _fmt[_c] = '{{:+.4f}}' if _c.startswith('d') or 'Phi' in _c else '{{:.4f}}'
        _sty = _df_diff.style.format(_fmt, na_rep='-')
        _resaltar = [c for c in ('dPhi','dL','drho') if c in _df_diff.columns]
        if _resaltar:
            try:
                _sty = _sty.map(_hl_amarillo, subset=_resaltar)
            except Exception:
                _sty = _sty.applymap(_hl_amarillo, subset=_resaltar)
        st.dataframe(_sty, use_container_width=True, hide_index=True)
        st.caption("Las celdas AMARILLAS son las cantidades que cambiaron.")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Tabla: Observaciones (Fotos)", "Tabla: Mediciones (Manchas)", "Resultados Calculados", "Animacion Solar", "Errores (+-sigma)", "Fotos (galeria)", "Resultado final"])

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
    cfg_obs = {{
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
    }}
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
        obs_nuevas = {{}}
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
                    cambios_manchas.append({{
                        "Mancha":   "M" + str(mrow.get('id_grupo','?')),
                        "Fecha":    str(obs_data.get('fecha_hora',''))[:16],
                        "mu":       "{{:+.3f}}".format(float(mu_deg)) if pd.notnull(mu_deg) else "-",
                        "beta":     "{{:+.3f}}".format(float(beta_deg)) if pd.notnull(beta_deg) else "-",
                        "Phi_antes":   float(phi_prev) if pd.notnull(phi_prev) else 0.0,
                        "Phi_despues": phi_new,
                        "dPhi":     dphi,
                        "L_antes":     float(lon_prev) if pd.notnull(lon_prev) else 0.0,
                        "L_despues":   lon_new,
                        "dL":       dlon,
                        "drho":     drho,
                    }})
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
        st.session_state['ultimo_cambio'] = {{
            "tipo":    "observaciones",
            "n":       n_recalc,
            "detalle": cambios_manchas,
        }}
        st.success("Observaciones guardadas. {{}} mancha(s) recalculadas.".format(n_recalc))
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
    cfg_med = {{
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
    }}
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
        st.success("Mostrando **{{}}** medicion(es) de {{}} totales, agrupadas en **{{}}** observacion(es) de {{}} totales.".format(
            len(df_res), n_med_total, df_res['id_observacion'].nunique(), n_obs_total))
        n_huerfanas = df_res['fecha_hora'].isna().sum()
        if n_huerfanas > 0:
            st.warning("{{}} medicion(es) sin observacion asociada - aparecen al final.".format(n_huerfanas))

        # Filtro por dia (los 153 expanders abiertos colapsan el navegador)
        df_res['_dia_str'] = df_res['fecha_hora'].apply(
            lambda s: (parsear_fecha(s).strftime('%Y-%m-%d')
                       if pd.notnull(parsear_fecha(s)) else 'Sin fecha'))
        dias_disponibles = ['(Todos)'] + sorted(df_res['_dia_str'].unique())
        dia_sel = st.selectbox("Filtrar por dia", dias_disponibles, index=0, key="tab3_dia")
        if dia_sel != '(Todos)':
            df_res_view = df_res[df_res['_dia_str'] == dia_sel].reset_index(drop=True)
            st.info("Mostrando {{}} medicion(es) del dia {{}}.".format(len(df_res_view), dia_sel))
        else:
            df_res_view = df_res
        expandido_por_defecto = (dia_sel != '(Todos)') and (len(df_res_view) <= 20)

        for _, row in df_res_view.iterrows():
            fh_safe   = row['fecha_hora']   if pd.notnull(row['fecha_hora'])   else 'sin fecha'
            arch_safe = row['archivo_img']  if pd.notnull(row['archivo_img'])  else 'sin foto'
            titulo = "📍 Mancha **{{}}** | {{}} | {{}}".format(
                row['id_grupo'], fh_safe, arch_safe)
            with st.expander(titulo, expanded=expandido_por_defecto):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**--- CALCULOS DEL CIELO ---**")
                    h    = row['h_sol']
                    az   = row['az_sol']
                    lam  = row['lambda_sol']
                    mu   = row['mu_angulo']
                    st.text("Altura Sol (h):              {{}}".format(fmt_dms(float(h))          if pd.notnull(h)   else "N/A"))
                    st.text("Azimut Sol (Az):             {{}}".format(fmt_dms(float(az))         if pd.notnull(az)  else "N/A"))
                    st.text("Longitud Solar (lambda):     {{}}".format(fmt_dms(float(lam) % 360) if pd.notnull(lam) else "N/A"))
                    st.text("Angulo Mu (CON SIGNO):       {{}}".format(fmt_dms(float(mu))         if pd.notnull(mu)  else "N/A"))

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
                        st.text("Distancia r:                 {{:.2f}} px".format(r_c))
                        st.text("Valor Rho:                   {{:.6f}}".format(rho_c))
                        st.text("Angulo Mancha (theta_m):     {{}}".format(fmt_dms(math.degrees(th_c))))
                        st.text("Norte Solar en foto (X,Y):   ({{:.2f}}, {{:.2f}})".format(xn, yn))
                        st.markdown("---")
                        st.text("LATITUD HELIOGRAF. (Phi):    {{}}".format(fmt_dms(math.degrees(lat_r))))
                        st.text("LONGITUD HELIOGRAF. [0,360]: {{}}".format(fmt_dms(lon_360)))
                        st.text("LONGITUD HELIOGRAF. [+-180]: {{}}".format(fmt_dms(lon_pm)))
                        if rho_c > 1.0:
                            st.warning("Rho > 1: la mancha esta fuera del disco solar.")
                    except Exception as e:
                        st.error("Error calculando: {{}}".format(e))

with tab4:
    import sim_solar
    sim_solar.render_animacion(RUTA_BD, video_path=os.path.join(_RAIZ, 'fotos abril 2026', 'fotos_con_ejes_TODAS', 'CON_EJES_CURVOS', 'video', 'video_manchas.mp4'))


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
            st.caption("Total: {{}} mancha(s) -> {{}} punto(s) en el grafico.".format(
                len(filas_mancha), len(filas_mancha)))
            for f in sorted(filas_mancha, key=lambda x: int(x['grp'])):
                st.markdown("---")
                st.markdown("### Mancha {{}}  ·  {{}} obs  ·  metodo: **{{}}**".format(
                    f['grp'], f['n_obs'], f['metodo']))
                st.markdown(
                    "**Primera obs:** {{}}  &emsp;  **Ultima obs:** {{}}  &emsp;  "
                    "Δt = **{{:.3f}}** d &emsp; ΔΛ = **{{:.3f}}°**".format(
                        f['f1'], f['fN'], f['dt_tot'], f['dL_tot']))
                st.markdown(
                    "**Phi media:** {{:+.4f}}° &emsp;±&emsp; **{{:.4f}}°**  "
                    "&nbsp;(muestral = {{:.4f}}°, propagacion = {{:.4f}}° → se usa el MAX)".format(
                        f['phi_med'], f['S_phi_fin'], f['S_phi_mu'], f['S_phi_pr']))
                if f['S_L_resid'] is not None:
                    st.markdown(
                        "**S_Lambda (residuos):** {{:.4f}}°".format(f['S_L_resid']))
                sT_s  = "± **{{:.4f}}** d".format(f['sigma_T_g'])  if f['sigma_T_g']  is not None else "N/D"
                som_s = "± **{{:.4f}}** °/d".format(f['sigma_om_g']) if f['sigma_om_g'] is not None else "N/D"
                st.markdown(
                    "**ω:** {{:.4f}} °/d  &nbsp;{{}} &emsp;&emsp; **T sidéreo:** {{:.3f}} d &nbsp;{{}}".format(
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

                filas_err.append({{
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
                }})

        if filas_err:
            st.caption("sigma calculado con propagacion numerica (diferencias finitas centrales, delta = 5 px)")
            # Agrupar por mancha y mostrar como texto
            from collections import defaultdict as _dd
            por_mancha = _dd(list)
            for f in filas_err:
                por_mancha[f['Mancha']].append(f)

            for mancha_id, pares in sorted(por_mancha.items(), key=lambda x: int(x[0])):
                st.markdown("---")
                st.markdown("### ☀️ Mancha {{}}".format(mancha_id))
                for p in pares:
                    som_str = "± {{:.4f}}".format(p['+-sigma_om'])   if p['+-sigma_om']  is not None else "N/D"
                    sT_str  = "± {{:.4f}}".format(p['+-sigma_T'])    if p['+-sigma_T']   is not None else "N/D"
                    sPh_str = "± {{:.4f}}°".format(p['+-sigma_Phi']) if p['+-sigma_Phi'] is not None else "N/D"
                    st.markdown(
                        "**{{}}  →  {{}}** &emsp;&emsp;&emsp;&emsp;&emsp; Δt = **{{}}** d (días)".format(
                            p['Obs 1'], p['Obs 2'], p['Dt (dias)']))
                    st.markdown(
                        "&emsp; "
                        "ΔΛ = **{{:.4f}}°** &emsp; "
                        "Φ = **{{:.4f}}°** &emsp; "
                        "ω = **{{:.4f}} °/d** &nbsp; {{}} &emsp; "
                        "T = **{{:.3f}}** d (días) &nbsp; {{}} &emsp; "
                        "σΦ = {{}}".format(
                            p['DeltaL (°)'], p['Phi (°)'],
                            p['omega (°/d)'], som_str,
                            p['T_sid (d)'],  sT_str,
                            sPh_str))
                    st.markdown("")
        else:
            st.info("No hay pares de observaciones del mismo grupo todavia.")

with tab6:
    import galeria
    galeria.render_galeria(_RAIZ)

with tab7:
    st.header("Resultado final")
    _graf = os.path.join(_RAIZ, "figuras", "rotacion_solar.png")
    if os.path.exists(_graf):
        st.image(_graf, use_column_width=True,
                 caption="Velocidad angular y periodo frente a la latitud heliografica, con barras de error y comparacion con la ley de Faye.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A  (°/día)", "+14,10 ± 0,28")
    c2.metric("B  (°/día)", "-2,21 ± 2,47")
    c3.metric("Periodo ecuador", "≈ 25 días")
    c4.metric("ω ecuador (°/día)", "≈ 14,1")
    st.success("B < 0: el ecuador gira más rápido que los polos → rotación diferencial del Sol "
               "(descarta el giro rígido). El valor central coincide casi con la ley de Faye.")
    st.caption("Ajuste ω(Φ) = A + B·sin²Φ a las 27 manchas seguidas (χ²_ν ≈ 0,94). "
               "Si has metido tus propios datos, tu ajuste está en la pestaña «Resultados Calculados».")
'''
            path_st = os.path.join(CARPETA_TFG, "gestor_web", "gestor_web.py")
            if False:  # el gestor se mantiene como archivo propio; no se regenera
                f.write(codigo_streamlit)
            print("\n[i] Lanzando Gestor Web de Base de Datos (Streamlit)...")
            print("    (Manten esta terminal abierta. Ctrl+C para cerrarlo)")
            try:
                subprocess.Popen(["streamlit", "run", path_st], shell=True)
            except Exception as e:
                print("[!] Error al lanzar Streamlit: {}".format(e))

    conn.close()

if __name__ == "__main__":
    main()