# -*- coding: utf-8 -*-
"""
Figura 24 v2 (TFG) - mas clara.
Arriba: orbita de la Tierra + eje solar fijo (por que cambia B0).
Abajo: el Sol como se ve desde la Tierra en 4 fechas, con la REJILLA heliografica
inclinada segun B0 (exagerada x3 para que se aprecie).
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams['font.family'] = 'DejaVu Sans'
I = 7.25
EXAG = 3.0   # exageracion visual de B0 en los discos

fig = plt.figure(figsize=(12, 8.2))
gs = gridspec.GridSpec(2, 4, height_ratios=[1.15, 1.0], hspace=0.32, wspace=0.18)

# ============== PANEL SUPERIOR: orbita + eje fijo ==============
axo = fig.add_subplot(gs[0, :]); axo.set_aspect('equal'); axo.axis('off')
axo.set_xlim(-7.6, 7.6); axo.set_ylim(-2.7, 2.9)
A, Bb = 5.4, 1.9
t = np.linspace(0, 2*np.pi, 300)
axo.plot(A*np.cos(t), Bb*np.sin(t), '--', color='#999', lw=1.1)
# Sol + eje fijo
g = np.radians(I)
axo.add_patch(plt.Circle((0, 0), 0.75, color='#ffae42', ec='#e07b00', lw=1.4, zorder=3))
ux, uy = np.sin(g), np.cos(g)
axo.plot([-1.45*ux, 1.45*ux], [-1.45*uy, 1.45*uy], color='#1a3b8b', lw=2.6, zorder=4)
axo.text(1.45*ux, 1.45*uy+0.05, 'N', color='#1a3b8b', fontsize=12, fontweight='bold', ha='center', va='bottom')
axo.text(0, -2.35, 'El eje del Sol esta FIJO (I = 7,25 deg) y apunta siempre igual',
         ha='center', fontsize=10.5, color='#1a3b8b')
# 4 posiciones de la Tierra
pos = [(0,   '~8 sep'), (90,  '~7 dic'), (180, '~8 mar'), (270, '~6 jun')]
for ang, fe in pos:
    a = np.radians(ang); x, y = A*np.cos(a), Bb*np.sin(a)
    axo.plot(x, y, 'o', color='#2b6cff', ms=12, mec='white', mew=1.2, zorder=5)
    dx = 0.0 if ang in (90, 270) else (0.7 if ang == 0 else -0.7)
    axo.text(x*1.16, y*1.32+ (0.45 if ang==90 else (-0.55 if ang==270 else 0)),
             fe, ha='center', va='center', fontsize=10, color='#2b6cff', fontweight='bold')
axo.text(0, 2.55, 'Por que cambia B0', ha='center', fontsize=13, fontweight='bold', color='#222')

# ============== PANELES INFERIORES: disco visto desde la Tierra ==============
casos = [
    dict(fecha='~8 sep', lam=166, B0=+I, polo='polo NORTE', col='#d62728'),
    dict(fecha='~7 dic', lam=256, B0=0.0, polo='ecuador de canto', col='#555'),
    dict(fecha='~8 mar', lam=346, B0=-I, polo='polo SUR', col='#1f77b4'),
    dict(fecha='~6 jun', lam=76,  B0=0.0, polo='ecuador de canto', col='#555'),
]

def dibuja_disco(ax, B0deg):
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.3, 1.35)
    B0 = np.radians(B0deg * EXAG)
    # disco
    ax.add_patch(plt.Circle((0, 0), 1.0, color='#ffd27f', ec='#e07b00', lw=1.6, zorder=2))
    lam = np.radians(np.linspace(-90, 90, 120))
    # paralelos
    for phi_d in (-60, -30, 0, 30, 60):
        phi = np.radians(phi_d)
        X = np.cos(phi)*np.sin(lam)
        Y = np.sin(phi)*np.cos(B0) - np.cos(phi)*np.sin(B0)*np.cos(lam)
        if phi_d == 0:
            ax.plot(X, Y, color='#1b7d1b', lw=2.6, zorder=4)   # ecuador
        else:
            ax.plot(X, Y, color='#b06a00', lw=0.9, alpha=0.55, zorder=3)
    # meridianos
    phi = np.radians(np.linspace(-90, 90, 120))
    for lam0_d in (-60, -30, 0, 30, 60):
        lam0 = np.radians(lam0_d)
        X = np.cos(phi)*np.sin(lam0)
        Y = np.sin(phi)*np.cos(B0) - np.cos(phi)*np.sin(B0)*np.cos(lam0)
        col = '#0aa' if lam0_d == 0 else '#b06a00'
        ax.plot(X, Y, color=col, lw=(2.0 if lam0_d == 0 else 0.9),
                alpha=(0.95 if lam0_d == 0 else 0.5), zorder=3)
    # polo visible
    if B0deg > 0.1:
        ax.plot(0, np.cos(B0), 'o', color='#1a3b8b', ms=8, zorder=5)
        ax.text(0, np.cos(B0)+0.13, 'N', color='#1a3b8b', fontsize=13, fontweight='bold', ha='center')
    elif B0deg < -0.1:
        ax.plot(0, -np.cos(B0), 'o', color='#1a3b8b', ms=8, zorder=5)
        ax.text(0, -np.cos(B0)-0.22, 'S', color='#1a3b8b', fontsize=13, fontweight='bold', ha='center')

for i, c in enumerate(casos):
    ax = fig.add_subplot(gs[1, i])
    dibuja_disco(ax, c['B0'])
    ax.text(0, -1.62, '%s   (lambda_Sol ~ %d deg)' % (c['fecha'], c['lam']),
            ha='center', fontsize=9.5, color='#333', transform=ax.transData)
    ax.text(0, -1.85, 'B0 = %+.2f deg' % c['B0'], ha='center', fontsize=10.5,
            fontweight='bold', color=c['col'])
    ax.text(0, -2.07, c['polo'], ha='center', fontsize=9.5, color=c['col'])

fig.text(0.5, 0.50, 'Lo que se ve desde la Tierra  (rejilla heliografica; '
         'inclinacion B0 exagerada x3 para que se aprecie)',
         ha='center', fontsize=11, fontweight='bold', color='#222')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion',
                   'fig24_B0_v2.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
