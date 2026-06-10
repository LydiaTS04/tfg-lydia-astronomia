import os
import glob
import sqlite3
from math import sin, cos, atan2, sqrt, radians, degrees, pi, hypot

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

try:
    import cv2
    TIENE_CV2 = True
except Exception:
    TIENE_CV2 = False

st.set_page_config(layout="wide", page_title="Ejes y meridianos", page_icon="\U0001F9ED")

_AQUI   = os.path.dirname(os.path.abspath(__file__))   # gestor_web/pages
_GESTOR = os.path.dirname(_AQUI)                        # gestor_web
_RAIZ   = os.path.dirname(_GESTOR)                      # proyecto
RUTA_BD = os.path.join(_GESTOR, "manchas_tfg.db")

# Constantes del codigo principal
PHI_ZERO     = radians(82.0 + 44.0/60.0 + 53.56/3600.0)
LAMBDA_NORTH = radians(-13.0 - 52.0/60.0 - 21.41/3600.0)

# ---------- inversa (Phi,L) -> pixel  (idéntica al código del TFG) ----------
def pole_proj(l_sol):
    C = (l_sol + pi) - LAMBDA_NORTH
    return (cos(PHI_ZERO)*cos(C), -cos(PHI_ZERO)*sin(C), sin(PHI_ZERO))

def base_perp(p):
    ref = (0., 0., 1.)
    if abs(p[2]) > 0.99:
        ref = (1., 0., 0.)
    ux = p[1]*ref[2]-p[2]*ref[1]; uy = p[2]*ref[0]-p[0]*ref[2]; uz = p[0]*ref[1]-p[1]*ref[0]
    n = sqrt(ux*ux+uy*uy+uz*uz); u = (ux/n, uy/n, uz/n)
    wx = p[1]*u[2]-p[2]*u[1]; wy = p[2]*u[0]-p[0]*u[2]; wz = p[0]*u[1]-p[1]*u[0]
    return u, (wx, wy, wz)

def punto_px(v, mu, R, xc, yc, beta):
    if v[0] <= 0.001:
        return None
    rho = sqrt(v[1]*v[1]+v[2]*v[2]); A = atan2(v[2], v[1]); th = A-mu-beta; r = rho*R
    return (xc + r*cos(th), yc - r*sin(th))

def paralelo(Phi_deg, l_sol, mu, R, xc, yc, beta, n=500):
    Phi = radians(Phi_deg); p = pole_proj(l_sol); u, w = base_perp(p)
    sP, cP = sin(Phi), cos(Phi); tr = []; act = []
    for i in range(n+1):
        t = 2*pi*i/n; ct, st_ = cos(t), sin(t)
        v = (sP*p[0]+cP*(ct*u[0]+st_*w[0]),
             sP*p[1]+cP*(ct*u[1]+st_*w[1]),
             sP*p[2]+cP*(ct*u[2]+st_*w[2]))
        px = punto_px(v, mu, R, xc, yc, beta)
        if px is None:
            if len(act) > 1: tr.append(act)
            act = []
        else:
            act.append(px)
    if len(act) > 1: tr.append(act)
    return tr

def norte_px(mu, R, xc, yc, beta, l_sol):
    lam = LAMBDA_NORTH - (l_sol + pi)
    yv = sin(PHI_ZERO); xv = cos(PHI_ZERO)*sin(lam)
    A = atan2(yv, xv); rho = hypot(xv, yv); th = A-mu-beta
    return (xc + rho*cos(th)*R, yc - rho*sin(th)*R)

# ---------- deteccion de disco (cv2 + RANSAC, como en el codigo) ----------
def _circ3(p1, p2, p3):
    ax, ay = p1; bx, by = p2; cx, cy = p3
    d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d) < 1e-6: return None
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return ux, uy, sqrt((ax-ux)**2+(ay-uy)**2)

def detectar_disco(bgr):
    import random as _r
    _r.seed(7)
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY); H, W = g.shape
    gb = cv2.GaussianBlur(g, (7, 7), 0); edges = cv2.Canny(gb, 25, 70)
    ys, xs = np.where(edges > 0)
    keep = (xs > 4) & (xs < W-4) & (ys > 4) & (ys < H-4)
    pts = np.c_[xs[keep], ys[keep]].astype(float)
    if len(pts) < 50: return None
    best = None; bestn = 0; bestin = None
    for _ in range(4000):
        s = _r.sample(range(len(pts)), 3)
        c3 = _circ3(pts[s[0]], pts[s[1]], pts[s[2]])
        if not c3: continue
        xc, yc, R = c3
        if R < W*0.18 or R > W*1.8: continue
        dd = np.abs(np.sqrt((pts[:, 0]-xc)**2 + (pts[:, 1]-yc)**2) - R)
        ninl = int((dd < 4).sum())
        if ninl > bestn: bestn = ninl; best = c3; bestin = dd < 4
    if best is None: return None
    x, y = pts[bestin, 0], pts[bestin, 1]
    A = np.c_[2*x, 2*y, np.ones(len(x))]; b = x*x+y*y
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    xc, yc = sol[0], sol[1]; R = sqrt(sol[2]+xc*xc+yc*yc)
    return float(xc), float(yc), float(R)

# ---------- dibujo de la cuadricula ----------
def dibujar_ejes(pil_img, xc, yc, R, l_sol_deg, mu_deg, beta_deg):
    l_sol = radians(l_sol_deg); mu = radians(mu_deg); beta = radians(beta_deg)
    im = pil_img.convert("RGB").copy()
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("arialbd.ttf", 18)
    except Exception:
        fnt = ImageFont.load_default()
    for Phi in range(-75, 76, 15):
        col = (0, 210, 0) if Phi == 0 else (0, 170, 230)
        anc = 5 if Phi == 0 else 2
        for tramo in paralelo(Phi, l_sol, mu, R, xc, yc, beta):
            d.line(tramo, fill=col, width=anc)
    xN, yN = norte_px(mu, R, xc, yc, beta, l_sol)
    vx, vy = xN-xc, yN-yc; nn = hypot(vx, vy)
    if nn > 1e-6:
        vx, vy = vx/nn, vy/nn
        d.line([(xc-vx*R, yc-vy*R), (xc+vx*R, yc+vy*R)], fill=(255, 230, 0), width=3)
        d.text((xc+vx*R-8, yc+vy*R-6), "N", fill=(255, 230, 0), font=fnt)
        d.text((xc-vx*R-8, yc-vy*R-18), "S", fill=(255, 230, 0), font=fnt)
    return im

def buscar_foto(nombre):
    cands = (glob.glob(os.path.join(_RAIZ, "fotos abril 2026", "fotos_con_nºmanchas", "*.png")) +
             glob.glob(os.path.join(_RAIZ, "joseluis_agosto_2024_ fotos del sol", "*.jpg")))
    key = nombre.lower().replace(" ", "")
    for c in cands:
        b = os.path.splitext(os.path.basename(c))[0].lower()
        b = b.replace("nºmanchas_", "").replace("limpia", "").replace(" ", "").replace("-copia", "")
        if key and (key in b or b in key):
            return c
    return None

# ======================= INTERFAZ =======================
st.title("\U0001F9ED Ejes y meridianos sobre una foto del Sol")
st.markdown(
    "Dibuja el **ecuador** (verde), los **paralelos heliográficos** (azul) y el "
    "**eje Norte–Sur** (amarillo) sobre una foto, con los mismos cálculos del TFG "
    "(la inversa $(\\Phi, L)\\to$ píxel). Necesita los datos de la observación: "
    "**µ**, **β_opt** y **λ☉**, además del centro y el radio del disco."
)

if not TIENE_CV2:
    st.warning("OpenCV no está disponible: la detección automática del disco no funcionará. "
               "Usa el centro y el radio manuales.")

modo = st.radio("¿Qué foto quieres usar?",
                ["Una foto de la base de datos de Lydia", "Subir mi propia foto"])

if modo.startswith("Una"):
    try:
        con = sqlite3.connect(RUTA_BD)
        filas = con.execute(
            "SELECT archivo_img, centro_x, centro_y, radio_sol, lambda_sol, mu_angulo, beta_optica "
            "FROM Observaciones WHERE mu_angulo IS NOT NULL AND lambda_sol IS NOT NULL "
            "ORDER BY archivo_img").fetchall()
        con.close()
    except Exception as e:
        st.error("No se pudo leer la base de datos: %s" % e); st.stop()

    if not filas:
        st.info("No hay observaciones con µ y λ☉ en la base de datos."); st.stop()

    fila_por_nombre = {f[0]: f for f in filas}
    # Las de abril (no empiezan por "S") salen primero -> foto de abril por defecto
    nombres = sorted(fila_por_nombre, key=lambda n: (n.startswith("S"), n))
    sel = st.selectbox("Observación (foto)", nombres)
    row = dict(zip(["archivo_img", "cx", "cy", "R", "lsol", "mu", "beta"],
                   fila_por_nombre[sel]))
    foto = buscar_foto(sel)
    if not foto:
        st.warning("La foto de esa observación no está en el repositorio. "
                   "Prueba con otra, o usa «Subir mi propia foto».")
        st.stop()

    img = Image.open(foto).convert("RGB")
    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) if TIENE_CV2 else None
    det = detectar_disco(bgr) if TIENE_CV2 else None
    if det:
        xc, yc, R = det
        st.caption("Disco detectado automáticamente: centro (%.0f, %.0f), radio %.0f px." % (xc, yc, R))
    else:
        xc, yc, R = float(row["cx"]), float(row["cy"]), float(row["R"])
        st.caption("Usando el centro y el radio guardados en la base de datos.")

    out = dibujar_ejes(img, xc, yc, R, float(row["lsol"]), float(row["mu"]), float(row["beta"]))
    c1, c2 = st.columns(2)
    c1.image(img, caption="Original", use_column_width=True)
    c2.image(out, caption="Con ejes y meridianos", use_column_width=True)
    st.caption("Datos usados — µ = %.2f°,  β_opt = %.2f°,  λ☉ = %.2f°." %
               (float(row["mu"]), float(row["beta"]), float(row["lsol"])))

else:
    up = st.file_uploader("Sube una foto del Sol (con el disco visible)",
                          type=["png", "jpg", "jpeg"])
    st.markdown("**Datos de la observación** (los mismos que calcula el código en el modo *f*):")
    cc1, cc2, cc3 = st.columns(3)
    mu_deg   = cc1.number_input("µ (grados)", value=0.0, format="%.2f")
    beta_deg = cc2.number_input("β_opt (grados)", value=0.0, format="%.2f")
    lsol_deg = cc3.number_input("λ☉ (grados)", value=30.0, format="%.2f")

    if up is not None:
        img = Image.open(up).convert("RGB")
        W, H = img.size
        auto = st.checkbox("Detectar el disco automáticamente", value=TIENE_CV2, disabled=not TIENE_CV2)
        xc = yc = R = None
        if auto and TIENE_CV2:
            bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            det = detectar_disco(bgr)
            if det:
                xc, yc, R = det
                st.caption("Disco detectado: centro (%.0f, %.0f), radio %.0f px." % (xc, yc, R))
            else:
                st.warning("No pude detectar el disco; introdúcelo a mano.")
        if xc is None:
            m1, m2, m3 = st.columns(3)
            xc = m1.number_input("Centro x (px)", value=float(W//2))
            yc = m2.number_input("Centro y (px)", value=float(H//2))
            R  = m3.number_input("Radio (px)", value=float(min(W, H)//2 - 5))
        out = dibujar_ejes(img, xc, yc, R, lsol_deg, mu_deg, beta_deg)
        c1, c2 = st.columns(2)
        c1.image(img, caption="Original", use_column_width=True)
        c2.image(out, caption="Con ejes y meridianos", use_column_width=True)
    else:
        st.info("Sube una foto para empezar.")
