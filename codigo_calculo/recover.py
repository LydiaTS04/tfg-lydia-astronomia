import sqlite3

conn = sqlite3.connect('manchas_tfg.db')
cursor = conn.cursor()

cursor.execute("SELECT id_observacion FROM Observaciones WHERE archivo_img = 'lunes_13-4-26-11_15'")
row1 = cursor.fetchone()
if row1:
    id_obs1 = row1[0]
    cursor.execute('''INSERT OR IGNORE INTO Mediciones 
        (id_observacion, id_grupo, pixel_x, pixel_y, rho, latitud_phi, longitud_L, mu_angulo, beta_optica) 
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (id_obs1, '1', 285.0, 358.0, 0.343053, -21.3119697222222, 204.338847222222, -22.3374583333333, 20.5544444444444))

cursor.execute("SELECT id_observacion FROM Observaciones WHERE archivo_img = 'martes_14-4-26_11_18'")
row2 = cursor.fetchone()
if row2:
    id_obs2 = row2[0]
    cursor.execute('''INSERT OR IGNORE INTO Mediciones 
        (id_observacion, id_grupo, pixel_x, pixel_y, rho, latitud_phi, longitud_L, mu_angulo, beta_optica) 
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (id_obs2, '1', 537.0, 715.0, 0.252747, -10.1411755555556, 204.337738888889, -22.3488027777778, 17.9852222222222))

conn.commit()
conn.close()
print('Recovered lost data successfully!')
