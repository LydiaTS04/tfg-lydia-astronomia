# -*- coding: utf-8 -*-
"""
Figura del Sol y B0 - completa y clara.
Arriba-izq: VISTA LATERAL (que es B0: angulo entre la visual Tierra-Sol y el ecuador solar).
Arriba-der: el DISCO como se ve, con la rejilla inclinada y B0 marcado.
Abajo: las 4 fechas (B0 = +I, 0, -I, 0).
Texto sin acentos (matplotlib); acentos en el \\caption del TFG.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Wedge, Arc, FancyArrowPatch

plt.rcParams['font.family'] = 'DejaVu Sans'
I = 7.25
EXAG = 3.0
B0v = np.radians(22.0)   # B0 exagerado para la explicacion grande

fig = plt.figure(figsize=(12.5, 9.4))
gs = gridspec.GridSpec(2, 4, height_ratios=[1.35, 1.0], hspace=0.33, wspace=0.2)

# ===================== (A) VISTA LATERAL: que es B0 =====================
axA = fig.add_subplot(gs[0, :2]); axA.set_aspect('equal'); axA.axis('off')
axA.set_xlim(-5.2, 2.2); axA.set_ylim(-2.5, 3.1)
R = 1.4
# Sol
axA.add_patch(plt.Circle((0, 0), R, color='#ffd27f', ec='#e07b00', lw=1.6, zorder=3))
# eje de rotacion (norte inclinado hacia la Tierra, a la izquierda)
n = np.array([-np.sin(B0v), np.cos(B0v)])
axA.plot([-1.5*R*n[0], 1.5*R*n[0]], [-1.5*R*n[1], 1.5*R*n[1]], color='#1a3b8b', lw=2.6, zorder=5)
axA.text(1.5*R*n[0]-0.18, 1.5*R*n[1]+0.02, 'N', color='#1a3b8b', fontsize=14, fontweight='bold', ha='center', va='bottom')
axA.text(-1.5*R*n[0], -1.5*R*n[1]-0.05, 'S', color='#1a3b8b', fontsize=13, fontweight='bold', ha='center', va='top')
# plano del ecuador solar (perpendicular al eje), visto de canto = linea
e = np.array([np.cos(B0v), np.sin(B0v)])
axA.plot([-1.55*R*e[0], 1.55*R*e[1]*0+1.55*R*e[0]], [-1.55*R*e[1], 1.55*R*e[1]],
         color='#1b7d1b', lw=2.6, zorder=5)
axA.text(1.55*R*e[0]+0.08, 1.55*R*e[1], 'ecuador solar', color='#1b7d1b', fontsize=10, va='center')
# hemisferio norte (el que se ve mas) sombreado
axA.add_patch(Wedge((0, 0), R, np.degrees(B0v), 180+np.degrees(B0v),
                    color='#9ecae1', alpha=0.5, zorder=4))
# Tierra + visual
axA.add_patch(plt.Circle((-4.3, 0), 0.16, color='#2b6cff', zorder=5))
axA.text(-4.3, -0.4, 'Tierra', color='#2b6cff', fontsize=10, ha='center')
axA.annotate('', xy=(-R, 0), xytext=(-4.1, 0),
             arrowprops=dict(arrowstyle='-|>', color='#2b6cff', lw=1.8), zorder=4)
axA.text(-2.6, 0.18, 'visual', color='#2b6cff', fontsize=9.5, ha='center')
# linea de vision prolongada (horizontal) para marcar el angulo B0 con el ecuador
axA.plot([-1.55*R, 1.55*R], [0, 0], color='#2b6cff', lw=1.0, ls=':', zorder=4)
# arco B0 entre la horizontal (visual) y el ecuador
axA.add_patch(Arc((0, 0), 2.0*R, 2.0*R, angle=0, theta1=0, theta2=np.degrees(B0v),
                  color='#d62728', lw=2.2, zorder=6))
axA.text(R*1.18, R*0.28, r'$B_0$', color='#d62728', fontsize=15, fontweight='bold')
axA.text(0, -2.05, 'B0 = angulo entre la visual y el ecuador solar\n(= latitud del centro del disco)',
         ha='center', fontsize=10, color='#222')
axA.text(-1.5, 2.85, '(A)  VISTA LATERAL: que es B0', fontsize=12.5, fontweight='bold', color='#222', ha='center')

# ===================== (B) DISCO ANOTADO =====================
axB = fig.add_subplot(gs[0, 2:]); axB.set_aspect('equal'); axB.axis('off')
axB.set_xlim(-1.65, 1.95); axB.set_ylim(-1.6, 1.7)

def grid_disco(ax, B0r, big=True):
    ax.add_patch(plt.Circle((0, 0), 1.0, color='#ffd27f', ec='#e07b00', lw=1.7, zorder=2))
    lam = np.radians(np.linspace(-90, 90, 140))
    for phi_d in (-60, -30, 0, 30, 60):
        phi = np.radians(phi_d)
        X = np.cos(phi)*np.sin(lam)
        Y = np.sin(phi)*np.cos(B0r) - np.cos(phi)*np.sin(B0r)*np.cos(lam)
        ax.plot(X, Y, color=('#1b7d1b' if phi_d == 0 else '#b06a00'),
                lw=(2.8 if phi_d == 0 else 0.9), alpha=(1 if phi_d == 0 else 0.5), zorder=3)
    phi = np.radians(np.linspace(-90, 90, 140))
    for lam0_d in (-60, -30, 0, 30, 60):
        lam0 = np.radians(lam0_d)
        X = np.cos(phi)*np.sin(lam0)
        Y = np.sin(phi)*np.cos(B0r) - np.cos(phi)*np.sin(B0r)*np.cos(lam0)
        ax.plot(X, Y, color=('#0aa' if lam0_d == 0 else '#b06a00'),
                lw=(2.0 if lam0_d == 0 else 0.9), alpha=(0.95 if lam0_d == 0 else 0.45), zorder=3)
    # polo visible
    if B0r > 0.01:
        ax.plot(0, np.cos(B0r), 'o', color='#1a3b8b', ms=9, zorder=5)
    elif B0r < -0.01:
        ax.plot(0, -np.cos(B0r), 'o', color='#1a3b8b', ms=9, zorder=5)

grid_disco(axB, B0v)
# centro del disco
axB.plot(0, 0, '+', color='k', ms=12, mew=2, zorder=6)
axB.annotate('centro del disco', xy=(0, 0), xytext=(-1.55, -1.25),
             fontsize=9.5, color='k', arrowprops=dict(arrowstyle='->', color='k', lw=1))
# ecuador (desplazado del centro por B0)
yeq = -np.sin(B0v)
axB.annotate('ecuador', xy=(0.0, yeq), xytext=(1.15, -0.75),
             fontsize=10, color='#1b7d1b', fontweight='bold',
             arrowprops=dict(arrowstyle='->', color='#1b7d1b', lw=1.2))
# polo N visible
axB.annotate('polo N (visible)', xy=(0, np.cos(B0v)), xytext=(0.65, 1.35),
             fontsize=10, color='#1a3b8b', fontweight='bold',
             arrowprops=dict(arrowstyle='->', color='#1a3b8b', lw=1.2))
# B0 = distancia centro-ecuador a lo largo del meridiano central
axB.annotate('', xy=(0, yeq), xytext=(0, 0),
             arrowprops=dict(arrowstyle='<->', color='#d62728', lw=2), zorder=6)
axB.text(0.1, yeq/2, r'$B_0$', color='#d62728', fontsize=14, fontweight='bold', va='center')
axB.text(0, -1.5, '(B)  EL DISCO VISTO: el centro queda a latitud B0;\nse ve mas el hemisferio norte',
         ha='center', fontsize=10, color='#222')

# ===================== (C) LAS 4 FECHAS =====================
casos = [
    dict(fecha='~8 sep', lam=166, B0=+I, polo='polo NORTE', col='#d62728'),
    dict(fecha='~7 dic', lam=256, B0=0.0, polo='de canto', col='#555'),
    dict(fecha='~8 mar', lam=346, B0=-I, polo='polo SUR', col='#1f77b4'),
    dict(fecha='~6 jun', lam=76,  B0=0.0, polo='de canto', col='#555'),
]
for i, c in enumerate(casos):
    ax = fig.add_subplot(gs[1, i]); ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.5, 1.25)
    grid_disco(ax, np.radians(c['B0']*EXAG))
    if c['B0'] > 0.1: ax.text(0, np.cos(np.radians(c['B0']*EXAG))+0.1, 'N', color='#1a3b8b', fontsize=12, fontweight='bold', ha='center')
    if c['B0'] < -0.1: ax.text(0, -np.cos(np.radians(c['B0']*EXAG))-0.2, 'S', color='#1a3b8b', fontsize=12, fontweight='bold', ha='center')
    ax.text(0, -1.18, '%s' % c['fecha'], ha='center', fontsize=9.5, color='#333', fontweight='bold')
    ax.text(0, -1.36, 'B0=%+.1f deg, %s' % (c['B0'], c['polo']), ha='center', fontsize=8.6, color=c['col'])

fig.text(0.5, 0.475, '(C)  A lo largo del anio  (B0 oscila entre -I y +I; I=7,25 deg; inclinacion exagerada x3)',
         ha='center', fontsize=11.5, fontweight='bold', color='#222')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion', 'fig_sol_B0.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
