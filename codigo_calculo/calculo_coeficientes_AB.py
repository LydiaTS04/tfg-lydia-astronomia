# -*- coding: utf-8 -*-
"""
Replica EXACTA del ajuste no ponderado del codigo (sin tocar BD ni codigo).
Calcula A, B con TODOS los datos (validacion) y SIN el 22-manana (id_obs=14).
"""
import sqlite3, math
from datetime import datetime

import os; BD=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gestor_web', 'manchas_tfg.db')
FAYE_A=14.370; FAYE_B=-2.300
TMIN,TMAX=22.0,32.0
FMTS=['%d-%m-%Y %H:%M','%d/%m/%Y %H:%M','%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M','%d-%m-%Y']

def fecha_a_dias(s):
    for f in FMTS:
        try: return datetime.strptime(s.strip(),f).timestamp()/86400.0
        except ValueError: pass
    return None

def delta_longitud_real(L1,L2,dt):
    om=FAYE_A; dL=(L2-L1)%360.0; k=int(om*dt/360.0)
    dLr=dL+k*360.0; dLa=dL+(k+1)*360.0
    if abs(dLa/dt-om)<abs(dLr/dt-om): dLr=dLa
    return dLr

def calcular(excluir=None):
    con=sqlite3.connect(BD); cur=con.cursor()
    q=("SELECT m.id_grupo,o.fecha_hora,m.latitud_phi,m.longitud_L "
       "FROM Mediciones m JOIN Observaciones o ON m.id_observacion=o.id_observacion "
       "WHERE m.latitud_phi IS NOT NULL AND m.longitud_L IS NOT NULL "
       "AND COALESCE(m.excluida,0)=0")
    if excluir is not None: q+=" AND m.id_observacion!=%d"%excluir
    q+=" ORDER BY m.id_grupo,o.fecha_hora"
    cur.execute(q); filas=cur.fetchall(); con.close()
    grupos={}
    for g,fh,phi,L in filas: grupos.setdefault(g,[]).append((fh,phi,L))
    puntos=[]
    for g,obs in sorted(grupos.items(),key=lambda kv:str(kv[0])):
        n=len(obs)
        if n<2: continue
        phis=[o[1] for o in obs]; phi_med=sum(phis)/n
        ts=[fecha_a_dias(o[0]) for o in obs]; Ls=[o[2] for o in obs]
        if any(t is None for t in ts): continue
        pares=sorted(zip(ts,Ls),key=lambda p:p[0])
        t1,L1=pares[0]; tN,LN=pares[-1]; dt=tN-t1
        if dt<=0: continue
        dL=delta_longitud_real(L1,LN,dt)
        if abs(dL)<0.1: continue
        om=dL/dt; T=360.0/om
        puntos.append({'g':g,'N':n,'phi':phi_med,'T':T,'om':om})
    susp=lambda p: p['T']>TMAX or p['T']<TMIN
    pf=[p for p in puntos if not susp(p)]
    N=len(pf); Sx=Sy=Sxx=Sxy=0.0
    for p in pf:
        xi=math.sin(math.radians(p['phi']))**2; yi=p['om']
        Sx+=xi;Sy+=yi;Sxx+=xi*xi;Sxy+=xi*yi
    D=N*Sxx-Sx*Sx
    A=(Sxx*Sy-Sx*Sxy)/D; B=(N*Sxy-Sx*Sy)/D
    ss=sum((p['om']-(A+B*math.sin(math.radians(p['phi']))**2))**2 for p in pf)
    s2=ss/(N-2) if N>2 else 0.0
    sigA=math.sqrt(s2*Sxx/D) if N>2 else 0.0
    sigB=math.sqrt(s2*N/D)   if N>2 else 0.0
    return A,B,sigA,sigB,N,len(puntos),pf

for etiqueta,exc in [("CON TODO (validacion)",None),("SIN 22-MANANA (id=14)",14)]:
    A,B,sA,sB,N,Ntot,pf=calcular(exc)
    print("\n===== %s ====="%etiqueta)
    print("  Manchas en grafico: %d  | usadas en fit (no sospechosas): %d"%(Ntot,N))
    print("  A = %+.3f +- %.3f  grados/dia"%(A,sA))
    print("  B = %+.3f +- %.3f  grados/dia"%(B,sB))
    print("  (Faye: A=14.370  B=-2.300)")
    print("  grupos en fit:", ", ".join("M%s(phi=%+.1f,T=%.1f)"%(p['g'],p['phi'],p['T']) for p in pf))
