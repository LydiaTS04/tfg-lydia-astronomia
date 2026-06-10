# -*- coding: utf-8 -*-
"""
Figura 24 (TFG): orientacion del eje solar a lo largo del anio.
El eje del Sol esta inclinado I=7,25 deg y apunta SIEMPRE igual; segun donde este
la Tierra en su orbita, la latitud del centro del disco B0 oscila entre -I y +I.
Texto sin acentos a proposito (matplotlib); los acentos van en el \\caption del TFG.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Wedge

plt.rcParams['font.family'] = 'DejaVu Sans'
I = 7.25
g = np.radians(I)

fig, ax = plt.subplots(figsize=(11.8, 7.8))
ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-8.4, 8.4); ax.set_ylim(-5.2, 6.6)

# ---- orbita de la Tierra ----
A, B = 5.6, 2.7
th = np.linspace(0, 2*np.pi, 300)
ax.plot(A*np.cos(th), B*np.sin(th), color='#888', lw=1.2, ls='--', zorder=1)
ax.text(0, -B-0.45, 'orbita de la Tierra (ecliptica)', ha='center',
        color='#666', fontsize=9, style='italic')

# ---- Sol central, eje FIJO inclinado I ----
Rs = 0.95
ax.add_patch(plt.Circle((0, 0), Rs, color='#ffae42', zorder=3, ec='#e07b00', lw=1.5))
L = 1.75
ux, uy = np.sin(g), np.cos(g)
ax.plot([-L*ux, L*ux], [-L*uy, L*uy], color='#1a3b8b', lw=3, zorder=4)
ax.text(L*ux+0.06, L*uy+0.05, 'N', color='#1a3b8b', fontsize=15, fontweight='bold', va='bottom')
ax.text(-L*ux-0.06, -L*uy-0.05, 'S', color='#1a3b8b', fontsize=15, fontweight='bold', va='top')
ex, ey = np.cos(g), -np.sin(g)
ax.plot([-Rs*ex, Rs*ex], [-Rs*ey, Rs*ey], color='w', lw=1.6, zorder=4)
ax.text(0, -2.05, 'eje fijo  I = 7,25 deg', ha='center', color='#1a3b8b', fontsize=9)

# ---- 4 posiciones de la Tierra (el eje se inclina hacia +x = sep) ----
casos = [
    dict(ang=0,   lam=166, fecha='~8 sep', B0=+I, polo='NORTE',    col='#d62728', mp=(7.6, 1.1)),
    dict(ang=90,  lam=256, fecha='~7 dic', B0=0,  polo='de canto', col='#555',    mp=(4.9, 3.7)),
    dict(ang=180, lam=346, fecha='~8 mar', B0=-I, polo='SUR',      col='#1f77b4', mp=(-7.6, 1.1)),
    dict(ang=270, lam=76,  fecha='~6 jun', B0=0,  polo='de canto', col='#555',    mp=(-4.9, -4.0)),
]

def mini(cx, cy, B0, EXAG=3.2, r=0.66):
    """Sol visto desde la Tierra: ecuador (verde) inclinado segun B0 (exagerado)."""
    ax.add_patch(plt.Circle((cx, cy), r, color='#ffd27f', ec='#e07b00', lw=1.3, zorder=6))
    sb = np.sin(np.radians(B0)) * EXAG
    off = -r*sb*0.7                      # el ecuador se desplaza al ver mas un hemisferio
    ev = r*abs(sb)
    if ev > 0.03:
        ax.add_patch(Ellipse((cx, cy+off), 2*r*0.97, 2*ev, fill=False,
                             color='#2e7d32', lw=2.2, zorder=7))
        # casquete del polo visible, sombreado
        if B0 > 0:
            ax.add_patch(Wedge((cx, cy), r, 0, 180, width=r*0.33, color='#9ecae1', alpha=0.6, zorder=6.5))
            ax.plot(cx, cy+r*0.7, 'o', color='#1a3b8b', ms=5, zorder=8)
            ax.text(cx, cy+r*0.78, 'N', color='#1a3b8b', fontsize=11, fontweight='bold', ha='center', va='bottom')
        else:
            ax.add_patch(Wedge((cx, cy), r, 180, 360, width=r*0.33, color='#9ecae1', alpha=0.6, zorder=6.5))
            ax.plot(cx, cy-r*0.7, 'o', color='#1a3b8b', ms=5, zorder=8)
            ax.text(cx, cy-r*0.78, 'S', color='#1a3b8b', fontsize=11, fontweight='bold', ha='center', va='top')
    else:
        ax.plot([cx-r*0.97, cx+r*0.97], [cy, cy], color='#2e7d32', lw=2.2, zorder=7)

for c in casos:
    a = np.radians(c['ang'])
    tx, ty = A*np.cos(a), B*np.sin(a)
    ax.annotate('', xy=(0, 0), xytext=(tx, ty),
                arrowprops=dict(arrowstyle='-', color='#2b6cff', lw=1, ls=':'), zorder=2)
    ax.plot(tx, ty, 'o', color='#2b6cff', ms=13, zorder=5, mec='white', mew=1.2)
    mx, my = c['mp']
    ax.annotate('', xy=(mx, my), xytext=(tx, ty),
                arrowprops=dict(arrowstyle='-', color='#ccc', lw=0.8), zorder=2)
    mini(mx, my, c['B0'])
    txt = '%s  (lambda_Sol ~ %d deg)\nB0 = %+.2f deg\nse ve el polo %s' % (
        c['fecha'], c['lam'], c['B0'], c['polo'])
    dy = 1.15 if my > 0 else -1.15
    va = 'bottom' if dy > 0 else 'top'
    ax.text(mx, my+dy, txt, ha='center', va=va, fontsize=9.5, color=c['col'],
            fontweight='bold' if c['B0'] != 0 else 'normal', linespacing=1.3)

ax.text(0, 6.25, 'Orientacion del eje solar a lo largo del anio',
        ha='center', fontsize=13.5, fontweight='bold', color='#222')
ax.text(0, 5.75, 'El eje esta FIJO (I = 7,25 deg); B0 oscila entre -I y +I segun la fecha',
        ha='center', fontsize=10, color='#444')
ax.text(7.6, -0.9, '(inclinacion del\necuador exagerada)', ha='center', va='top',
        fontsize=7.5, color='#999', style='italic')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion',
                   'fig24_B0_orientacion_anual.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
