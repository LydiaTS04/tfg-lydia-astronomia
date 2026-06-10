# -*- coding: utf-8 -*-
"""
Figura 2 (sugerida): esfera solar con eje de rotacion y flechas de velocidad,
mas largas en el ecuador que cerca de los polos -> rotacion diferencial.

La longitud de cada flecha es proporcional a la velocidad lineal de rotacion
   v(phi) = omega(phi) * R cos(phi),  con  omega(phi) = A + B sin^2(phi)
usando los valores medidos por Lydia (A = 14.01, B = -2.60).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc

# Ley de rotacion medida
A_FIT, B_FIT = 14.01, -2.60
def omega(phi_deg):
    p = np.deg2rad(phi_deg)
    return A_FIT + B_FIT*np.sin(p)**2
def v_lineal(phi_deg):
    return omega(phi_deg) * np.cos(np.deg2rad(phi_deg))   # ~ omega * R cos phi (R=1)

fig, ax = plt.subplots(figsize=(9.5, 9))
ax.set_aspect('equal'); ax.axis('off')

R = 1.0
theta = np.linspace(0, 2*np.pi, 400)
k = 0.32   # achatamiento de las elipses (perspectiva 3D)

# Esfera
ax.fill(R*np.cos(theta), R*np.sin(theta), color='#fff6d6', ec='#caa53a', lw=2, zorder=1)

# Eje N-S
ax.plot([0, 0], [-R*1.30, R*1.30], color='black', lw=2.4, zorder=3)
ax.text(0, R*1.36, 'N', ha='center', va='bottom', fontsize=18, fontweight='bold')
ax.text(0, -R*1.36, 'S', ha='center', va='top', fontsize=18, fontweight='bold')

# Rotacion (curva arriba)
arc_rot = Arc((0, R*1.14), 0.55, 0.22, angle=0, theta1=200, theta2=520, color='black', lw=1.6, zorder=4)
ax.add_patch(arc_rot)
ax.annotate('', xy=(0.27, R*1.18), xytext=(0.20, R*1.07),
            arrowprops=dict(arrowstyle='-|>', color='black', lw=1.6))

# Latitudes a dibujar (con su flecha de velocidad)
lats = [0, 25, 45, 62, 78]
vmax = v_lineal(0)            # normalizacion (ecuador = mas larga)
LMAX = 0.62                   # longitud de flecha del ecuador

for lat in lats:
    for s in ([0] if lat == 0 else [1, -1]):   # hemisferio N y S (el ecuador una vez)
        phi = s*lat
        yL = R*np.sin(np.deg2rad(phi))
        rL = R*np.cos(np.deg2rad(phi))
        # circulo de latitud (elipse) tenue
        col = '#2e8b57' if lat == 0 else '#cfa9dd'
        lw  = 1.7 if lat == 0 else 1.1
        ls  = '--' if lat == 0 else ':'
        ax.plot(rL*np.cos(theta), k*rL*np.sin(theta)+yL, ls, color=col, lw=lw, zorder=2)
        # punto en el frente de la latitud (parte inferior de la elipse, mirando al lector)
        px, py = 0.0, yL - k*rL
        # flecha de velocidad: horizontal hacia la derecha (sentido de giro)
        Lf = LMAX * v_lineal(phi)/vmax
        ax.add_patch(FancyArrowPatch((px, py), (px+Lf, py),
                     arrowstyle='-|>', mutation_scale=18, color='#c0392b', lw=3.0, zorder=6))
        ax.plot([px], [py], 'o', color='black', ms=4.5, zorder=7)

# Etiquetas de velocidad ecuador vs polo
ax.text(LMAX+0.05, -k*R-0.0, r'$v_{\rm ecuador}$  (máxima)', color='#c0392b',
        fontsize=12, va='center', fontweight='bold')
yhi = R*np.sin(np.deg2rad(78))
ax.text(LMAX*v_lineal(78)/vmax+0.06, yhi-k*np.cos(np.deg2rad(78))*R, r'$v_{\rm polo}\!\to 0$',
        color='#c0392b', fontsize=11, va='center')

# Ecuador etiqueta
ax.text(-R*0.93, 0.06, 'Ecuador', color='#2e8b57', fontsize=12, style='italic')

ax.set_title('Rotación diferencial: el ecuador gira más rápido que los polos',
             fontsize=15, fontweight='bold', pad=16)

ax.set_xlim(-1.5, 1.9); ax.set_ylim(-1.7, 1.6)

OUT = r'C:\Users\lydia\Downloads\tfg\documentos explicacion\rotacion_diferencial_flechas.png'
plt.savefig(OUT, dpi=150, bbox_inches='tight', facecolor='white')
print('Figura 2 guardada:', OUT)
