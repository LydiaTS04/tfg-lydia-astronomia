# -*- coding: utf-8 -*-
import sys
import sqlite3
import os
from math import sin, cos, tan, asin, acos, atan2, radians, degrees, pi, sqrt

# Intentar cargar librerías para el Visor 3D
try:
    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd
    VISUALIZACION_ACTIVA = True
except ImportError:
    VISUALIZACION_ACTIVA = False

# =========================
# CONFIGURACIÓN DE RUTAS (Protegidas con 'r')
# =========================
CARPETA_TFG = r'C:\Users\lydia\Downloads\tfg'
RUTA_BD = os.path.join(CARPETA_TFG, 'manchas_tfg.db')
EPSILON_J2000 = radians(23.0 + 26.0/60.0 + 21.4) # Oblicuidad J2000

# =========================
# BASE DE DATOS (SQLite)
# =========================

def inicializar_bd():
    if not os.path.exists(CARPETA_TFG):
        os.makedirs(CARPETA_TFG)
    
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    
    # Tabla de fotos y estado del Sol
    cursor.execute('''CREATE TABLE IF NOT EXISTS Observaciones (
        id_observacion INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora TEXT,
        archivo_img TEXT UNIQUE,
        centro_x REAL, centro_y REAL, radio_sol REAL,
        lambda_sol REAL, B0_latitud REAL, P_angulo REAL)''')
    
    # Tabla de las manchas calculadas
    cursor.execute('''CREATE TABLE IF NOT EXISTS Mediciones (
        id_medicion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_observacion INTEGER,
        id_grupo TEXT,
        pixel_x REAL, pixel_y REAL, rho REAL,
        latitud_phi REAL, longitud_L REAL,
        FOREIGN KEY(id_observacion) REFERENCES Observaciones(id_observacion),
        UNIQUE(id_observacion, id_grupo))''')
    
    conexion.commit()
    return conexion

# =========================
# MATEMÁTICAS DEL TFG
# =========================

def wrap_pm180(d): return (d + 180) % 360 - 180

def solve_direct_equatorial(phi, delta, H):
    sin_h = sin(delta)*sin(phi) + cos(delta)*cos(phi)*cos(H)
    h = asin(max(-1, min(1, sin_h)))
    num = sin(H)
    den = sin(phi)*cos(H) - tan(delta)*cos(phi)
    return h, atan2(num, den)

def solve_ecliptic_to_equatorial(lmb_rad, beta_rad, eps_rad):
    sin_delta = sin(beta_rad)*cos(eps_rad) + cos(beta_rad)*sin(eps_rad)*sin(lmb_rad)
    delta = asin(max(-1, min(1, sin_delta)))
    y = cos(beta_rad)*sin(lmb_rad)*cos(eps_rad) - sin(beta_rad)*sin(eps_rad)
    x = cos(beta_rad)*cos(lmb_rad)
    return atan2(y, x), delta

def solve_mu_and_azpi(phi, theta, h_sun, eps):
    # Cálculo de Mu (Magnitud)
    cos_mu = (sin(phi)*cos(eps) - cos(phi)*sin(eps)*sin(theta)) / cos(h_sun)
    mu = acos(max(-1, min(1, cos_mu)))
    # Cálculo de Azimut de Pi
    num_az = -(cos(theta) * sin(eps))
    den_az = (cos(eps)*cos(phi)) + (sin(eps)*sin(phi)*sin(theta))
    return mu, atan2(num_az, den_az)

def solve_heliographic(mu_signed, R_s, xm, ym, xc, yc, beta_opt, lambda_sol_deg):
    # Parámetros físicos del Sol para la fecha
    L_rad = radians(lambda_sol_deg)
    L76 = radians(lambda_sol_deg - 76.0)
    P_rad = radians(-23.5 * cos(L_rad) - 7.2 * cos(L76))
    B0_rad = radians(7.2 * sin(L76))
    
    # Geometría en la foto
    dx, dy = xm - xc, ym - yc
    r_px = sqrt(dx**2 + dy**2)
    rho = min(1.0, r_px / R_s)
    phi_M = asin(rho) # Distancia angular al centro
    
    # Ángulo de giro real (alpha) considerando Mu y orientación óptica
    alpha = atan2(dx, dy) + mu_signed + beta_opt - P_rad
    
    # Fórmulas finales de Carrington
    sin_Phi = sin(B0_rad)*cos(phi_M) + cos(B0_rad)*sin(phi_M)*cos(alpha)
    Phi = asin(max(-1, min(1, sin_Phi)))
    
    sin_L = (sin(phi_M)*sin(alpha)) / cos(Phi)
    L = asin(max(-1, min(1, sin_L)))
    
    return Phi, L, rho, P_rad, B0_rad

# =========================
# VISOR 3D Y GESTIÓN
# =========================

def visor_3d_interactivo(conn):
    if not VISUALIZACION_ACTIVA:
        print("\n [X] Error: Librerías 3D no instaladas.")
        return
    
    fechas_in = input("\nFechas a comparar separadas por coma (ej: 2024-04-01, 2024-04-02): ")
    lista_f = [f.strip() for f in fechas_in.split(',')]
    
    fig = go.Figure()
    # Esfera solar
    u, v = np.mgrid[0:2*pi:40j, 0:pi:20j]
    fig.add_trace(go.Surface(x=np.cos(u)*np.sin(v), y=np.sin(u)*np.sin(v), z=np.cos(v), 
                             opacity=0.15, showscale=False, name="Sol", hoverinfo='none'))
    
    colores = ['red', 'blue', 'green', 'orange', 'purple']
    encontrado = False
    
    for i, fecha in enumerate(lista_f):
        query = "SELECT m.id_grupo, m.latitud_phi, m.longitud_L FROM Mediciones m JOIN Observaciones o ON m.id_observacion = o.id_observacion WHERE o.fecha_hora LIKE ?"
        df = pd.read_sql_query(query, conn, params=(fecha + '%',))
        
        if not df.empty:
            encontrado = True
            lat_r, lon_r = np.radians(df['latitud_phi']), np.radians(df['longitud_L'])
            # Conversión a coordenadas 3D para el visor
            x = np.cos(lat_r) * np.sin(lon_r)
            y = np.cos(lat_r) * np.cos(lon_r)
            z = np.sin(lat_r)
            
            fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='markers+text', name=f"Día: {fecha}",
                                       text=df['id_grupo'], marker=dict(size=7, color=colores[i % 5])))
    
    if encontrado:
        fig.update_layout(title="Visor 3D Carrington - TFG", scene=dict(aspectmode='cube'))
        fig.show()
    else:
        print(" No se encontraron datos para esas fechas.")

# =========================
# BUCLE PRINCIPAL
# =========================

def main():
    conn = inicializar_bd()
    while True:
        print("\n" + "="*40)
        print("      APP SOLAR TFG - MENÚ PRINCIPAL")
        print("="*40)
        print("f) Calcular y Guardar Mancha")
        print("g) Gestor de Base de Datos / Visor 3D")
        print("q) Salir")
        
        opc = input("\nSelecciona una opción: ").lower()
        if opc == 'q': break

        if opc == 'f':
            print("\n--- REGISTRO DE MANCHA ---")
            fh = input("Fecha y Hora (AAAA-MM-DD HH:MM): ")
            img = input("Nombre de la foto (ej: img01.jpg): ")
            grp = input("ID de la mancha (ej: AR3590): ")
            
            # Datos astronómicos automáticos
            lam = float(input("Longitud Eclíptica Sol (lambda en grados): "))
            phi_o = radians(float(input("Latitud Observador (grados): ")))
            theta = radians(float(input("Hora Sidérea Local (en grados, h*15): ")))
            
            # Proceso automático de Mu y Az_pi
            al_s, de_s = solve_ecliptic_to_equatorial(radians(lam), 0, EPSILON_J2000)
            h_s, az_s = solve_direct_equatorial(phi_o, de_s, theta - al_s)
            mu_v, az_p = solve_mu_and_azpi(phi_o, theta, h_s, EPSILON_J2000)
            
            # Signo de Mu
            diff = wrap_pm180(degrees(az_p) - degrees(az_s))
            mu_signed = -mu_v if diff > 0 else mu_v
            
            # Datos de imagen
            rs = float(input("Radio Sol en la foto (píxeles): "))
            xc, yc = float(input("Centro Sol X: ")), float(input("Centro Sol Y: "))
            xm, ym = float(input("Mancha X: ")), float(input("Mancha Y: "))
            beta_opt = radians(float(input("Ángulo Óptica / Beta (grados): ")))
            
            # Cálculo Carrington
            Phi, L, rho, P, B0 = solve_heliographic(mu_signed, rs, xm, ym, xc, yc, beta_opt, lam)
            
            # Guardar
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO Observaciones (fecha_hora, archivo_img, centro_x, centro_y, radio_sol, lambda_sol, B0_latitud, P_angulo) VALUES (?,?,?,?,?,?,?,?)", 
                               (fh, img, xc, yc, rs, lam, degrees(B0), degrees(P)))
                cursor.execute("SELECT id_observacion FROM Observaciones WHERE archivo_img=?", (img,))
                id_o = cursor.fetchone()[0]
                cursor.execute("INSERT OR REPLACE INTO Mediciones (id_observacion, id_grupo, pixel_x, pixel_y, rho, latitud_phi, longitud_L) VALUES (?,?,?,?,?,?,?)", 
                               (id_o, grp, xm, ym, rho, degrees(Phi), degrees(L)))
                conn.commit()
                print(f"\n [!] ÉXITO: Latitud={degrees(Phi):.4f}, Longitud={degrees(L):.4f}")
            except Exception as e:
                print(f" [X] Error al guardar: {e}")

        if opc == 'g':
            while True:
                print("\n--- GESTOR BD ---")
                print("1) Ver Tabla | 2) Borrar Registro | 3) VISOR 3D | 4) Volver")
                g_opc = input("Selecciona: ")
                if g_opc == '1':
                    df = pd.read_sql_query("SELECT m.id_medicion as ID, o.fecha_hora, m.id_grupo, m.latitud_phi as Lat, m.longitud_L as Lon FROM Mediciones m JOIN Observaciones o ON m.id_observacion = o.id_observacion", conn)
                    print("\n", df)
                elif g_opc == '2':
                    id_del = input("Introduce el ID a borrar: ")
                    conn.execute("DELETE FROM Mediciones WHERE id_medicion=?", (id_del,))
                    conn.commit()
                    print(" Registro eliminado.")
                elif g_opc == '3':
                    visor_3d_interactivo(conn)
                elif g_opc == '4':
                    break
    conn.close()

if __name__ == "__main__":
    main()