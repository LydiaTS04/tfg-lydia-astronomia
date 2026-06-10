# -*- coding: utf-8 -*-
import sqlite3
BS = chr(92)          # backslash
E  = ' ' + BS + BS    # fin de fila LaTeX  (espacio + \\)
con = sqlite3.connect('manchas_tfg.db.bak_20260524_193126_antes_de_restaurar')
cur = con.cursor()

def num(v, d=2):
    if v is None:
        return '--'
    try:
        return ('{:.' + str(d) + 'f}').format(float(v)).replace('.', ',')
    except Exception:
        return str(v)

fechas = {r[0]: r[1] for r in cur.execute('SELECT id_observacion,fecha_hora FROM Observaciones')}
L = []
L.append('% Generado desde la base de datos (no editar a mano)')
L.append(BS + r'subsection*{C.1\quad Datos de cada fotografia (observaciones)}')
L.append(BS + 'footnotesize')
L.append(BS + 'begin{longtable}{llrrrrrr}')
L.append(BS + 'toprule')
L.append('Fecha y hora & Archivo & $x_c$ & $y_c$ & $R$ & $' + BS + 'lambda_' + BS +
         'odot$ & $' + BS + 'mu$ & $' + BS + 'beta_{' + BS + 'mathrm{opt}}$' + E)
L.append(BS + 'midrule ' + BS + 'endhead')
for r in cur.execute('SELECT fecha_hora,archivo_img,centro_x,centro_y,radio_sol,'
                     'lambda_sol,mu_angulo,beta_optica FROM Observaciones ORDER BY id_observacion'):
    arch = str(r[1]).replace('_', BS + '_')
    L.append('{0} & {1}texttt{{{1}scriptsize {2}}} & {3} & {4} & {5} & {6} & {7} & {8}{9}'.format(
        r[0], BS, arch, num(r[2], 0), num(r[3], 0), num(r[4], 0),
        num(r[5]), num(r[6]), num(r[7]), E))
L.append(BS + 'bottomrule')
L.append(BS + 'end{longtable}')
L.append(BS + 'normalsize')
L.append('')
L.append(BS + r'subsection*{C.2\quad Posicion de cada mancha en cada foto (mediciones brutas)}')
L.append(BS + 'footnotesize')
L.append(BS + 'begin{longtable}{llrrrrr}')
L.append(BS + 'toprule')
L.append('Mancha & Fecha & $x_m$ & $y_m$ & $' + BS + 'rho$ & $' + BS + 'Phi$ & $L$' + E)
L.append(BS + 'midrule ' + BS + 'endhead')
rows = list(cur.execute('SELECT id_grupo,id_observacion,pixel_x,pixel_y,rho,'
                        'latitud_phi,longitud_L,excluida FROM Mediciones'))
def key(x):
    try:
        return (float(x[0]), x[1])
    except Exception:
        return (9999.0, x[1])
rows.sort(key=key)
for r in rows:
    f = fechas.get(r[1], '--').split(' ')[0]
    exc = ('$^' + BS + 'dagger$') if r[7] else ''
    L.append('M{0}{1} & {2} & {3} & {4} & {5} & {6} & {7}{8}'.format(
        r[0], exc, f, num(r[2], 0), num(r[3], 0), num(r[4], 3),
        num(r[5]), num(r[6]), E))
L.append(BS + 'bottomrule')
L.append(BS + 'end{longtable}')
L.append(BS + 'normalsize')
L.append(BS + 'noindent' + BS + 'footnotesize $^' + BS + 'dagger$ Medicion excluida del calculo.' + BS + 'normalsize')

with open('../latex/capitulos/apendiceC-tablas.tex', 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(L))
print('OK  observaciones=18  mediciones=', len(rows))
