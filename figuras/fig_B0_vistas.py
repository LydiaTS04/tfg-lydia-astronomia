# -*- coding: utf-8 -*-
"""
Figura "vistas": desde donde esta la Tierra en cada momento y QUE VE.
Por equinoccios/solsticios, lambda_sol en RADIANES, colores cuidados, B0 una vez.
Texto sin acentos (matplotlib); acentos en el \\caption del TFG.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'DejaVu Sans'
I = 7.25
EXAG = 3.0
CN  = '#ef7a18'; CS = '#2a72c0'; CNn = '#f4a460'; CSs = '#86a9d4'
GEQ = '#1b7d1b'; GCM = '#0094c8'; GFA = '#cf9b46'; POL = '#15357e'
DISK= '#ffe1a8'; DISKE='#e0902a'

PHI0 = np.radians(82+44/60+53.56/3600); LN = np.radians(-13-52/60-21.41/3600)
def B0deg(l): return np.degrees(np.arcsin(np.clip(np.cos(PHI0)*np.cos(np.radians(l+180)-LN), -1, 1)))

ea, eb = 5.0, 3.0
def P(l, k=1.0):
    a = np.radians(l); return k*ea*np.cos(a), k*eb*np.sin(a)

fig, ax = plt.subplots(figsize=(13.0, 10.0))
ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-13.3, 13.3); ax.set_ylim(-7.6, 8.2)

# orbita + Sol
t = np.linspace(0, 2*np.pi, 300)
ax.plot(ea*np.cos(t), eb*np.sin(t), '--', color='#b0b0b0', lw=1.2, zorder=1)
ax.add_patch(plt.Circle((0, 0), 0.6, color='#ffcc33', ec='#e8a000', lw=1.4, zorder=4))
for k in range(12):
    a = k*np.pi/6
    ax.plot([0.7*np.cos(a), 0.92*np.cos(a)], [0.7*np.sin(a), 0.92*np.sin(a)], color='#ffcc33', lw=1.6, zorder=3)
# eje de rotacion del Sol (orientacion)
g = np.radians(I); axu, axv = np.sin(g), np.cos(g)
ax.plot([-1.2*axu, 1.2*axu], [-1.2*axv, 1.2*axv], color=POL, lw=2.2, zorder=5)
ax.text(1.2*axu+0.02, 1.2*axv+0.04, 'N', color=POL, fontsize=10, fontweight='bold', ha='center', va='bottom')
ax.text(-1.2*axu, -1.2*axv-0.06, 'S', color=POL, fontsize=9, fontweight='bold', ha='center', va='top')
ax.text(1.0, -0.4, 'eje del Sol', color=POL, fontsize=7.5, style='italic')

# disco que ve la Tierra
def disco_en(cx, cy, r, b0):
    B0r = np.radians(b0*EXAG)
    ax.add_patch(plt.Circle((cx, cy), r, color=DISK, ec=DISKE, lw=1.5, zorder=6))
    lam = np.radians(np.linspace(-90, 90, 110))
    for pd in (-60, -30, 0, 30, 60):
        ph = np.radians(pd); X = np.cos(ph)*np.sin(lam); Y = np.sin(ph)*np.cos(B0r)-np.cos(ph)*np.sin(B0r)*np.cos(lam)
        ax.plot(cx+r*X, cy+r*Y, color=(GEQ if pd == 0 else GFA), lw=(2.2 if pd == 0 else 0.9),
                alpha=(1 if pd == 0 else 0.7), zorder=7)
    ph = np.radians(np.linspace(-90, 90, 110))
    for l0 in (-60, -30, 0, 30, 60):
        lr = np.radians(l0); X = np.cos(ph)*np.sin(lr); Y = np.sin(ph)*np.cos(B0r)-np.cos(ph)*np.sin(B0r)*np.cos(lr)
        ax.plot(cx+r*X, cy+r*Y, color=(GCM if l0 == 0 else GFA), lw=(1.6 if l0 == 0 else 0.9),
                alpha=(1 if l0 == 0 else 0.7), zorder=7)
    if B0r > 0.01:
        ax.plot(cx, cy+r*np.cos(B0r), 'o', color=POL, ms=6, zorder=8)
        ax.text(cx, cy+r*np.cos(B0r)+0.18, 'N', color=POL, fontsize=11, fontweight='bold', ha='center')
    elif B0r < -0.01:
        ax.plot(cx, cy-r*np.cos(B0r), 'o', color=POL, ms=6, zorder=8)
        ax.text(cx, cy-r*np.cos(B0r)-0.3, 'S', color=POL, fontsize=11, fontweight='bold', ha='center')

# 4 momentos en equinoccios/solsticios
mom = [
    ('Eq. primavera', 0,   r'\lambda_\odot=0', 've el polo SUR',  CS),
    ('Sols. verano',  90,  r'\lambda_\odot=\pi/2',        've el ecuador casi recto', CNn),
    ('Eq. otoño',     180, r'\lambda_\odot=\pi',          've el polo NORTE', CN),
    ('Sols. invierno',270, r'\lambda_\odot=3\pi/2',       've el ecuador casi recto', CSs),
]
rd = 1.15
GAP = 0.55                                  # separacion disco-eclptica (pequena)
for nom, l, lam, ve, col in mom:
    b = B0deg(l)
    ex, ey = P(l)                           # Tierra sobre la orbita
    h = np.hypot(ex, ey); ux, uy = ex/h, ey/h
    px, py = -uy, ux                        # perpendicular a la visual
    dcx, dcy = ex+ux*(rd+GAP), ey+uy*(rd+GAP)   # disco justo fuera de la eclptica
    ax.annotate('', xy=(0, 0), xytext=(ex, ey), arrowprops=dict(arrowstyle='-|>', color='#2b6cff', lw=1.5), zorder=4)
    ax.plot(ex, ey, 'o', color='#2b6cff', ms=12, mec='white', mew=1.5, zorder=9)
    ax.text(ex+px*0.6, ey+py*0.6, 'Tierra', color='#2b6cff', fontsize=8.5, ha='center', va='center')
    disco_en(dcx, dcy, rd, b)
    # etiqueta: solsticios (arriba/abajo) -> AL LADO ; equinoccios (izq/der) -> pegada al disco hacia fuera
    if l == 90:    lx, ly, ha = dcx - 3.9, dcy, 'center'
    elif l == 270: lx, ly, ha = dcx + 3.9, dcy, 'center'
    elif l == 0:   lx, ly, ha = dcx + rd + 0.4, dcy, 'left'
    else:          lx, ly, ha = dcx - rd - 0.4, dcy, 'right'
    ax.text(lx, ly, '%s  ($%s$)\n$B_0\\approx%+.1f^\\circ$\n%s' % (nom, lam, b, ve),
            ha=ha, va='center', fontsize=9.6, color=col, fontweight='bold', linespacing=1.35)

# ---- inset esquina: QUE ES B0 (VISTA LATERAL) ----
from matplotlib.patches import Arc, Wedge
icx, icy, ir = -10.0, 5.1, 0.85
b0d = np.radians(25)                        # exagerado para la definicion
ax.add_patch(plt.Rectangle((icx-3.0, icy-2.4), 5.4, 4.9, facecolor='#f7f7f7',
             edgecolor='#bbb', lw=1.0, zorder=10))
ax.text(icx-0.2, icy+2.15, 'Que es $B_0$  (vista lateral)', ha='center', va='center',
        fontsize=9.5, fontweight='bold', color='#222', zorder=14)
# Sol
ax.add_patch(plt.Circle((icx, icy), ir, color=DISK, ec=DISKE, lw=1.3, zorder=11))
# hemisferio norte (el que se ve) sombreado
ax.add_patch(Wedge((icx, icy), ir, np.degrees(b0d), 180+np.degrees(b0d), color='#bcd6ee', alpha=0.55, zorder=11))
# eje N-S (norte inclinado hacia la Tierra, a la izquierda)
n = np.array([-np.sin(b0d), np.cos(b0d)])
ax.plot([icx-1.35*ir*n[0], icx+1.35*ir*n[0]], [icy-1.35*ir*n[1], icy+1.35*ir*n[1]], color=POL, lw=2, zorder=12)
ax.text(icx+1.35*ir*n[0]-0.12, icy+1.35*ir*n[1], 'N', color=POL, fontsize=9, fontweight='bold', va='bottom', zorder=13)
# ecuador solar (perpendicular al eje) visto de canto
e = np.array([np.cos(b0d), np.sin(b0d)])
ax.plot([icx-1.25*ir*e[0], icx+1.25*ir*e[0]], [icy-1.25*ir*e[1], icy+1.25*ir*e[1]], color=GEQ, lw=2.2, zorder=12)
ax.text(icx+1.25*ir*e[0]+0.1, icy+1.25*ir*e[1]+0.05, 'ecuador', color=GEQ, fontsize=7, ha='left', zorder=12)
# Tierra + visual (horizontal)
ax.plot(icx-2.45, icy, 'o', color='#2b6cff', ms=6, zorder=12)
ax.text(icx-2.45, icy-0.4, 'Tierra', color='#2b6cff', fontsize=7, ha='center', zorder=12)
ax.annotate('', xy=(icx-ir, icy), xytext=(icx-2.3, icy),
            arrowprops=dict(arrowstyle='-|>', color='#2b6cff', lw=1.4), zorder=12)
ax.plot([icx-1.25*ir, icx+1.25*ir], [icy, icy], color='#2b6cff', lw=0.8, ls=':', zorder=11)
# arco B0 entre la visual (horizontal) y el ecuador
ax.add_patch(Arc((icx, icy), 1.7*ir, 1.7*ir, angle=0, theta1=0, theta2=np.degrees(b0d),
            color='#d62728', lw=1.8, zorder=13))
ax.text(icx+ir*1.0, icy+ir*0.28, '$B_0$', color='#d62728', fontsize=11, fontweight='bold', zorder=13)
ax.text(icx-0.2, icy-2.0, '$B_0$ = angulo entre la visual\ny el ecuador (latitud del centro)',
        ha='center', va='center', fontsize=7.3, color='#333', zorder=12, linespacing=1.2)

ax.text(0, 7.95, 'Desde donde esta la Tierra en cada momento y que ve del Sol',
        ha='center', fontsize=13.5, fontweight='bold', color='#222')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion', 'fig_B0_vistas.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
