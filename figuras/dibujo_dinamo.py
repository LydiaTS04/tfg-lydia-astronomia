# -*- coding: utf-8 -*-
"""
Figura 3: mecanismo del dinamo (efecto Omega -> tubo de flujo -> par de manchas).
Version propia, sin problemas de copyright.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc

fig, ax = plt.subplots(figsize=(9.5, 9))
ax.set_aspect('equal'); ax.axis('off')

R = 1.0
th = np.linspace(0, 2*np.pi, 400)
# Sol
ax.fill(R*np.cos(th), R*np.sin(th), color='#fff3cf', ec='#caa53a', lw=2, zorder=1)

# Eje N-S
ax.plot([0, 0], [-R*1.28, R*1.28], color='black', lw=2.2, zorder=3)
ax.text(0, R*1.33, 'N', ha='center', va='bottom', fontsize=17, fontweight='bold')
ax.text(0, -R*1.33, 'S', ha='center', va='top', fontsize=17, fontweight='bold')

# Rotacion diferencial: ecuador mas rapido
arc = Arc((0, R*1.10), 0.55, 0.20, angle=0, theta1=200, theta2=520, color='black', lw=1.5)
ax.add_patch(arc)
ax.annotate('', xy=(0.27, R*1.14), xytext=(0.20, R*1.03),
            arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5))

# Ecuador
ax.plot(R*np.cos(th), 0.28*R*np.sin(th), '--', color='#2e8b57', lw=1.4, zorder=2)

# ---- Campo TOROIDAL bajo la superficie (azul), arrollado cerca del ecuador ----
for yy in (0.06, -0.06):
    xb = np.linspace(-0.82, 0.82, 200)
    yb = yy + 0.10*np.sin(np.linspace(0, 3*np.pi, 200))*0.0 + yy*0  # base
    ax.plot(0.83*np.cos(th), 0.20*np.sin(th)+yy, color='#1f6fd0', lw=2.4,
            zorder=2, alpha=0.9)
ax.text(-0.86, 0.32, 'Campo toroidal\n(bajo la superficie)', color='#1f6fd0',
        fontsize=11, ha='right', va='center', fontweight='bold')
# flecha que indica el arrollado por la rotacion
ax.annotate('', xy=(0.55, 0.20), xytext=(0.15, 0.27),
            arrowprops=dict(arrowstyle='-|>', color='#1f6fd0', lw=1.6,
                            connectionstyle='arc3,rad=0.3'))

# ---- Tubo de flujo que EMERGE formando un arco (rojo) ----
# dos pies sobre la superficie cerca del ecuador, a la derecha
x1f, x2f = 0.30, 0.62
ysurf1 = np.sqrt(max(R**2 - x1f**2, 0))*0.28  # sobre la elipse ecuador (aprox)
# arco por encima de la superficie
t = np.linspace(0, np.pi, 100)
cxc = (x1f + x2f)/2
rad = (x2f - x1f)/2
ax.plot(cxc + rad*np.cos(t), 0.10 + 0.42*np.sin(t), color='#d62728', lw=3.2, zorder=6)
ax.annotate('', xy=(x2f, 0.12), xytext=(cxc, 0.52),
            arrowprops=dict(arrowstyle='-|>', color='#d62728', lw=2.2,
                            connectionstyle='arc3,rad=-0.3'), zorder=6)
ax.text(cxc+0.05, 0.60, 'Tubo de flujo\nque emerge', color='#d62728',
        fontsize=11, ha='left', va='bottom', fontweight='bold')

# ---- Par de manchas en los pies del tubo ----
for xf, pol, dx in [(x1f, '+', -0.02), (x2f, '$-$', 0.02)]:
    ax.plot([xf], [0.10], 'o', color='#3a2f10', ms=15, zorder=7)
    ax.text(xf+dx, 0.10, pol, color='white', fontsize=11, ha='center',
            va='center', zorder=8, fontweight='bold')
ax.annotate('Par de manchas\n(polaridad opuesta)', xy=(x2f, 0.06),
            xytext=(0.70, -0.30), fontsize=11, color='#3a2f10', fontweight='bold',
            ha='left', va='top',
            arrowprops=dict(arrowstyle='-|>', color='#3a2f10', lw=1.3))

ax.set_title('Mecanismo del dínamo: la rotación arrolla el campo\n'
             'y emerge formando las manchas', fontsize=14, fontweight='bold', pad=12)
ax.set_xlim(-1.6, 1.7); ax.set_ylim(-1.55, 1.55)

OUT = r'C:\Users\lydia\Downloads\tfg\documentos explicacion\dinamo_manchas.png'
plt.savefig(OUT, dpi=150, bbox_inches='tight', facecolor='white')
print('Figura 3 guardada:', OUT)
