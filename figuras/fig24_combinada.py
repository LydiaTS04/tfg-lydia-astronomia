# -*- coding: utf-8 -*-
"""
Figura 24 COMBINADA (TFG):
(A) Top-down de la ecliptica: donde apunta el eje solar (nodo lambda_N = -13 deg desde gamma).
(B) Consecuencia: el Sol visto desde la Tierra en 4 fechas; B0 oscila entre -I y +I.
Texto sin acentos (matplotlib); acentos en el \\caption del TFG.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams['font.family'] = 'DejaVu Sans'
I = 7.25
EXAG = 3.0

fig = plt.figure(figsize=(12.5, 9.2))
gs = gridspec.GridSpec(2, 4, height_ratios=[1.25, 1.0], hspace=0.30, wspace=0.18)

# ===================== (A) TOP-DOWN: orientacion del nodo =====================
axA = fig.add_subplot(gs[0, :]); axA.set_aspect('equal'); axA.axis('off')
axA.set_xlim(-7.6, 7.6); axA.set_ylim(-3.0, 3.4)

# ecliptica (elipse en perspectiva)
ea, eb = 6.2, 2.0
t = np.linspace(0, 2*np.pi, 400)
axA.plot(ea*np.cos(t), eb*np.sin(t), color='#2b6cff', lw=2.2, zorder=2)
axA.text(4.7, -1.55, 'Ecliptica', color='#2b6cff', fontsize=11, style='italic')

# ejes de estaciones
axA.plot([-ea, ea], [0, 0], color='#d62728', lw=1.4, zorder=1)          # solsticios
axA.plot([0, 0], [-eb, eb*1.0], color='#d62728', lw=1.4, zorder=1)      # equinoccios
axA.text(-ea-0.15, 0, 'Solsticio invierno\n$\\pi/2$', ha='right', va='center', color='#d62728', fontsize=10)
axA.text(ea+0.15, 0, 'Solsticio verano\n$3\\pi/2$', ha='left', va='center', color='#d62728', fontsize=10)
axA.text(0, eb+0.35, 'Otono   $0^\\circ\\,\\gamma$', ha='center', va='bottom', color='#d62728', fontsize=11)
axA.text(0, -eb-0.30, 'Primavera   $\\pi$', ha='center', va='top', color='#d62728', fontsize=10)

# Sol
axA.add_patch(plt.Circle((0, 0), 0.55, color='#ffd000', ec='#e8a000', lw=1.4, zorder=4))
for k in range(12):
    a = k*np.pi/6
    axA.plot([0.6*np.cos(a), 0.85*np.cos(a)], [0.6*np.sin(a), 0.85*np.sin(a)],
             color='#ffd000', lw=2, zorder=3)

# direccion del NODO (Norte solar) a -13 deg de gamma (vertical), hacia la derecha
ln = np.radians(13.0)          # 13 grados a la derecha de la vertical
Ln = 2.5
nx, ny = np.sin(ln), np.cos(ln)
axA.annotate('', xy=(Ln*nx, Ln*ny), xytext=(0, 0),
             arrowprops=dict(arrowstyle='-|>', color='#e000e0', lw=2.6), zorder=5)
axA.text(Ln*nx+0.15, Ln*ny+0.05, 'Norte solar\n(nodo del ecuador solar)',
         color='#e000e0', fontsize=10.5, fontweight='bold', va='bottom')
# arco del angulo -13 entre vertical y nodo
arc = np.linspace(np.pi/2, np.pi/2 - ln, 40)
axA.plot(1.15*np.cos(arc), 1.15*np.sin(arc), color='#1b7d1b', lw=1.8, zorder=5)
axA.text(0.42, 1.55, r'$\lambda_N = -13^\circ52^\prime$' + '\n(= 347 deg)',
         color='#1b7d1b', fontsize=10.5, ha='left')

axA.text(0, 3.05, '(A)  Donde apunta el eje solar: el nodo esta a un angulo fijo de gamma',
         ha='center', fontsize=12.5, fontweight='bold', color='#222')

# ===================== (B) DISCOS: lo que se ve =====================
casos = [
    dict(fecha='~8 sep', lam=166, B0=+I, polo='polo NORTE', col='#d62728'),
    dict(fecha='~7 dic', lam=256, B0=0.0, polo='ecuador de canto', col='#555'),
    dict(fecha='~8 mar', lam=346, B0=-I, polo='polo SUR', col='#1f77b4'),
    dict(fecha='~6 jun', lam=76,  B0=0.0, polo='ecuador de canto', col='#555'),
]

def disco(ax, B0deg):
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.35, 1.35)
    B0 = np.radians(B0deg*EXAG)
    ax.add_patch(plt.Circle((0, 0), 1.0, color='#ffd27f', ec='#e07b00', lw=1.6, zorder=2))
    lam = np.radians(np.linspace(-90, 90, 120))
    for phi_d in (-60, -30, 0, 30, 60):
        phi = np.radians(phi_d)
        X = np.cos(phi)*np.sin(lam)
        Y = np.sin(phi)*np.cos(B0) - np.cos(phi)*np.sin(B0)*np.cos(lam)
        ax.plot(X, Y, color=('#1b7d1b' if phi_d == 0 else '#b06a00'),
                lw=(2.6 if phi_d == 0 else 0.9), alpha=(1 if phi_d == 0 else 0.55), zorder=3)
    phi = np.radians(np.linspace(-90, 90, 120))
    for lam0_d in (-60, -30, 0, 30, 60):
        lam0 = np.radians(lam0_d)
        X = np.cos(phi)*np.sin(lam0)
        Y = np.sin(phi)*np.cos(B0) - np.cos(phi)*np.sin(B0)*np.cos(lam0)
        ax.plot(X, Y, color=('#0aa' if lam0_d == 0 else '#b06a00'),
                lw=(2.0 if lam0_d == 0 else 0.9), alpha=(0.95 if lam0_d == 0 else 0.5), zorder=3)
    if B0deg > 0.1:
        ax.plot(0, np.cos(B0), 'o', color='#1a3b8b', ms=8, zorder=5)
        ax.text(0, np.cos(B0)+0.12, 'N', color='#1a3b8b', fontsize=13, fontweight='bold', ha='center')
    elif B0deg < -0.1:
        ax.plot(0, -np.cos(B0), 'o', color='#1a3b8b', ms=8, zorder=5)
        ax.text(0, -np.cos(B0)-0.22, 'S', color='#1a3b8b', fontsize=13, fontweight='bold', ha='center')

for i, c in enumerate(casos):
    ax = fig.add_subplot(gs[1, i])
    disco(ax, c['B0'])
    ax.text(0, -1.62, '%s  (lambda_Sol ~ %d deg)' % (c['fecha'], c['lam']),
            ha='center', fontsize=9.3, color='#333')
    ax.text(0, -1.85, 'B0 = %+.2f deg' % c['B0'], ha='center', fontsize=10.5,
            fontweight='bold', color=c['col'])
    ax.text(0, -2.06, c['polo'], ha='center', fontsize=9.3, color=c['col'])

fig.text(0.5, 0.475, '(B)  Y por eso, segun la fecha, vemos el Sol asi  '
         '(rejilla heliografica; inclinacion B0 exagerada x3)',
         ha='center', fontsize=12, fontweight='bold', color='#222')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion',
                   'fig24_combinada.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
