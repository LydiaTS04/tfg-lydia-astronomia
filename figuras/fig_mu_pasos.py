# -*- coding: utf-8 -*-
"""
mu en 2 pasos (con acentos) + secuencia de 3 paneles con los pasos hechos.
Arriba: diagrama grande. Abajo: 1) foto sin orientar  2) paso 1 (mu->pi)  3) paso 2 (pi->eje Sol).
Angulos exagerados para que se vean (I de verdad 7,25).
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Arc

plt.rcParams['font.family'] = 'DejaVu Sans'
MU, BOPT, IDEG = 22.0, 13.0, 17.0   # exagerados (mu+beta_opt -> pi; I -> de pi al eje solar)
GRIS='#888'; MAG='#d000d0'; AZ='#15357e'; SOL='#ffcc33'; SOLE='#e8a000'

def sun(ax, r=0.55):
    ax.add_patch(plt.Circle((0, 0), r, color=SOL, ec=SOLE, lw=1.3, zorder=5))
    for k in range(12):
        a = k*np.pi/6
        ax.plot([1.12*r*np.cos(a), 1.45*r*np.cos(a)], [1.12*r*np.sin(a), 1.45*r*np.sin(a)], color=SOL, lw=1.4, zorder=4)

def arrow(ax, ang, color, L, lw=2.4, ls='-', alpha=1.0):
    a = np.radians(ang)
    ax.annotate('', xy=(L*np.cos(a), L*np.sin(a)), xytext=(0, 0),
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw, ls=ls, alpha=alpha), zorder=6)

from matplotlib.patches import FancyArrowPatch
def rot_arrow(ax, a1, a2, color, rad=1.0, bow=0.45, lw=2.2, scale=14):
    p1 = (rad*np.cos(np.radians(a1)), rad*np.sin(np.radians(a1)))
    p2 = (rad*np.cos(np.radians(a2)), rad*np.sin(np.radians(a2)))
    ax.add_patch(FancyArrowPatch(p1, p2, connectionstyle='arc3,rad=%g' % bow,
                 arrowstyle='-|>', mutation_scale=scale, color=color, lw=lw, zorder=8))

fig = plt.figure(figsize=(13.2, 11.0))
gs = gridspec.GridSpec(2, 4, height_ratios=[1.9, 1.0], hspace=0.16, wspace=0.12)

# ===================== ARRIBA: diagrama grande =====================
ax = fig.add_subplot(gs[0, :]); ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-3.5, 3.5); ax.set_ylim(-3.2, 3.7)
L = 2.05
ax.add_patch(plt.Rectangle((-3.05, -2.7), 6.1, 5.75, fill=False, edgecolor=GRIS, lw=1.5))
ax.text(-2.95, 2.88, r'foto plana: $(\rho,\ \theta_m)$', color=GRIS, fontsize=10, style='italic')
sun(ax)
a_v = 90.0
a_pi = 90.0 + MU + BOPT          # mu + beta_opt llevan la foto hasta pi
a_s  = a_pi + IDEG               # el triangulo lleva de pi al eje del Sol
arrow(ax, a_v, GRIS, L, lw=2.0, ls=(0, (5, 4)))
ax.text(0.12, L+0.1, 'vertical de la foto\n(arriba de la imagen)', color='#777', fontsize=10, ha='left', va='bottom')
# pi (magenta) -- etiqueta arriba a la izquierda de su punta
arrow(ax, a_pi, MAG, L)
ax.text(L*np.cos(np.radians(a_pi))+0.35, L*np.sin(np.radians(a_pi))+0.16,
        r'$\pi$ (polo eclíptica)', color=MAG, fontsize=10.5, fontweight='bold', ha='right', va='bottom')
# eje del Sol (azul) -- etiqueta debajo-izquierda de su punta (no choca con pi)
arrow(ax, a_s, AZ, L)
ax.text(L*np.cos(np.radians(a_s))-0.12, L*np.sin(np.radians(a_s))-0.08,
        'norte solar\n(eje del Sol)', color=AZ, fontsize=10, fontweight='bold', ha='right', va='top', linespacing=1.15)
# formula alfa, centrada bajo el Sol
ax.text(0, -1.5, r'$\alpha=\theta_m+\mu+\beta_{opt}$', color='#444', fontsize=11, ha='center')
# ETAPA 1: mu + beta_opt (a la vez) -> pi
ax.add_patch(Arc((0, 0), 1.9, 1.9, angle=0, theta1=a_v, theta2=a_pi, color=MAG, lw=2.6))
am = np.radians(103); ax.text(1.30*np.cos(am), 1.30*np.sin(am), r'$\mu+\beta_{opt}$', color=MAG, fontsize=13.5, fontweight='bold', ha='center', va='center')
# ETAPA 2: triangulo (norte solar), de pi al eje del Sol
ax.add_patch(Arc((0, 0), 2.7, 2.7, angle=0, theta1=a_pi, theta2=a_s, color=AZ, lw=2.3))
ai = np.radians((a_pi+a_s)/2); ax.text(2.10*np.cos(ai), 2.10*np.sin(ai), r'$I\approx7{,}25^\circ$', color=AZ, fontsize=10.5, fontweight='bold', ha='center', va='center')
ax.text(2.55, 1.5, r'ETAPA 1: $\mu+\beta_{opt}$' '\n(a la vez)\n'
        r'orientan la foto a $\pi$' '\n'
        r'$\mu$: geometría (dónde está $\pi$)' '\n'
        r'$\beta_{opt}$: giro óptico del tubo',
        color=MAG, fontsize=8.3, fontweight='bold',
        ha='center', va='center', linespacing=1.35, bbox=dict(boxstyle='round', fc='#fff0ff', ec=MAG, lw=1.2))
ax.text(2.55, -0.8, r'ETAPA 2 — giro del polo:' '\n'
        r'de $\pi$ al norte solar' '\n' r'($7{,}25^\circ$ más)' '\n' r'$\to\ (\Phi,\ L)$',
        color=AZ, fontsize=9.2, fontweight='bold', ha='center', va='center', linespacing=1.3,
        bbox=dict(boxstyle='round', fc='#eef2fb', ec=AZ, lw=1.2))
ax.text(0, 3.45, r'Las correcciones para orientar la foto: $\mu+\beta_{opt}$ (a $\pi$) y el norte solar',
        ha='center', fontsize=13, fontweight='bold', color='#222')
ax.text(0, -3.05, r'$\mu$ y $\beta_{opt}$ sitúan la mancha tomando $\pi$ como polo;  después se gira ese sistema $7{,}25^\circ$, de $\pi$ al norte solar, y se obtiene $(\Phi,\ L)$',
        ha='center', fontsize=8.8, color='#555', style='italic')

# ===================== ABAJO: 3 pasos, mostrando el GIRO =====================
def panel(axp, titulo, stage):
    axp.set_aspect('equal'); axp.axis('off'); axp.set_xlim(-2.0, 2.0); axp.set_ylim(-2.0, 2.3)
    axp.add_patch(plt.Rectangle((-1.85, -1.7), 3.7, 3.5, fill=False, edgecolor=GRIS, lw=1.0))
    sun(axp, r=0.42); Lm = 1.45
    PIA = MU + BOPT                                                  # giro total hasta pi
    if stage == 0:
        arrow(axp, 90, GRIS, Lm, lw=1.8, ls=(0, (4, 3)))
        axp.text(0.95*np.cos(np.radians(90+PIA)), 0.95*np.sin(np.radians(90+PIA))+0.05,
                 r'$\pi$?', color=MAG, fontsize=11, ha='center', va='center', alpha=0.6)
    elif stage == 1:
        arrow(axp, 90, GRIS, Lm, lw=1.5, ls=(0, (4, 3)), alpha=0.4)   # vertical, ya tenue
        rot_arrow(axp, 90, 90+PIA, MAG)                               # GIRO mu+beta_opt
        arrow(axp, 90+PIA, MAG, Lm, lw=2.2)                           # llega a pi
        am = np.radians(90+PIA/2); axp.text(0.60*np.cos(am), 0.60*np.sin(am), r'$\mu+\beta_{opt}$', color=MAG, fontsize=9.5, fontweight='bold', ha='center', va='center')
    else:
        IP = 30                                                       # I exagerado en el panel para que el giro se vea
        arrow(axp, 90+PIA, MAG, Lm, lw=1.6, alpha=0.45)              # pi, de donde partimos (tenue)
        rot_arrow(axp, 90+PIA, 90+PIA+IP, AZ, rad=1.25, bow=0.5, lw=3.0, scale=20)  # GIRO I, bien marcado
        arrow(axp, 90+PIA+IP, AZ, Lm, lw=2.4)                        # llega al eje del Sol
        ai = np.radians(90+PIA+IP/2); axp.text(1.45*np.cos(ai), 1.45*np.sin(ai), r'$I$', color=AZ, fontsize=13, fontweight='bold', ha='center', va='center')
    axp.text(0, -1.95, titulo, ha='center', va='center', fontsize=9.3, color='#222', fontweight='bold', linespacing=1.2)

p1 = fig.add_subplot(gs[1, 0]); panel(p1, r'1) Foto plana:' '\n' r'$(\rho,\ \theta_m)$', 0)
p2 = fig.add_subplot(gs[1, 1]); panel(p2, r'2) Giro $\mu+\beta_{opt}$:' '\n' r'apunta a $\pi$', 1)
p3 = fig.add_subplot(gs[1, 2]); panel(p3, r'3) Giro del polo:' '\n' r'de $\pi$ al norte solar', 2)

# 4) RESULTADO: el eje del Sol queda vertical (referencia)
def resultado(axp):
    axp.set_aspect('equal'); axp.axis('off'); axp.set_xlim(-2.0, 2.0); axp.set_ylim(-2.0, 2.3)
    axp.add_patch(plt.Rectangle((-1.85, -1.7), 3.7, 3.5, fill=False, edgecolor=GRIS, lw=1.0))
    r = 0.95
    axp.add_patch(plt.Circle((0, 0), r, color='#ffe1a8', ec=SOLE, lw=1.5, zorder=4))
    lam = np.radians(np.linspace(-90, 90, 80))
    for pd in (-45, 0, 45):                       # paralelos (horizontales)
        ph = np.radians(pd)
        axp.plot(r*np.cos(ph)*np.sin(lam), r*np.sin(ph)*np.ones_like(lam),
                 color=('#1b7d1b' if pd == 0 else '#cf9b46'), lw=(2.2 if pd == 0 else 0.9),
                 alpha=(1 if pd == 0 else 0.7), zorder=5)
    ph = np.radians(np.linspace(-90, 90, 80))
    for l0 in (-45, 0, 45):                        # meridianos
        lr = np.radians(l0)
        axp.plot(r*np.cos(ph)*np.sin(lr), r*np.sin(ph),
                 color=('#0094c8' if l0 == 0 else '#cf9b46'), lw=(1.8 if l0 == 0 else 0.9),
                 alpha=(1 if l0 == 0 else 0.7), zorder=5)
    # eje del Sol = VERTICAL (ya es la referencia)
    axp.plot([0, 0], [-1.35*r, 1.35*r], color=AZ, lw=2.4, zorder=6)
    axp.text(0, 1.35*r+0.05, 'N', color=AZ, fontsize=11, fontweight='bold', ha='center', va='bottom')
    axp.text(0, -1.35*r-0.05, 'S', color=AZ, fontsize=10, fontweight='bold', ha='center', va='top')
    # una mancha de ejemplo
    axp.plot(0.45*r, 0.4*r, 'o', color='#5a3210', ms=6, zorder=7)
    axp.text(0, -1.95, r'4) Ya orientada: eje del' '\n' r'Sol vertical $\to\ (\Phi,\ L)$',
             ha='center', va='center', fontsize=9.3, color='#222', fontweight='bold', linespacing=1.2)
p4 = fig.add_subplot(gs[1, 3]); resultado(p4)

fig.text(0.5, 0.355, 'La cadena, paso a paso (3 correcciones en 2 etapas):', ha='center', fontsize=12, fontweight='bold', color='#222')

out = os.path.join(r'C:\Users\lydia\Downloads\tfg', 'documentos explicacion', 'fig_mu_pasos.png')
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print('Guardado:', out)
