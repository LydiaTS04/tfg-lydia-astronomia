import os
import sys
from math import radians, degrees

import streamlit as st

st.set_page_config(layout="wide", page_title="Calculadora astronómica", page_icon="\U0001F9EE")

# Importa las funciones de cálculo del código principal (las mismas del TFG)
_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CC = os.path.join(_RAIZ, "codigo_calculo")
if _CC not in sys.path:
    sys.path.insert(0, _CC)
import calculo_principal as cp   # noqa: E402

EPS = cp.EPSILON_J2000

def grados(rad):   # "12,3456°  (12d 20m 44s)"
    return "%.4f°   (%s)" % (degrees(rad), cp.fmt_dms(degrees(rad)))

def horas(rad):    # en horas: "8,1234 h  (08h 07m ..)"
    h = degrees(rad) / 15.0
    return "%.4f h   (%s)" % (cp.wrap_0_24(h), cp.fmt_hms(cp.wrap_0_24(h)))

st.title("\U0001F9EE Calculadora astronómica")
st.caption("Las mismas conversiones del código del TFG (modos a–e y h). "
           "Los ángulos se introducen en grados decimales; la ascensión recta y "
           "la hora sidérea, en horas.")

modo = st.selectbox(
    "¿Qué quieres calcular?",
    ["Horizontales → Ecuatoriales  (modo a)",
     "Ecuatoriales → Horizontales  (modo b)",
     "Eclípticas → Ecuatoriales  (modo c)",
     "Ecuatoriales → Eclípticas  (modo d)",
     "Sol: ángulo µ y azimut de π  (modo e)",
     "Distancia entre dos manchas  (modo h)"],
)
st.divider()

# ----------------------------- modo a -----------------------------
if modo.startswith("Horizontales"):
    c1, c2, c3, c4 = st.columns(4)
    phi   = c1.number_input("Latitud observador φ (°)", value=40.40, format="%.4f")
    Az    = c2.number_input("Azimut Az (° · Sur=0, Oeste +)", value=30.00, format="%.4f")
    h     = c3.number_input("Altura h (°)", value=35.00, format="%.4f")
    theta = c4.number_input("Hora sidérea local θ (horas)", value=12.00, format="%.4f")
    delta, H = cp.solve_inverse_horizontal(radians(phi), radians(h), radians(Az))
    alpha = radians(theta * 15.0) - H
    lmb, _ = cp.solve_equatorial_to_ecliptic(alpha, delta, EPS)
    st.subheader("Resultado")
    st.write("**Ángulo horario H:**", horas(H))
    st.write("**Ascensión recta α:**", horas(alpha))
    st.write("**Declinación δ:**", grados(delta))
    st.write("**Longitud eclíptica del Sol λ:**", grados(radians(cp.wrap_0_360(degrees(lmb)))))

# ----------------------------- modo b -----------------------------
elif modo.startswith("Ecuatoriales → Horizontales"):
    c1, c2, c3, c4 = st.columns(4)
    phi   = c1.number_input("Latitud observador φ (°)", value=40.40, format="%.4f")
    alpha = c2.number_input("Ascensión recta α (horas)", value=8.00, format="%.4f")
    delta = c3.number_input("Declinación δ (°)", value=20.00, format="%.4f")
    theta = c4.number_input("Hora sidérea local θ (horas)", value=12.00, format="%.4f")
    H = radians(theta * 15.0) - radians(alpha * 15.0)
    h_out, Az_out = cp.solve_direct_equatorial(radians(phi), radians(delta), H)
    st.subheader("Resultado")
    st.write("**Ángulo horario H:**", horas(H))
    st.write("**Altura h:**", grados(h_out))
    st.write("**Azimut Az (±180°):**", grados(radians(cp.wrap_pm180(degrees(Az_out)))))

# ----------------------------- modo c -----------------------------
elif modo.startswith("Eclípticas"):
    c1, c2 = st.columns(2)
    lmb  = c1.number_input("Longitud eclíptica λ (°)", value=30.00, format="%.4f")
    beta = c2.number_input("Latitud eclíptica β (°)", value=0.00, format="%.4f")
    alpha, delta = cp.solve_ecliptic_to_equatorial(radians(lmb), radians(beta), EPS)
    st.subheader("Resultado")
    st.write("**Ascensión recta α:**", horas(alpha))
    st.write("**Declinación δ:**", grados(delta))

# ----------------------------- modo d -----------------------------
elif modo.startswith("Ecuatoriales → Eclípticas"):
    c1, c2 = st.columns(2)
    alpha = c1.number_input("Ascensión recta α (horas)", value=8.00, format="%.4f")
    delta = c2.number_input("Declinación δ (°)", value=20.00, format="%.4f")
    lmb, beta = cp.solve_equatorial_to_ecliptic(radians(alpha * 15.0), radians(delta), EPS)
    st.subheader("Resultado")
    st.write("**Longitud eclíptica λ (0–360°):**", grados(radians(cp.wrap_0_360(degrees(lmb)))))
    st.write("**Latitud eclíptica β:**", grados(beta))

# ----------------------------- modo e -----------------------------
elif modo.startswith("Sol"):
    c1, c2, c3, c4 = st.columns(4)
    phi   = c1.number_input("Latitud observador φ (°)", value=40.40, format="%.4f")
    dec   = c2.number_input("Declinación del Sol δ (°)", value=12.00, format="%.4f")
    alpha = c3.number_input("Ascensión recta del Sol α (horas)", value=4.00, format="%.4f")
    theta = c4.number_input("Hora sidérea local θ (horas)", value=6.00, format="%.4f")
    theta_r = radians(theta * 15.0); alpha_r = radians(alpha * 15.0)
    H_e = theta_r - alpha_r
    h_c, az_s = cp.solve_direct_equatorial(radians(phi), radians(dec), H_e)
    mu_v, az_p = cp.solve_mu_and_azpi(radians(phi), theta_r, h_c, EPS)
    api = cp.wrap_pm180(degrees(az_p)); az_sun = cp.wrap_pm180(degrees(az_s))
    if api > 0:
        bpi = -(180.0 - api)
    elif api < 0:
        bpi = 180.0 + api
    else:
        bpi = 0.0
    if bpi > az_sun:
        mu_signed = -abs(mu_v); signo = "π a la derecha (Este) del Sol → µ NEGATIVO"
    elif bpi < az_sun:
        mu_signed = abs(mu_v);  signo = "π a la izquierda (Oeste) del Sol → µ POSITIVO"
    else:
        mu_signed = 0.0;        signo = "alineados en el mismo meridiano → µ = 0"
    st.subheader("Resultado")
    st.write("**Altura del Sol h:**", grados(h_c))
    st.write("**Azimut del Sol (±180°):**", "%.4f°" % az_sun)
    st.write("**Azimut de π (±180°):**", "%.4f°" % api)
    st.write("**B_π (auxiliar de signo):**", "%.4f°" % bpi)
    st.success("**µ (con signo) = %s** — %s" % (cp.fmt_dms(degrees(mu_signed)), signo))

# ----------------------------- modo h -----------------------------
else:
    st.markdown("Distancia angular entre dos manchas a partir de sus coordenadas heliográficas (Φ, Λ).")
    c1, c2, c3, c4 = st.columns(4)
    phi1 = c1.number_input("Φ mancha 1 (°)", value=10.00, format="%.4f")
    lam1 = c2.number_input("Λ mancha 1 (°)", value=20.00, format="%.4f")
    phi2 = c3.number_input("Φ mancha 2 (°)", value=-5.00, format="%.4f")
    lam2 = c4.number_input("Λ mancha 2 (°)", value=50.00, format="%.4f")
    d_rad, d_deg, d_km = cp.distancia_manchas_calc(radians(phi1), radians(lam1),
                                                   radians(phi2), radians(lam2))
    st.subheader("Resultado")
    m1, m2 = st.columns(2)
    m1.metric("Distancia angular", "%.3f°" % d_deg)
    m2.metric("Distancia sobre la superficie", "%.0f km" % d_km)
