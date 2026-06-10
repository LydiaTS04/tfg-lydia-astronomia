# -*- coding: utf-8 -*-
"""
Cuadricula heliografica CURVA sobre la imagen LIMPIA numerada (761x773).
Detecta el disco en esa imagen y reutiliza mu, beta, lambda_sol de la BD
(angulos fisicos, no dependen del tamano de la foto).
"""
import os, sqlite3
import numpy as np
from math import sin, cos, asin, atan2, sqrt, radians, pi
from PIL import Image, ImageDraw, ImageFont

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(CARPETA, 'gestor_web', 'manchas_tfg.db')
IMG     = os.path.join(CARPETA, 'fotos abril 2026', 'manchas ejes martes_14-4-26_11_18.png')
FECHA   = '14-04-2026 11:18'
PHI_ZERO     = radians(82.0 + 44.0/60.0 + 53.56/3600.0)
LAMBDA_NORTH = radians(-13.0 - 52.0/60.0 - 21.41/3600.0)

def construir_pole_proj(l_sol):
    C = (l_sol + pi) - LAMBDA_NORTH
    return (cos(PHI_ZERO)*cos(C), -cos(PHI_ZERO)*sin(C), sin(PHI_ZERO))

def base_perp(p):
    ref=(0.,0.,1.)
    if abs(p[2])>0.99: ref=(1.,0.,0.)
    ux=p[1]*ref[2]-p[2]*ref[1]; uy=p[2]*ref[0]-p[0]*ref[2]; uz=p[0]*ref[1]-p[1]*ref[0]
    n=sqrt(ux*ux+uy*uy+uz*uz); u=(ux/n,uy/n,uz/n)
    wx=p[1]*u[2]-p[2]*u[1]; wy=p[2]*u[0]-p[0]*u[2]; wz=p[0]*u[1]-p[1]*u[0]
    return u,(wx,wy,wz)

def punto_a_pixel(v, mu, R, xc, yc, beta):
    if v[0] <= 0.001: return None
    rho=sqrt(v[1]*v[1]+v[2]*v[2]); A=atan2(v[2],v[1])
    th=A-mu-beta; r=rho*R
    return (xc+r*cos(th), yc-r*sin(th))

def paralelo(Phi_deg,l_sol,mu,R,xc,yc,beta,n=500):
    Phi=radians(Phi_deg); p=construir_pole_proj(l_sol); u,w=base_perp(p)
    sP,cP=sin(Phi),cos(Phi); tramos=[]; act=[]
    for i in range(n+1):
        t=2*pi*i/n; ct,st=cos(t),sin(t)
        v=(sP*p[0]+cP*(ct*u[0]+st*w[0]),
           sP*p[1]+cP*(ct*u[1]+st*w[1]),
           sP*p[2]+cP*(ct*u[2]+st*w[2]))
        px=punto_a_pixel(v,mu,R,xc,yc,beta)
        if px is None:
            if len(act)>1: tramos.append(act)
            act=[]
        else: act.append(px)
    if len(act)>1: tramos.append(act)
    return tramos

# --- detectar disco en la imagen limpia ---
im=Image.open(IMG).convert('RGB'); a=np.asarray(im).astype(int)
Rc,Gc,Bc=a[:,:,0],a[:,:,1],a[:,:,2]
mask=(Rc>120)&(Bc>110)&(Gc>70)&((Rc+Gc+Bc)>330)
ys,xs=np.where(mask)
xc=xs.mean(); yc=ys.mean(); R=sqrt(len(xs)/pi)
print('Disco limpio -> centro=(%.1f,%.1f) R=%.1f'%(xc,yc,R))

# --- mu, beta, lambda_sol de la BD ---
con=sqlite3.connect(RUTA_BD); cur=con.cursor()
cur.execute("SELECT lambda_sol,mu_angulo,beta_optica FROM Observaciones WHERE fecha_hora=?",(FECHA,))
l_sol_d,mu_d,beta_d=cur.fetchone(); con.close()
l_sol=radians(float(l_sol_d)); mu=radians(mu_d); beta=radians(beta_d)

d=ImageDraw.Draw(im)
try: fnt=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',20)
except: fnt=ImageFont.load_default()

for Phi in range(-75,76,15):
    if Phi==0: color=(0,210,0); ancho=5
    else:      color=(0,170,230); ancho=2
    tr=paralelo(Phi,l_sol,mu,R,xc,yc,beta)
    for tramo in tr: d.line(tramo,fill=color,width=ancho)
    if tr:
        tramo=max(tr,key=len); x,y=min(tramo,key=lambda q:q[0])
        d.text((x+4,y-22),('Ecuador' if Phi==0 else '%+d'%Phi),fill=color,font=fnt)

# --- EJE N-S (polo norte corregido, CON l_sol) ---
def calcular_norte(mu_s,R_s,xc_,yc_,beta_o,l_sol_):
    lam=LAMBDA_NORTH-(l_sol_+pi)
    yv=sin(PHI_ZERO); xv=cos(PHI_ZERO)*sin(lam)
    A=atan2(yv,xv); rho=sqrt(xv*xv+yv*yv); th=A-mu_s-beta_o
    return xc_+rho*cos(th)*R_s, yc_-rho*sin(th)*R_s
xN,yN=calcular_norte(mu,R,xc,yc,beta,l_sol)
vx,vy=xN-xc,yN-yc; nrm=sqrt(vx*vx+vy*vy); vx,vy=vx/nrm,vy/nrm
d.line([(xc-vx*R,yc-vy*R),(xc+vx*R,yc+vy*R)],fill=(255,230,0),width=4)  # eje amarillo
d.text((xc+vx*R-10,yc+vy*R-4),'N',fill=(255,230,0),font=fnt)
d.text((xc-vx*R-10,yc-vy*R-20),'S',fill=(255,230,0),font=fnt)
print('Eje: polo N en (%.0f,%.0f)  inclinacion=%.2f deg desde vertical'%(
    xN,yN,__import__('math').degrees(atan2(-(xN-xc),(yc-yN)))))

# --- VALIDACION: mapear manchas de la foto grande (px exactos) a la limpia ---
XCB,YCB,RB=580.0,586.0,538.0          # centro/radio en la foto grande (BD)
con=sqlite3.connect(RUTA_BD); cur=con.cursor()
cur.execute("SELECT id_grupo,pixel_x,pixel_y,latitud_phi FROM Mediciones WHERE id_observacion=2 ORDER BY id_grupo")
for g,xm,ym,lat in cur.fetchall():
    xn=xc+(R/RB)*(xm-XCB); yn=yc+(R/RB)*(ym-YCB)
    print("M%s -> limpia(%.0f,%.0f) lat=%+.1f"%(g,xn,yn,lat))
con.close()

salida=os.path.join(CARPETA,'documentos explicacion','martes14_LIMPIA_cuadricula.png')
im.save(salida); print('Guardado:',salida)
