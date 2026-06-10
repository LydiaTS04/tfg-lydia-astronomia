# -*- coding: utf-8 -*-
"""
CUADRICULA HELIOGRAFICA CURVA sobre la foto del Sol.
Transformacion INVERSA (latitud Phi, longitud L) -> pixel.

Dibuja el ECUADOR y los PARALELOS curvos (su curvatura sale sola
al proyectar cada punto, porque B0 != 0).

Es la inversa EXACTA de solve_mancha_heliografica() del codigo bueno.
"""
import os, sqlite3
from math import sin, cos, asin, atan2, sqrt, radians, degrees, pi
from PIL import Image, ImageDraw, ImageFont

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(CARPETA, 'gestor_web', 'manchas_tfg.db')
FECHA   = '14-04-2026 11:18'

# --- constantes del codigo (polo solar ecliptica) ---
PHI_ZERO     = radians(82.0 + 44.0/60.0 + 53.56/3600.0)
LAMBDA_NORTH = radians(-13.0 - 52.0/60.0 - 21.41/3600.0)

# ============================================================
# FORWARD (copiada del codigo, para verificar)
# ============================================================
def forward(mu, R, xm, ym, xc, yc, beta, l_sol):
    dx = xm - xc; dy = -(ym - yc)
    r = sqrt(dx*dx + dy*dy); rho = r/R
    theta_m = atan2(dy, dx)
    A = theta_m + mu + beta
    phi_M = asin(max(-1,min(1, rho*sin(A))))
    sin_lam = (rho*cos(A))/cos(phi_M) if cos(phi_M)!=0 else 0.0
    lam_M = asin(max(-1,min(1, sin_lam)))
    L = (l_sol+pi) + lam_M - LAMBDA_NORTH
    sinPhi = sin(PHI_ZERO)*sin(phi_M) + cos(PHI_ZERO)*cos(phi_M)*cos(L)
    Phi = asin(max(-1,min(1, sinPhi)))
    return degrees(Phi)

# ============================================================
# INVERSA:  (Phi, L_solar) -> pixel
# Trabajamos con vectores en el "frame de proyeccion":
#   v = [profundidad, derecha, arriba]
#   v = [cos f cos l , cos f sin l , sin f]   (f=phi_M, l=lambda_M)
#   visible  <=>  profundidad (v[0]) > 0
#   sin(Phi) = v . pole_proj
# ============================================================
def construir_pole_proj(l_sol):
    C = (l_sol + pi) - LAMBDA_NORTH          # L = lambda_M + C
    return (cos(PHI_ZERO)*cos(C), -cos(PHI_ZERO)*sin(C), sin(PHI_ZERO))

def base_perp(p):
    # dos vectores ortonormales perpendiculares a p
    ref = (0.0,0.0,1.0)
    if abs(p[2])>0.99: ref=(1.0,0.0,0.0)
    # u = p x ref  (normalizado)
    ux = p[1]*ref[2]-p[2]*ref[1]
    uy = p[2]*ref[0]-p[0]*ref[2]
    uz = p[0]*ref[1]-p[1]*ref[0]
    n = sqrt(ux*ux+uy*uy+uz*uz); u=(ux/n,uy/n,uz/n)
    # w = p x u
    wx = p[1]*u[2]-p[2]*u[1]
    wy = p[2]*u[0]-p[0]*u[2]
    wz = p[0]*u[1]-p[1]*u[0]
    return u,(wx,wy,wz)

def punto_a_pixel(v, mu, R, xc, yc, beta):
    """v (frame proyeccion) -> (x,y) pixel, o None si no es visible."""
    if v[0] <= 0.001:           # cara oculta del Sol
        return None
    phi_M = asin(max(-1,min(1, v[2])))
    rho = sqrt(v[1]*v[1] + v[2]*v[2])
    A = atan2(v[2], v[1])
    theta_m = A - mu - beta
    r = rho*R
    x = xc + r*cos(theta_m)
    y = yc - r*sin(theta_m)
    return (x, y)

def parametrizar_paralelo(Phi_deg, l_sol, mu, R, xc, yc, beta, n=400):
    """Devuelve lista de tramos visibles [(x,y),...] del paralelo Phi."""
    Phi = radians(Phi_deg)
    p = construir_pole_proj(l_sol)
    u,w = base_perp(p)
    sP, cP = sin(Phi), cos(Phi)
    tramos=[]; actual=[]
    for i in range(n+1):
        t = 2*pi*i/n
        ct,st = cos(t), sin(t)
        v = (sP*p[0]+cP*(ct*u[0]+st*w[0]),
             sP*p[1]+cP*(ct*u[1]+st*w[1]),
             sP*p[2]+cP*(ct*u[2]+st*w[2]))
        px = punto_a_pixel(v, mu, R, xc, yc, beta)
        if px is None:
            if len(actual)>1: tramos.append(actual)
            actual=[]
        else:
            actual.append(px)
    if len(actual)>1: tramos.append(actual)
    return tramos

# ============================================================
# MAIN
# ============================================================
def main():
    con=sqlite3.connect(RUTA_BD); cur=con.cursor()
    cur.execute("SELECT archivo_img,centro_x,centro_y,radio_sol,lambda_sol,mu_angulo,beta_optica "
                "FROM Observaciones WHERE fecha_hora=?", (FECHA,))
    arch,xc,yc,R,l_sol_d,mu_d,beta_d = cur.fetchone()
    l_sol=radians(float(l_sol_d)); mu=radians(mu_d); beta=radians(beta_d)
    cur.execute("SELECT id_grupo,pixel_x,pixel_y,latitud_phi FROM Mediciones "
                "WHERE id_observacion=2 ORDER BY id_grupo")
    manchas=cur.fetchall(); con.close()

    # --- verificacion round-trip (inversa correcta?) ---
    print("== VERIFICACION round-trip (Phi BD vs Phi recomputado) ==")
    for g,xm,ym,lat in manchas:
        print("  M%s pixel(%d,%d)  Phi_BD=%+6.2f  forward=%+6.2f" %
              (g,xm,ym,lat, forward(mu,R,xm,ym,xc,yc,beta,l_sol)))

    # --- buscar la foto ---
    ruta_img=None
    for ext in ('.JPEG','.jpeg','.jpg','.JPG','.png'):
        p=os.path.join(CARPETA,'fotos abril 2026',arch+ext)
        if os.path.exists(p): ruta_img=p; break
    img=Image.open(ruta_img).convert('RGB'); d=ImageDraw.Draw(img)
    try: fnt=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',26)
    except: fnt=ImageFont.load_default()

    # --- paralelos ---
    for Phi in range(-75,76,15):
        if Phi==0:
            color=(0,255,0); ancho=6              # ECUADOR verde lima grueso
        else:
            color=(0,220,255); ancho=2            # paralelos cian
        tr=parametrizar_paralelo(Phi,l_sol,mu,R,xc,yc,beta)
        for tramo in tr:
            d.line(tramo, fill=color, width=ancho)
        # etiqueta del paralelo en su extremo izquierdo visible
        if tr:
            tramo=max(tr,key=len)
            x,y=min(tramo,key=lambda q:q[0])      # punto mas a la izquierda
            txt=('  ECUADOR 0' if Phi==0 else '  %+d' % Phi)
            d.text((x,y-26),txt,fill=color,font=fnt)

    # --- manchas ---
    for g,xm,ym,lat in manchas:
        d.ellipse([xm-10,ym-10,xm+10,ym+10],outline=(255,160,0),width=5)
        d.text((xm+14,ym-30),"M%s (%+.0f)" % (g,lat),fill=(255,160,0),font=fnt)

    salida=os.path.join(CARPETA,'documentos explicacion','martes14_cuadricula_curva.png')
    img.save(salida)
    print("\nGuardado:", salida)

if __name__=='__main__':
    main()
