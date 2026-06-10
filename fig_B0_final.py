# -*- coding: utf-8 -*-
"""
Figura B0 FINAL: por equinoccios/solsticios, lambda_sol en RADIANES (pi),
colores cuidados, B0 una sola vez por momento.
Texto sin acentos (matplotlib); acentos en el \\caption del TFG.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

plt.rcParams['font.family'] = 'DejaVu Sans'
I = 7.25
EXAG = 3.0
# --- paleta cuidada (sin grises) ---
CN  = '#ef7a18'   # NORTE (naranja fuerte)
CS  = '#2a72c0'   # SUR (azul fuerte)
CNn = '#f4a460'   # casi de canto, ligero N (naranja claro)
CSs = '#86a9d4'   # casi de canto, ligero S (azul claro)
GEQ = '#1b7d1b'   # ecuador (verde)
GCM = '#0094c8'   # meridiano central (azul nitido)
GFA = '#cf9b46'   # rejilla fina (dorado calido)
POL = '#15357e'   # polos (azul marino)
DISK= '#ffe1a8'; DISKE='#e0902a'

PHI0 = np.radians(82+44/60+53.56/3600); LN = np.radians(-13-52/60-21.41/3600)
def B0deg(l): return np.degrees(np.arcsin(np.clip(np.cos(PHI0)*np.cos(np.radians(l+180)-LN), -1, 1)))

ea, eb = 6.0, 3.6
def P(l, k=1.0):
    a = np.radians(l); return k*ea*np.cos(a), k*eb*np.sin(a)

fig = plt.figure(figsize=(12.8, 10.6))
gs = gridspec.GridSpec(2, 4, height_ratios=[1.6, 1.0], hspace=0.16, wspace=0.18)

# ===================== ARRIBA =====================
ax = fig.add_subplot(gs[0, :]); ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-10.8, 10.8); ax.set_ylim(-6.0, 6.4)

# tramos: NORTE lambda in [76,256]
aN = np.radians(np.linspace(76, 256, 200)); aS = np.radians(np.linspace(256, 436, 200))
ax.plot(ea*np.cos(aN), eb*np.sin(aN), color=CN, lw=7, solid_capstyle='round', zorder=2)
ax.plot(ea*np.cos(aS), eb*np.sin(aS), color=CS, lw=7, solid_capstyle='round', zorder=2)

# Sol
ax.add_patch(plt.Circle((0, 0), 0.62, color='#ffcc33', ec='#e8a000', lw=1.4, zorder=5))
for k in range(12):
    a = k*np.pi/6
    ax.plot([0.7*np.cos(a), 0.92*np.cos(a)], [0.7*np.sin(a), 0.92*np.sin(a)], color='#ffcc33', lw=1.6, zorder=4)
# eje de rotacion del Sol (orientacion)
g = np.radians(I); axu, axv = np.sin(g), np.cos(g)
ax.plot([-1.25*axu, 1.25*axu], [-1.25*axv, 1.25*axv], color=POL, lw=2.2, zorder=6)
ax.text(1.25*axu+0.02, 1.25*axv+0.04, 'N', color=POL, fontsize=10, fontweight='bold', ha='center', va='bottom')
ax.text(-1.25*axu, -1.25*axv-0.06, 'S', color=POL, fontsize=9, fontweight='bold', ha='center', va='top')
ax.text(1.0, -0.78, 'eje del Sol', color=POL, fontsize=7.5, style='italic')

# nodos del ecuador solar (B0=0): en lambda_sol = 76 y 256 (NO en los equinoccios)
for l in (76, 256):
    x, y = P(l)
    ax.plot([0.93*x, 1.07*x], [0.93*y, 1.07*y], color='#666', lw=1.3, zorder=3)
    ax.text(*P(l, 1.15), 'nodo\n$(B_0=0)$', color='#666', fontsize=8,
            ha='center', va='center', linespacing=1.1)

# 4 momentos (equinoccios/solsticios)
mom = [
    ('Eq. primavera', 0,   r'\lambda_\odot=0', CS),
    ('Sols. verano',  90,  r'\lambda_\odot=\pi/2',        CNn),
    ('Eq. otoño',     180, r'\lambda_\odot=\pi',          CN),
    ('Sols. invierno',270, r'\lambda_\odot=3\pi/2',       CSs),
]
for nom, l, lam, col in mom:
    b = B0deg(l)
    polo = 'polo NORTE' if b > 3 else ('polo SUR' if b < -3 else 'ecuador casi recto')
    if l == 0:     pre = r'$\gamma$ (Aries)' + '\n'
    elif l == 180: pre = r'$\Omega$ (otoño)' + '\n'
    else:          pre = ''
    x, y = P(l)
    ax.plot(x, y, 'o', color='#2b6cff', ms=13, mec='white', mew=1.5, zorder=7)
    ax.text(*P(l, 1.52), '%s%s\n$%s$\n$B_0\\approx%+.1f^\\circ$  (%s)' % (pre, nom, lam, b, polo),
            ha='center', va='center', fontsize=9.6, color=col, fontweight='bold', linespacing=1.35)

# etiquetas DENTRO de la elipse, junto a cada tramo (dicen cuando se ve cada polo)
ax.text(*P(143, 0.66), 'en este tramo\nse ve el polo\nNORTE  ($B_0>0$)',
        ha='center', va='center', color=CN, fontsize=9.5, fontweight='bold', linespacing=1.25)
ax.text(*P(323, 0.66), 'en este tramo\nse ve el polo\nSUR  ($B_0<0$)',
        ha='center', va='center', color=CS, fontsize=9.5, fontweight='bold', linespacing=1.25)

ax.text(0, 6.1, 'Visibilidad de los polos a lo largo del anio  '
        r'($\lambda_\odot$ en radianes)', ha='center', fontsize=13.5, fontweight='bold', color='#222')
# (la nota de los maximos de B0 va en el caption / la teoria)

# ===================== ABAJO: discos (solo nombre, sin repetir B0) =====================
def disco(axx, b0):
    axx.set_aspect('equal'); axx.axis('off'); axx.set_xlim(-1.2, 1.2); axx.set_ylim(-1.4, 1.2)
    B0r = np.radians(b0*EXAG)
    axx.add_patch(plt.Circle((0, 0), 1.0, color=DISK, ec=DISKE, lw=1.6, zorder=2))
    lam = np.radians(np.linspace(-90, 90, 130))
    for pd in (-60, -30, 0, 30, 60):
        ph = np.radians(pd); X = np.cos(ph)*np.sin(lam); Y = np.sin(ph)*np.cos(B0r)-np.cos(ph)*np.sin(B0r)*np.cos(lam)
        axx.plot(X, Y, color=(GEQ if pd == 0 else GFA), lw=(2.6 if pd == 0 else 1.0),
                 alpha=(1 if pd == 0 else 0.7), zorder=3)
    ph = np.radians(np.linspace(-90, 90, 130))
    for l0 in (-60, -30, 0, 30, 60):
        lr = np.radians(l0); X = np.cos(ph)*np.sin(lr); Y = np.sin(ph)*np.cos(B0r)-np.cos(ph)*np.sin(B0r)*np.cos(lr)
        axx.plot(X, Y, color=(GCM if l0 == 0 else GFA), lw=(2.0 if l0 == 0 else 1.0),
                 alpha=(1 if l0 == 0 else 0.7), zorder=3)
    if B0r > 0.01: axx.plot(0, np.cos(B0r), 'o', color=POL, ms=8, zorder=5); axx.text(0, np.cos(B0r)+0.1, 'N', color=POL, fontsize=12, fontweight='bold', ha='center')
    if B0r < -0.01: axx.plot(0, -np.cos(B0r), 'o', color=POL, ms=8, zorder=5); axx.text(0, -np.cos(B0r)-0.2, 'S', color=POL, fontsize=12, fontweight='bold', ha='center')

orden = [('Eq. primavera', 0, CS), ('Sols. verano', 90, CNn), ('Eq. otoño', 180, CN), ('Sols. invierno', 270, CSs)]
for i, (nom, l, col) in enumerate(orden):
    axx = fig.add_subplot(gs[1, i]); disco(axx, B0deg(l))
    axx.text(0, -1.25, nom, ha='center', fontsize=10.5, color=col, fontweight='bold')

fig.text(0.5, 0.40, 'Lo que se ve desde la Tierra', ha='center', fontsize=11.5, fontweight='bold', color='#222')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion', 'fig_B0_final.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
