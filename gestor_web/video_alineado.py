# -*- coding: utf-8 -*-
"""
Alinea todas las fotos limpias (mismo centro, mismo radio, eje norte VERTICAL)
y monta un video del movimiento de las manchas a lo largo de los dias.

Cada frame: disco centrado y a escala fija, rotado para que el polo norte
solar quede ARRIBA. Se dibuja el circulo + eje amarillo (vertical) + ecuador.
Asi el Sol se ve siempre igual y las manchas se mueven entre dias.
"""
import os, sqlite3, glob, re, random, sys
import numpy as np, cv2
from math import sin, cos, atan2, sqrt, radians, degrees, pi, hypot
from PIL import Image
random.seed(7)

CARPETA=r'C:\Users\lydia\Downloads\tfg'
RUTA_BD=os.path.join(CARPETA,'manchas_tfg.db')
DIR_IN =os.path.join(CARPETA,'fotos_con_ejes_TODAS')
EXTRA  =os.path.join(CARPETA,'fotos abril 2026','fotos sin ejes con numeros')
DIR_OUT=os.path.join(CARPETA,'fotos abril 2026','fotos_con_ejes_TODAS','CON_EJES_CURVOS','video')
os.makedirs(DIR_OUT,exist_ok=True)
for _old in glob.glob(os.path.join(DIR_OUT,'frame_*.png')): os.remove(_old)  # limpiar frames viejos
EXCLUIR={'miercoles_22-4-26_10_19'}   # quitar el 22 por la manana
NOMBRE_VIDEO='video_manchas.mp4'
PHI_ZERO=radians(82+44/60+53.56/3600); LAMBDA_NORTH=radians(-13-52/60-21.41/3600)

S=900; CT=S//2; RT=380.0   # canvas, centro, radio destino
MANUAL={}
# discos elipticos: (centro_x, centro_y, semieje_a, semieje_b, angulo_deg) -> warp elipse->circulo
ELIPSE={'jueves_16-4-26_12_27':(384.1,374.2,335.0,343.4,22.9)}

# ---- deteccion disco (Canny + RANSAC) ----
def _c3(p1,p2,p3):
    ax,ay=p1;bx,by=p2;cx,cy=p3
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-6:return None
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return ux,uy,sqrt((ax-ux)**2+(ay-uy)**2)
def detectar(path):
    im=cv2.imread(path); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY); H,W=g.shape
    edges=cv2.Canny(cv2.GaussianBlur(g,(7,7),0),25,70)
    ys,xs=np.where(edges>0); k=(xs>4)&(xs<W-4)&(ys>4)&(ys<H-4)
    pts=np.c_[xs[k],ys[k]].astype(float)
    best=None;bn=0;bi=None
    for _ in range(6000):
        s=random.sample(range(len(pts)),3);c3=_c3(pts[s[0]],pts[s[1]],pts[s[2]])
        if not c3:continue
        xc,yc,R=c3
        if R<W*0.18 or R>W*1.8:continue
        dd=np.abs(np.sqrt((pts[:,0]-xc)**2+(pts[:,1]-yc)**2)-R)
        n=int((dd<4).sum())
        if n>bn:bn=n;best=c3;bi=dd<4
    x,y=pts[bi,0],pts[bi,1];A=np.c_[2*x,2*y,np.ones(len(x))];b=x*x+y*y
    sol,*_=np.linalg.lstsq(A,b,rcond=None)
    return sol[0],sol[1],sqrt(sol[2]+sol[0]**2+sol[1]**2)
def norte(mu,R,xc,yc,beta,l_sol):
    lam=LAMBDA_NORTH-(l_sol+pi); yv=sin(PHI_ZERO); xv=cos(PHI_ZERO)*sin(lam)
    A=atan2(yv,xv); rho=hypot(xv,yv); th=A-mu-beta
    return xc+rho*cos(th)*R, yc-rho*sin(th)*R

def limpiar(fn):
    b=os.path.splitext(os.path.basename(fn))[0]
    b=re.sub(r'^limpia\s+','',b); b=re.sub(r'\s*-\s*copia$','',b)
    return b.strip()
def fecha_key(nombre):
    m=re.search(r'(\d{1,2})-(\d{1,2})-\d{2}[_-](\d{1,2})[_-](\d{2})',nombre)
    if m: return (int(m.group(2)),int(m.group(1)),int(m.group(3)),int(m.group(4)))
    return (99,99,99,99)

con=sqlite3.connect(RUTA_BD); cur=con.cursor()
def obs(n):
    cur.execute("SELECT centro_x,centro_y,radio_sol,lambda_sol,mu_angulo,beta_optica FROM Observaciones WHERE archivo_img=?",(n,))
    return cur.fetchone()

# recopilar fotos limpias unicas, ordenadas por fecha
archivos=glob.glob(os.path.join(DIR_IN,'limpia *.png'))+glob.glob(os.path.join(EXTRA,'limpia *.png'))
vistos={};
for f in archivos:
    n=limpiar(f)
    if n in EXCLUIR: continue
    if n not in vistos: vistos[n]=f
items=sorted(vistos.items(), key=lambda kv: fecha_key(kv[0]))

frames=[]
for nombre,fn in items:
    row=obs(nombre)
    if not row: print('  [sin BD]',nombre); continue
    xcB,ycB,RB,lsd,mud,betad=row
    l_sol=radians(float(lsd)); mu=radians(mud); beta=radians(betad)
    img=cv2.imread(fn)
    if nombre in ELIPSE:
        # disco eliptico: warp anisotropo elipse->circulo (lo redondea) + norte arriba
        ex,ey,sa,sb,ang=ELIPSE[nombre]; ang=radians(ang)
        Rot=lambda a:np.array([[cos(a),-sin(a)],[sin(a),cos(a)]])
        Re=Rot(-ang); D=np.diag([RT/sa,RT/sb])
        xN,yN=norte(mu,300.0,ex,ey,beta,l_sol); v=np.array([xN-ex,yN-ey])
        w=D@Re@v; R2=Rot(-pi/2-atan2(w[1],w[0]))
        L=R2@D@Re; M=np.zeros((2,3)); M[:,:2]=L; M[:,2]=np.array([CT,CT])-L@np.array([ex,ey])
        tilt=0.0
    else:
        if nombre in MANUAL: xc,yc,R=MANUAL[nombre]
        else: xc,yc,R=detectar(fn)
        xN,yN=norte(mu,R,xc,yc,beta,l_sol)
        tilt=degrees(atan2(-(xN-xc),(yc-yN)))   # angulo del eje desde la vertical
        M=cv2.getRotationMatrix2D((xc,yc),-tilt,RT/R)   # rotar norte arriba, escalar
        M[0,2]+=CT-xc; M[1,2]+=CT-yc
    out=cv2.warpAffine(img,M,(S,S),flags=cv2.INTER_LANCZOS4,borderValue=(0,0,0))
    # recortar TODO lo de fuera del circulo (esquinas, textos, halo) -> fondo negro
    mask=np.zeros((S,S),np.uint8); cv2.circle(mask,(CT,CT),int(RT),255,-1)
    out[mask==0]=(0,0,0)
    # circulo BLANCO nitido + eje vertical (amarillo) + ecuador (verde)
    cv2.circle(out,(CT,CT),int(RT),(255,255,255),3,lineType=cv2.LINE_AA)
    cv2.line(out,(CT,CT-int(RT)),(CT,CT+int(RT)),(0,230,255),2,lineType=cv2.LINE_AA)  # eje N-S
    cv2.line(out,(CT-int(RT),CT),(CT+int(RT),CT),(0,210,0),2,lineType=cv2.LINE_AA)     # ecuador
    cv2.putText(out,'N',(CT-8,CT-int(RT)-8),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(out,'S',(CT-8,CT+int(RT)+22),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(out,nombre.replace('_',' '),(20,40),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
    pf=os.path.join(DIR_OUT,'frame_%02d_%s.png'%(len(frames),nombre))
    cv2.imwrite(pf,out); frames.append(out)
    print('  frame %02d  %-26s tilt=%.1f -> norte arriba'%(len(frames)-1,nombre,tilt))
con.close()

# montar video MP4 en H.264 (lo reproduce el navegador con boton Play; al
# llegar al ultimo dia se para, no hace bucle). Cada foto ~1 s.
import imageio
fps=10; reps=10
ruta_mp4=os.path.join(DIR_OUT,NOMBRE_VIDEO)
wr=imageio.get_writer(ruta_mp4, fps=fps, codec='libx264', quality=8,
                      macro_block_size=8, ffmpeg_params=['-pix_fmt','yuv420p'])
for fr in frames:
    rgb=cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)
    for _ in range(reps): wr.append_data(rgb)
wr.close()
# tambien el gif por si acaso
gif=[Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)) for fr in frames]
gif[0].save(os.path.join(DIR_OUT,'video_manchas.gif'),save_all=True,
            append_images=gif[1:],duration=900)
print('\n%d frames -> %s'%(len(frames),DIR_OUT))
print('  %s (H.264)  y  video_manchas.gif'%NOMBRE_VIDEO)
