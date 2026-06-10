# -*- coding: utf-8 -*-
"""
Pone EJES (ecuador + paralelos curvos + eje N-S) en TODAS las fotos limpias
de fotos_con_ejes_TODAS, usando los datos propios de cada observacion (BD):
mu, beta, lambda_sol, y las manchas con su latitud.

- Detecta el disco en cada imagen limpia (centro, radio).
- Usa la inversa exacta del codigo (round-trip verificado).
- Eje N-S con el polo norte CORREGIDO (con l_sol).
"""
import os, sqlite3, glob, re, random
import numpy as np
import cv2
from math import sin, cos, asin, atan2, sqrt, radians, degrees, pi, hypot
from PIL import Image, ImageDraw, ImageFont
random.seed(7)

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(CARPETA, 'gestor_web', 'manchas_tfg.db')
DIR_IN  = os.path.join(CARPETA, 'fotos_con_ejes_TODAS')
DIR_OUT = os.path.join(DIR_IN, 'CON_EJES_CURVOS')
os.makedirs(DIR_OUT, exist_ok=True)
PHI_ZERO     = radians(82.0 + 44.0/60.0 + 53.56/3600.0)
LAMBDA_NORTH = radians(-13.0 - 52.0/60.0 - 21.41/3600.0)

# ---------- inversa (Phi,L)->pixel ----------
def pole_proj(l_sol):
    C=(l_sol+pi)-LAMBDA_NORTH
    return (cos(PHI_ZERO)*cos(C), -cos(PHI_ZERO)*sin(C), sin(PHI_ZERO))
def base_perp(p):
    ref=(0.,0.,1.)
    if abs(p[2])>0.99: ref=(1.,0.,0.)
    ux=p[1]*ref[2]-p[2]*ref[1]; uy=p[2]*ref[0]-p[0]*ref[2]; uz=p[0]*ref[1]-p[1]*ref[0]
    n=sqrt(ux*ux+uy*uy+uz*uz); u=(ux/n,uy/n,uz/n)
    wx=p[1]*u[2]-p[2]*u[1]; wy=p[2]*u[0]-p[0]*u[2]; wz=p[0]*u[1]-p[1]*u[0]
    return u,(wx,wy,wz)
def punto_px(v,mu,R,xc,yc,beta):
    if v[0]<=0.001: return None
    rho=sqrt(v[1]*v[1]+v[2]*v[2]); A=atan2(v[2],v[1]); th=A-mu-beta; r=rho*R
    return (xc+r*cos(th), yc-r*sin(th))
def paralelo(Phi_deg,l_sol,mu,R,xc,yc,beta,n=500):
    Phi=radians(Phi_deg); p=pole_proj(l_sol); u,w=base_perp(p)
    sP,cP=sin(Phi),cos(Phi); tr=[]; act=[]
    for i in range(n+1):
        t=2*pi*i/n; ct,st=cos(t),sin(t)
        v=(sP*p[0]+cP*(ct*u[0]+st*w[0]),sP*p[1]+cP*(ct*u[1]+st*w[1]),sP*p[2]+cP*(ct*u[2]+st*w[2]))
        px=punto_px(v,mu,R,xc,yc,beta)
        if px is None:
            if len(act)>1: tr.append(act)
            act=[]
        else: act.append(px)
    if len(act)>1: tr.append(act)
    return tr
def norte_px(mu,R,xc,yc,beta,l_sol):
    lam=LAMBDA_NORTH-(l_sol+pi)
    yv=sin(PHI_ZERO); xv=cos(PHI_ZERO)*sin(lam)
    A=atan2(yv,xv); rho=hypot(xv,yv); th=A-mu-beta
    return (xc+rho*cos(th)*R, yc-rho*sin(th)*R)

# ---------- detectar disco (cv2 + RANSAC, robusto a recortes/dedo/halo) ----------
def _circ3(p1,p2,p3):
    ax,ay=p1; bx,by=p2; cx,cy=p3
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-6: return None
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return ux,uy,sqrt((ax-ux)**2+(ay-uy)**2)
def detectar_disco(path):
    im=cv2.imread(path); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY); H,W=g.shape
    # Borde mas nitido (limbo real): Canny ignora el halo (gradiente suave)
    # y el brillo absoluto (sobreexposicion). RANSAC descarta dedo/manchas/bordes.
    gb=cv2.GaussianBlur(g,(7,7),0)
    edges=cv2.Canny(gb,25,70)
    ys,xs=np.where(edges>0)
    keep=(xs>4)&(xs<W-4)&(ys>4)&(ys<H-4)
    pts=np.c_[xs[keep],ys[keep]].astype(float)
    if len(pts)<50: return None
    best=None;bestn=0;bestin=None
    for _ in range(6000):
        s=random.sample(range(len(pts)),3)
        c3=_circ3(pts[s[0]],pts[s[1]],pts[s[2]])
        if not c3: continue
        xc,yc,R=c3
        if R<W*0.18 or R>W*1.8: continue
        dd=np.abs(np.sqrt((pts[:,0]-xc)**2+(pts[:,1]-yc)**2)-R)
        ninl=int((dd<4).sum())
        if ninl>bestn: bestn=ninl;best=c3;bestin=dd<4
    if best is None: return None
    x,y=pts[bestin,0],pts[bestin,1]
    A=np.c_[2*x,2*y,np.ones(len(x))]; b=x*x+y*y
    sol,*_=np.linalg.lstsq(A,b,rcond=None)
    xc,yc=sol[0],sol[1]; R=sqrt(sol[2]+xc*xc+yc*yc)
    res=float(np.mean(np.abs(np.sqrt((x-xc)**2+(y-yc)**2)-R)))
    return xc,yc,R,res

# ---------- BD ----------
con=sqlite3.connect(RUTA_BD); cur=con.cursor()
def obs_por_nombre(nombre):
    cur.execute("SELECT id_observacion,centro_x,centro_y,radio_sol,lambda_sol,mu_angulo,beta_optica "
                "FROM Observaciones WHERE archivo_img=?",(nombre,))
    return cur.fetchone()

def limpiar_nombre(fn):
    b=os.path.splitext(os.path.basename(fn))[0]
    b=re.sub(r'^limpia\s+','',b)
    b=re.sub(r'\s*-\s*copia$','',b)
    return b.strip()

# ---------- proceso ----------
try: fnt=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',18)
except: fnt=ImageFont.load_default()

import sys
EXTRA = os.path.join(CARPETA, 'fotos abril 2026', 'fotos sin ejes con numeros')
archivos = glob.glob(os.path.join(DIR_IN,'limpia *.png')) + glob.glob(os.path.join(EXTRA,'limpia *.png'))
# si se pasan filtros por linea de comandos, solo procesar esos (no tocar el resto)
filtros=[a.lower() for a in sys.argv[1:]]
if filtros:
    archivos=[f for f in archivos if any(k in os.path.basename(f).lower() for k in filtros)]
# quitar duplicados por nombre (prioridad: el primero encontrado)
vistos=set(); unicos=[]
for f in archivos:
    n=limpiar_nombre(f)
    if n in vistos: continue
    vistos.add(n); unicos.append(f)
archivos=unicos
print('Procesando %d fotos%s\n'%(len(archivos),(' (filtro: %s)'%filtros if filtros else '')))
for fn in sorted(archivos):
    nombre=limpiar_nombre(fn)
    row=obs_por_nombre(nombre)
    if not row:
        print('  [SIN BD] %s  (nombre=%s)'%(os.path.basename(fn),nombre)); continue
    idobs,xcB,ycB,RB,lsd,mud,betad=row
    l_sol=radians(float(lsd)); mu=radians(mud); beta=radians(betad)
    im=Image.open(fn).convert('RGB')
    # Override manual de centro/radio para fotos donde el disco es eliptico/descentrado
    # y el ajuste al limbo nitido se queda corto (jueves 16: hugea mejor con contorno completo)
    MANUAL={'jueves_16-4-26_12_27':(345.0,365.0,347.0)}
    if nombre in MANUAL:
        xc,yc,R=MANUAL[nombre]; res=0.0
    else:
        det=detectar_disco(fn)
        if not det:
            print('  [NO DISCO] %s'%os.path.basename(fn)); continue
        xc,yc,R,res=det
    d=ImageDraw.Draw(im)
    # paralelos + ecuador
    for Phi in range(-75,76,15):
        col=(0,210,0) if Phi==0 else (0,170,230); anc=5 if Phi==0 else 2
        tr=paralelo(Phi,l_sol,mu,R,xc,yc,beta)
        for tramo in tr: d.line(tramo,fill=col,width=anc)
        if tr:
            tt=max(tr,key=len); x,y=min(tt,key=lambda q:q[0])
            d.text((x+3,y-20),('Ec.' if Phi==0 else '%+d'%Phi),fill=col,font=fnt)
    # eje N-S
    xN,yN=norte_px(mu,R,xc,yc,beta,l_sol)
    vx,vy=xN-xc,yN-yc; nn=hypot(vx,vy); vx,vy=vx/nn,vy/nn
    d.line([(xc-vx*R,yc-vy*R),(xc+vx*R,yc+vy*R)],fill=(255,230,0),width=3)
    d.text((xc+vx*R-8,yc+vy*R-6),'N',fill=(255,230,0),font=fnt)
    d.text((xc-vx*R-8,yc-vy*R-18),'S',fill=(255,230,0),font=fnt)
    tilt=degrees(atan2(-(xN-xc),(yc-yN)))
    out=os.path.join(DIR_OUT,nombre+'_EJES.png')
    im.save(out)
    print('  OK %-26s id=%s eje=%.1f deg  disco_resid=%.2fpx'%(nombre,idobs,tilt,res))

con.close()
print('\nSalida en:', DIR_OUT)
