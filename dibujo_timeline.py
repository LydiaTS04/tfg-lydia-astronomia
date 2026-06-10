# -*- coding: utf-8 -*-
"""Figura 1: linea de tiempo de la historia de la rotacion solar."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

hitos = [
    (1610, '1610', 'Galileo y Scheiner\nobservan las manchas', +1),
    (1864, '1863–1865', 'Carrington la mide y Faye\nla formula: $\\omega=A+B\\sin^2\\!\\Phi$', -1),
    (1908, '1908', 'Hale: las manchas\nson magnéticas', +1),
    (2010, '2010', 'SOHO y SDO:\nvigilancia espacial', -1),
    (2026, '2026', 'Seguimiento amateur\n+ software propio\n(este trabajo)', +1),
]

fig, ax = plt.subplots(figsize=(13, 4.6))
x0, x1 = 1600, 2040
# eje temporal
ax.add_patch(FancyArrowPatch((x0, 0), (x1, 0), arrowstyle='-|>',
             mutation_scale=22, color='#37474f', lw=3, zorder=2))

col = '#1565c0'
for yr, ylabel, txt, side in hitos:
    # tallo
    ax.plot([yr, yr], [0, 0.55*side], color=col, lw=1.6, zorder=2)
    ax.plot([yr], [0], 'o', color=col, ms=11, zorder=4,
            markeredgecolor='white', markeredgewidth=1.5)
    # año
    ax.text(yr, 0.16*side, ylabel, ha='center',
            va='bottom' if side > 0 else 'top',
            fontsize=12, fontweight='bold', color='#0d47a1')
    # texto del hito
    ax.text(yr, 0.62*side, txt, ha='center',
            va='bottom' if side > 0 else 'top',
            fontsize=10.5, color='#222',
            bbox=dict(boxstyle='round,pad=0.35', fc='#e3f2fd',
                      ec=col, lw=1.1))

ax.set_xlim(x0-5, x1+5)
ax.set_ylim(-1.5, 1.5)
ax.axis('off')
ax.set_title('De Galileo a hoy: hitos en el estudio de la rotación solar',
             fontsize=14, fontweight='bold', pad=10)

plt.tight_layout()
OUT = r'C:\Users\lydia\Downloads\tfg\documentos explicacion\timeline_historia.png'
plt.savefig(OUT, dpi=150, bbox_inches='tight', facecolor='white')
print('Figura 1 guardada:', OUT)
