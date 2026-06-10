# -*- coding: utf-8 -*-
"""
VIDEO profesional del movimiento de las manchas.
- Alinea: mismo centro/radio, eje N-S vertical (norte arriba).
- Rota SOLO la foto (cubica), recorta el disco sobre fondo negro,
  normaliza el brillo (sin parpadeo), enfoca (unsharp) y dibuja la
  cuadricula VECTORIAL con antialias DESPUES (lineas nitidas).
Salida: CON_EJES_CURVOS/video/  (frames + GIF + MP4)
"""
import os, sqlite3, glob, re, random
import numpy as np, cv2
from math import sin, cos, atan2, sqrt, radians, degrees, pi, hypot
from PIL import Image
random.seed(7)

CARPETA=r'C:\Users\lydia\Downloads\tfg'
RUTA_BD=os.path.join(CARPETA,'manchas_tfg.db')
BASE=os.path.join(CARPETA,'fotos abril 2026','fotos_con_ejes_TODAS')
DIR_EJES=os.path.join(BASE,'CON_EJES_CURVOS')
DIR_CLEAN=[BASE, os.path.join(CARPETA,'fotos abril 2026','fotos sin ejes con numeros')]
DIR_OUT=os.path.join(DIR_EJES,'video'); os.makedirs(DIR_OUT,exist_ok=True)
PHI_ZERO=radians(82+44/60+53.56/3600); LAMBDA_NORTH=radians(-13-52/60-21.41/3600)
CANVAS=820; CX=CY=410; RC=360
MANUAL={'jueves_16-4-26_12_27':(345.0,365.0,347.0)}
OMITIR=set()   # (vuelta al video con las 11 fotos, incluido el 22-mañana)
BRILLO_OBJ=205.0   # brillo medio del disco objetivo (anti-parpadeo)

# ---- geometria (inversa) ----
def pole_proj(l_sol):
    C=(l_sol+pi)-LAMBDA_NORTH
    return (cos(PHI_ZERO)*cos(C),-cos(PHI_ZERO)*sin(C),sin(PHI_ZERO))
def base_perp(p):
    ref=(0.,0.,1.)
    if abs(p[2])>0.99: ref=(1.,0.,0.)
    ux=p[1]*ref[2]-p[2]*ref[1];uy=p[2]*ref[0]-p[0]*ref[2];uz=p[0]*ref[1]-p[1]*ref[0]
    n=sqrt(ux*ux+uy*uy+uz*uz);u=(ux/n,uy/n,uz/n)
    wx=p[1]*u[2]-p[2]*u[1];wy=p[2]*u[0]-p[0]*u[2];wz=p[0]*u[1]-p[1]*u[0]
    return u,(wx,wy,wz)
def punto_px(v,mu,R,xc,yc,beta):
    if v[0]<=0.001: return None
    rho=sqrt(v[1]*v[1]+v[2]*v[2]);A=atan2(v[2],v[1]);th=A-mu-beta;r=rho*R
    return (xc+r*cos(th),yc-r*sin(th))
def paralelo(Phi_deg,l_sol,mu,R,xc,yc,beta,n=600):
    Phi=radians(Phi_deg);p=pole_proj(l_sol);u,w=base_perp(p)
    sP,cP=sin(Phi),cos(Phi);tr=[];act=[]
    for i in range(n+1):
        t=2*pi*i/n;ct,st=cos(t),sin(t)
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
    yv=sin(PHI_ZERO);xv=cos(PHI_ZERO)*sin(lam)
    A=atan2(yv,xv);rho=hypot(xv,yv);th=A-mu-beta
    return (xc+rho*cos(th)*R,yc-rho*sin(th)*R)

# ---- deteccion disco (Canny+RANSAC) ----
def _circ3(p1,p2,p3):
    ax,ay=p1;bx,by=p2;cx,cy=p3
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-6:return None
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return ux,uy,sqrt((ax-ux)**2+(ay-uy)**2)
def detectar(path):
    im=cv2.imread(path);g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);H,W=g.shape
    gb=cv2.GaussianBlur(g,(7,7),0);edges=cv2.Canny(gb,25,70)
    ys,xs=np.where(edges>0);k=(xs>4)&(xs<W-4)&(ys>4)&(ys<H-4)
    pts=np.c_[xs[k],ys[k]].astype(float)
    best=None;bn=0;bi=None
    for _ in range(6000):
        s=random.sample(range(len(pts)),3);c3=_circ3(pts[s[0]],pts[s[1]],pts[s[2]])
        if not c3:continue
        xc,yc,R=c3
        if R<W*0.18 or R>W*1.8:continue
        dd=np.abs(np.sqrt((pts[:,0]-xc)**2+(pts[:,1]-yc)**2)-R)
        n=int((dd<4).sum())
        if n>bn:bn=n;best=c3;bi=dd<4
    x,y=pts[bi,0],pts[bi,1];A=np.c_[2*x,2*y,np.ones(len(x))];b=x*x+y*y
    sol,*_=np.linalg.lstsq(A,b,rcond=None);xc,yc=sol[0],sol[1];R=sqrt(sol[2]+xc*xc+yc*yc)
    return xc,yc,R
def buscar(arch):
    for d in DIR_CLEAN:
        g=glob.glob(os.path.join(d,'limpia '+arch+'.png')) or glob.glob(os.path.join(d,'limpia '+arch+'*.png'))
        if g: return g[0]
    return None

# ---- obs ordenadas por fecha ----
con=sqlite3.connect(RUTA_BD);cur=con.cursor()
cur.execute("SELECT archivo_img,fecha_hora,lambda_sol,mu_angulo,beta_optica FROM Observaciones")
obs=[]
for arch,fh,ls,mu,be in cur.fetchall():
    if arch in OMITIR: continue
    if not os.path.exists(os.path.join(DIR_EJES,arch+'_EJES.png')): continue
    cl=buscar(arch)
    if not cl: continue
    m=re.match(r'(\d+)-(\d+)-(\d+)\s+(\d+):(\d+)',fh)
    key=(int(m.group(3)),int(m.group(2)),int(m.group(1)),int(m.group(4)),int(m.group(5)))
    obs.append((key,arch,fh,radians(float(ls)),radians(mu),radians(be),cl))
obs.sort();con.close()

def Taff(M,p): return (M[0,0]*p[0]+M[0,1]*p[1]+M[0,2], M[1,0]*p[0]+M[1,1]*p[1]+M[1,2])

frames=[]
print('Generando video pro de %d frames...\n'%len(obs))
for idx,(key,arch,fh,l_sol,mu,beta,cl) in enumerate(obs,1):
    xc,yc,R = MANUAL[arch] if arch in MANUAL else detectar(cl)
    xN,yN=norte_px(mu,R,xc,yc,beta,l_sol)
    rot=90.0-degrees(atan2(-(yN-yc),(xN-xc)))
    M=cv2.getRotationMatrix2D((xc,yc),rot,RC/R); M[0,2]+=CX-xc; M[1,2]+=CY-yc
    clean=cv2.imread(cl)
    warp=cv2.warpAffine(clean,M,(CANVAS,CANVAS),flags=cv2.INTER_CUBIC,borderValue=(0,0,0))
    # mascara circular (disco un pelin menor para limpiar el borde)
    mask=np.zeros((CANVAS,CANVAS),np.uint8); cv2.circle(mask,(CX,CY),RC-3,255,-1)
    # normalizar brillo del disco (anti-parpadeo)
    disk=warp[mask>0].astype(np.float32); m=disk.reshape(-1,3).mean()
    warp=np.clip(warp.astype(np.float32)*(BRILLO_OBJ/max(m,1)),0,255).astype(np.uint8)
    # unsharp (enfoque suave)
    blur=cv2.GaussianBlur(warp,(0,0),2.5); warp=cv2.addWeighted(warp,1.4,blur,-0.4,0)
    # componer sobre fondo negro con borde suave
    out=np.zeros_like(warp)
    m3=cv2.GaussianBlur(mask,(0,0),1.2).astype(np.float32)/255.0
    out=(warp.astype(np.float32)*m3[...,None]).astype(np.uint8)
    # circulo del limbo (blanco fino)
    cv2.circle(out,(CX,CY),RC-3,(235,235,235),2,cv2.LINE_AA)
    # cuadricula vectorial (transformar puntos -> nitido)
    for Phi in range(-75,76,15):
        col=(60,235,60) if Phi==0 else (235,170,40); anc=3 if Phi==0 else 1
        for seg in paralelo(Phi,l_sol,mu,R,xc,yc,beta):
            p=np.array([Taff(M,q) for q in seg],np.int32)
            cv2.polylines(out,[p],False,col,anc,cv2.LINE_AA)
    # eje N-S
    a=np.array([Taff(M,(xc-(xN-xc)/hypot(xN-xc,yN-yc)*R, yc-(yN-yc)/hypot(xN-xc,yN-yc)*R)),
                Taff(M,(xN,yN))],np.int32)
    cv2.line(out,tuple(a[0]),tuple(a[1]),(40,235,235),2,cv2.LINE_AA)
    cv2.putText(out,'N',(CX-8,CY-RC+24),cv2.FONT_HERSHEY_SIMPLEX,0.7,(40,235,235),2,cv2.LINE_AA)
    cv2.putText(out,'S',(CX-8,CY+RC-10),cv2.FONT_HERSHEY_SIMPLEX,0.7,(40,235,235),2,cv2.LINE_AA)
    # fecha (barra inferior)
    cv2.rectangle(out,(0,CANVAS-46),(CANVAS,CANVAS),(0,0,0),-1)
    cv2.putText(out,'Sol  '+fh,(18,CANVAS-15),cv2.FONT_HERSHEY_DUPLEX,0.9,(255,255,255),1,cv2.LINE_AA)
    fpath=os.path.join(DIR_OUT,'frame_%02d_%s.png'%(idx,arch))
    cv2.imwrite(fpath,out); frames.append(out)
    print('  %02d  %-20s rot=%6.1f  R=%.0f'%(idx,fh,rot,R))

pil=[Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)) for f in frames]
pil[0].save(os.path.join(DIR_OUT,'video_manchas.gif'),save_all=True,
            append_images=pil[1:],duration=900,loop=0)
h,w=frames[0].shape[:2]
vw=cv2.VideoWriter(os.path.join(DIR_OUT,'video_manchas.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),1.5,(w,h))
for f in frames: vw.write(f)
vw.release()
print('\nGIF + MP4 en:',DIR_OUT)
