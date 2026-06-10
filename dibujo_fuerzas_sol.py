# -*- coding: utf-8 -*-
"""
Figura 1: Fuerzas que rompen la rotacion rigida del Sol
Version SIN cuadro de texto, ajustada:
  - flecha -1/rho grad P exactamente radial hacia afuera (opuesta a g)
  - g con etiqueta separada
  - etiqueta de conveccion debajo de las flechas (sin solapar)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc

fig, ax = plt.subplots(figsize=(9, 9))
ax.set_aspect('equal'); ax.axis('off')

R = 1.0
theta = np.linspace(0, 2*np.pi, 400)

# Esfera
ax.fill(R*np.cos(theta), R*np.sin(theta), color='#fdf3d0', ec='#caa53a', lw=2, zorder=1)

# Eje N-S
ax.plot([0, 0], [-R*1.28, R*1.28], color='black', lw=2.2, zorder=3)
ax.text(0, R*1.34, 'N', ha='center', va='bottom', fontsize=18, fontweight='bold')
ax.text(0, -R*1.34, 'S', ha='center', va='top', fontsize=18, fontweight='bold', color='black')

# Rotacion omega(phi)
arc_rot = Arc((0, R*1.12), 0.55, 0.22, angle=0, theta1=200, theta2=520, color='black', lw=1.6, zorder=4)
ax.add_patch(arc_rot)
ax.annotate('', xy=(0.27, R*1.16), xytext=(0.20, R*1.05),
            arrowprops=dict(arrowstyle='-|>', color='black', lw=1.6))
ax.text(0.42, R*1.15, r'$\omega(\phi)$', fontsize=15, va='center')

# Ecuador
ax.plot(R*np.cos(theta), 0.30*R*np.sin(theta), '--', color='#2e8b57', lw=1.6, zorder=2)
ax.text(R*0.60, -0.205*R, 'Ecuador', color='#2e8b57', fontsize=12, style='italic')

# Latitud de M
phi = np.deg2rad(33)
yM = R*np.sin(phi); rM = R*np.cos(phi)
ax.plot(rM*np.cos(theta), 0.30*rM*np.sin(theta)+yM, ':', color='#c39bd3', lw=1.3, zorder=2)
Mx, My = rM, yM
ax.plot([Mx], [My], 'o', color='black', ms=7, zorder=8)
ax.text(Mx+0.02, My+0.085, r'$dm$', fontsize=15, fontweight='bold')

# r = R cos phi
ax.annotate('', xy=(Mx, My), xytext=(0, My),
            arrowprops=dict(arrowstyle='-', color='#e8308a', lw=2.2))
ax.text(Mx*0.45, My+0.07, r'$r = R\cos\phi$', color='#e8308a', fontsize=13, ha='center')

# R_sol (centro a M, gris discontinuo)
ax.annotate('', xy=(Mx, My), xytext=(0, 0),
            arrowprops=dict(arrowstyle='-', color='#aaaaaa', lw=1.0, ls=(0,(4,3))))
ax.text(Mx*0.30, My*0.30-0.02, r'$R_\odot$', color='#888888', fontsize=12, ha='center')

# angulo phi
arc_phi = Arc((0, 0), 0.60, 0.60, angle=0, theta1=0, theta2=np.rad2deg(phi), color='black', lw=1.2)
ax.add_patch(arc_phi)
ax.text(0.35, 0.11, r'$\phi$', fontsize=14)

# ===== Vectores en M =====
gnorm = np.hypot(Mx, My)
ur = np.array([Mx/gnorm, My/gnorm])         # unitario radial (centro -> M, hacia afuera)
ut = np.array([My/gnorm, -Mx/gnorm])        # unitario tangente hacia el ecuador

def vec(d, color, lw=2.6, ms=20):
    ax.add_patch(FancyArrowPatch((Mx, My), (Mx+d[0], My+d[1]),
                 arrowstyle='-|>', mutation_scale=ms, color=color, lw=lw, zorder=7))

# omega^2 r : perpendicular al eje, hacia afuera (horizontal)
vec(np.array([0.58, 0.0]), '#f08000')
ax.text(Mx+0.62, My+0.0, 'Centrífuga\n' r'$\omega^2 r$', color='#f08000',
        fontsize=12.5, va='center', fontweight='bold')

# g : radial hacia el centro
vec(-0.46*ur, '#1f6fd0')
ax.text(0.20, 0.45, 'Gravedad ' r'$\vec{g}$',
        color='#1f6fd0', fontsize=12.5, va='center', ha='right', fontweight='bold')

# -1/rho grad P : radial hacia AFUERA (exactamente opuesta a g)
vec(0.46*ur, '#8e44ad', lw=2.3)
ax.text(Mx+0.46*ur[0]+0.04, My+0.46*ur[1]+0.10, 'Gradiente de presión\n' r'$-\dfrac{1}{\rho}\nabla P$',
        color='#8e44ad', fontsize=12, va='bottom', ha='left', fontweight='bold')

# Componente tangencial (hacia el ecuador)
vec(0.38*ut, '#d62728', lw=2.4)
ax.text(Mx+0.44, My-0.36, 'Componente tangencial\n(hacia el ecuador)',
        color='#d62728', fontsize=11, fontweight='bold', va='top')

ax.set_title('Fuerzas que rompen la rotación rígida del Sol', fontsize=15, fontweight='bold', pad=14)
ax.set_xlim(-1.7, 2.35); ax.set_ylim(-1.75, 1.65)

OUT = r'C:\Users\lydia\Downloads\tfg\documentos explicacion\fuerzas_sol_gas_SIN_TEXTO.png'
plt.savefig(OUT, dpi=150, bbox_inches='tight', facecolor='white')
print('Figura 1 guardada:', OUT)
