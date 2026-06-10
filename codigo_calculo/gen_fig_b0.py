# -*- coding: utf-8 -*-
"""Genera el diagrama del B_0 a lo largo del anyo (4 posiciones de la Tierra).
Esquema conceptual: eje solar fijo e inclinado I=7,25 (exagerado en el dibujo),
y la latitud del centro del disco B_0 oscilando entre -I y +I segun la fecha.
Valores verificados con el codigo: ceros en lambda_sol~76/256, extremos en ~166/346."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Arc

fig, ax = plt.subplots(figsize=(9.2, 5.6))
ax.set_aspect('equal'); ax.axis('off')

# --- orbita de la Tierra (ecliptica) en perspectiva ---
a, b = 5.0, 1.85
orb = Ellipse((0, 0), 2*a, 2*b, fill=False, ls='--', lw=1.3, ec='#8a8a8a', zorder=1)
ax.add_patch(orb)

# --- Sol en el centro ---
ax.add_patch(plt.Circle((0, 0), 0.95, color='#ffd23a', zorder=4, ec='#e0a800', lw=1.2))
ax.add_patch(plt.Circle((0, 0), 0.95, color='none', zorder=4))

# --- eje de rotacion solar: fijo, inclinado (exagerado a 20 deg, real 7,25) ---
tilt = np.radians(20.0)          # inclinacion DIBUJADA (exagerada)
L = 1.85
nx, ny = L*np.sin(tilt), L*np.cos(tilt)      # extremo Norte (arriba, inclinado a la derecha)
ax.plot([-nx, nx], [-ny, ny], color='#c01515', lw=2.4, zorder=5)
ax.text(nx+0.06, ny+0.12, 'N', color='#c01515', fontsize=13, fontweight='bold', ha='center')
ax.text(-nx-0.06, -ny-0.16, 'S', color='#c01515', fontsize=13, fontweight='bold', ha='center')

# --- vertical de referencia (polo de la ecliptica) y angulo I ---
ax.plot([0, 0], [0, ny+0.15], color='#555', lw=1.0, ls=':', zorder=3)
ax.add_patch(Arc((0, 0), 1.7, 1.7, angle=90, theta1=-20, theta2=0,
                 color='#555', lw=1.0, zorder=3))
ax.text(0.34, 1.32, r'$I=7{,}25^\circ$', color='#333', fontsize=10.5)

# --- 4 posiciones de la Tierra y sus datos ---
# (x, y, etiqueta, color_caja, alineacion del texto)
casos = [
    ( a, 0.0, '$\\approx$ 8 sep\n$\\lambda_\\odot\\approx166^\\circ$\n$B_0=+7{,}25^\\circ$\nvemos el polo N', '#1f6fb2', 'left'),
    (-a, 0.0, '$\\approx$ 8 mar\n$\\lambda_\\odot\\approx346^\\circ$\n$B_0=-7{,}25^\\circ$\nvemos el polo S', '#1f6fb2', 'right'),
    (0.0,  b, '$\\approx$ 6 jun\n$\\lambda_\\odot\\approx76^\\circ$\n$B_0=0$\necuador de canto', '#3a8a3a', 'center'),
    (0.0, -b, '$\\approx$ 7 dic\n$\\lambda_\\odot\\approx256^\\circ$\n$B_0=0$\necuador de canto', '#3a8a3a', 'center'),
]
for (x, y, txt, col, ha) in casos:
    # linea de vision Tierra -> Sol
    arr = FancyArrowPatch((x, y), (np.sign(x)*0.95 if x != 0 else 0.0,
                                   np.sign(y)*0.95 if y != 0 else 0.0),
                          arrowstyle='-|>', mutation_scale=11, lw=1.0,
                          color='#777', ls=(0, (4, 3)), zorder=2)
    ax.add_patch(arr)
    ax.add_patch(plt.Circle((x, y), 0.17, color=col, zorder=6, ec='white', lw=1.0))
    # caja de texto
    if ha == 'left':
        tx, tyy, hh = x+0.45, y, 'left'
    elif ha == 'right':
        tx, tyy, hh = x-0.45, y, 'right'
    elif y > 0:
        tx, tyy, hh = x, y+0.42, 'center'
    else:
        tx, tyy, hh = x, y-0.42, 'center'
    va = 'center' if ha in ('left', 'right') else ('bottom' if y > 0 else 'top')
    ax.text(tx, tyy, txt, fontsize=8.3, ha=hh, va=va, color='#111',
            linespacing=1.35,
            bbox=dict(boxstyle='round,pad=0.32', fc='white', ec=col, lw=1.0, alpha=0.96))

ax.text(0, 3.95, u'Orientación del eje solar a lo largo del año',
        ha='center', fontsize=12.5, fontweight='bold')
ax.text(0, -3.98,
        u'El eje del Sol está inclinado $I=7{,}25^\\circ$ (exagerado en el dibujo) y apunta siempre\n'
        u'en la misma dirección; según dónde está la Tierra, vemos más el polo N, el S o el ecuador.',
        ha='center', fontsize=8.8, color='#333', linespacing=1.4)

ax.set_xlim(-7.3, 7.3); ax.set_ylim(-4.45, 4.35)
plt.tight_layout()
out = r'..\latex\figuras\orientacion_polo_solar_generada.png'
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('GUARDADA:', out)
