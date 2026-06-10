# -*- coding: utf-8 -*-
"""
Figura comparativa: montura azimutal vs montura ecuatorial.
Izquierda: eje vertical (azimut) + eje horizontal (altura).
Derecha: eje polar inclinado a la latitud (paralelo al eje de la Tierra,
apunta al polo celeste) + eje de declinacion.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 7))

def suelo(ax, x0=-1.3, x1=1.3, y=0.0):
    ax.plot([x0, x1], [y, y], color='#6d4c41', lw=2, zorder=1)
    for x in np.linspace(x0, x1-0.12, 16):
        ax.plot([x, x-0.10], [y, y-0.10], color='#6d4c41', lw=1, zorder=1)

def tripode(ax, cx=0.0, top=0.22):
    # base sencilla del tripode
    for dx in (-0.32, 0.0, 0.32):
        ax.plot([cx, cx+dx], [top, 0.0], color='#555', lw=3, zorder=2)
    ax.plot([cx], [top], 'o', color='#444', ms=6, zorder=3)

def tubo(ax, x0, y0, ang_deg, L=0.62, color='#9e9e9e'):
    a = np.deg2rad(ang_deg)
    x1, y1 = x0 + L*np.cos(a), y0 + L*np.sin(a)
    ax.plot([x0, x1], [y0, y1], color=color, lw=13,
            solid_capstyle='round', zorder=4)
    # abertura (extremo abierto)
    ax.plot([x1], [y1], 'o', color='#cfcfcf', ms=15, zorder=5,
            markeredgecolor='#777', markeredgewidth=1.5)
    return x1, y1

def eje(ax, x0, y0, x1, y1, color, lw=4):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-',
                 color=color, lw=lw, zorder=3))

# =========================================================
# PANEL A: MONTURA AZIMUTAL
# =========================================================
suelo(axA); tripode(axA)
# eje vertical (azimut)
eje(axA, 0, 0.22, 0, 1.02, '#1565c0', lw=5)
axA.text(0.06, 0.62, 'Eje vertical\n(azimut)', color='#1565c0',
         fontsize=12, va='center', fontweight='bold')
# rotacion azimutal (elipse horizontal en la base)
arcA = Arc((0, 0.30), 0.7, 0.20, angle=0, theta1=0, theta2=320,
           color='#1565c0', lw=1.8, zorder=3)
axA.add_patch(arcA)
axA.annotate('', xy=(0.33, 0.33), xytext=(0.30, 0.24),
             arrowprops=dict(arrowstyle='-|>', color='#1565c0', lw=1.8))
# eje horizontal (altura) en lo alto
eje(axA, -0.30, 1.02, 0.30, 1.02, '#2e7d32', lw=5)
axA.text(-0.95, 1.06, 'Eje horizontal\n(altura)', color='#2e7d32',
         fontsize=12, va='bottom', fontweight='bold')
# arco de altura (vertical)
arcAlt = Arc((0, 1.02), 0.5, 0.5, angle=0, theta1=20, theta2=110,
             color='#2e7d32', lw=1.8, zorder=3)
axA.add_patch(arcAlt)
axA.annotate('', xy=(0.05, 1.27), xytext=(0.20, 1.18),
             arrowprops=dict(arrowstyle='-|>', color='#2e7d32', lw=1.8))
# tubo
tubo(axA, 0.0, 1.02, 58)
axA.set_title('Montura azimutal', fontsize=15, fontweight='bold', pad=12)
axA.text(0, -0.42, 'Los ejes son vertical y horizontal:\nse apunta con azimut y altura.',
         ha='center', va='top', fontsize=11, color='#333')

# =========================================================
# PANEL B: MONTURA ECUATORIAL
# =========================================================
suelo(axB); tripode(axB)
phi = 40  # latitud
a = np.deg2rad(phi)
# eje polar inclinado phi sobre el horizonte
px0, py0 = -0.05, 0.22
pL = 0.95
px1, py1 = px0 + pL*np.cos(a), py0 + pL*np.sin(a)
eje(axB, px0, py0, px1, py1, '#e65100', lw=5)
# etiqueta del eje polar, arriba a la izquierda con guia hacia el eje
axB.text(-0.05, 0.98, 'Eje polar\n($\\parallel$ eje de la Tierra)',
         color='#e65100', fontsize=12, va='bottom', ha='center', fontweight='bold')
axB.plot([0.02, 0.22], [0.90, 0.48], color='#e65100', lw=1, ls=(0,(2,2)), zorder=3)
# estrella polo celeste a donde apunta
axB.plot([px1+0.30], [py1+0.34], marker='*', color='#fbc02d', ms=24,
         markeredgecolor='#b8860b', zorder=6)
axB.text(px1+0.42, py1+0.34, 'Polo celeste', fontsize=11, va='center',
         ha='left', color='#555')
axB.annotate('', xy=(px1+0.24, py1+0.26), xytext=(px1, py1),
             arrowprops=dict(arrowstyle='-|>', color='#e65100', lw=1.6, ls=(0,(3,2))))
# angulo phi entre eje polar y horizonte
arcphi = Arc((px0, py0), 0.55, 0.55, angle=0, theta1=0, theta2=phi,
             color='black', lw=1.4)
axB.add_patch(arcphi)
axB.text(px0+0.30, py0+0.07, r'$\varphi$ = latitud', fontsize=12)
# linea de horizonte de referencia desde el pie del eje
axB.plot([px0, px0+0.5], [py0, py0], color='black', lw=1, ls=(0,(4,3)))
# rotacion ascension recta (alrededor del eje polar)
arcRA = Arc(((px0+px1)/2, (py0+py1)/2), 0.45, 0.20, angle=phi,
            theta1=0, theta2=320, color='#e65100', lw=1.8, zorder=3)
axB.add_patch(arcRA)
axB.text((px0+px1)/2-0.43, (py0+py1)/2-0.02, 'Ascensión\nrecta',
         color='#e65100', fontsize=11, va='center', ha='center', fontweight='bold')
# eje de declinacion (perpendicular al polar) en el extremo
dx, dy = np.cos(a+np.pi/2), np.sin(a+np.pi/2)
eje(axB, px1-0.32*dx, py1-0.32*dy, px1+0.32*dx, py1+0.32*dy, '#2e7d32', lw=5)
axB.text(px1-0.55*dx-0.05, py1-0.55*dy, 'Declinación', color='#2e7d32',
         fontsize=11, va='center', ha='center', fontweight='bold')
# tubo a lo largo del eje de declinacion
tubo(axB, px1, py1, phi+90, L=0.5)
# contrapeso al otro lado
cwx, cwy = px1 - 0.42*dx, py1 - 0.42*dy
axB.plot([px1, cwx], [py1, cwy], color='#555', lw=4, zorder=3)
axB.plot([cwx], [cwy], 'o', color='#333', ms=14, zorder=4)

axB.set_title('Montura ecuatorial', fontsize=15, fontweight='bold', pad=12)
axB.text(0.1, -0.42, 'El eje polar va inclinado a la latitud y apunta al polo:\n'
         'se apunta con ascensión recta y declinación.',
         ha='center', va='top', fontsize=11, color='#333')

axA.set_aspect('equal'); axA.axis('off')
axA.set_xlim(-1.4, 1.5); axA.set_ylim(-0.6, 1.75)
axB.set_aspect('equal'); axB.axis('off')
axB.set_xlim(-1.4, 1.95); axB.set_ylim(-0.6, 1.75)

plt.tight_layout()
OUT = r'C:\Users\lydia\Downloads\tfg\documentos explicacion\monturas_comparacion.png'
plt.savefig(OUT, dpi=150, bbox_inches='tight', facecolor='white')
print('Figura guardada:', OUT)
