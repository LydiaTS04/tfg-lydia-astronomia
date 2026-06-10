# -*- coding: utf-8 -*-
"""
modo_i_explicacion_COMPLETO.pdf  (fuente ARIAL -> griego se ve bien).
Estructurado alrededor de la idea CLAVE:
  - La LATITUD Phi por ESTADISTICA DESCRIPTIVA (media +- desv. tipica), porque
    hay VARIAS medidas por mancha.
  - El PERIODO T por PROPAGACION ANALITICA, porque es un UNICO valor por mancha.
Ajuste NO PONDERADO. Coincide con el codigo.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

WIN = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('Ar',  os.path.join(WIN, 'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArB', os.path.join(WIN, 'arialbd.ttf')))
pdfmetrics.registerFont(TTFont('ArI', os.path.join(WIN, 'ariali.ttf')))
pdfmetrics.registerFontFamily('Ar', normal='Ar', bold='ArB', italic='ArI')

COL_T=HexColor('#1a237e'); COL_H1=HexColor('#0d47a1'); COL_H2=HexColor('#1565c0')
COL_H3=HexColor('#2e7d32')
FORM_BG=HexColor('#fff8e1'); FORM_BR=HexColor('#f57f17')
BOX_BG=HexColor('#e3f2fd');  BOX_BR=HexColor('#1976d2')
OK_BG=HexColor('#e8f5e9');   OK_BR=HexColor('#2e7d32')
KEY_BG=HexColor('#ede7f6');  KEY_BR=HexColor('#5e35b1')

st_tit=ParagraphStyle('T',fontName='ArB',fontSize=24,textColor=COL_T,alignment=TA_CENTER,spaceAfter=10)
st_sub=ParagraphStyle('S',fontName='Ar',fontSize=13,textColor=COL_H2,alignment=TA_CENTER,spaceAfter=18)
st_part=ParagraphStyle('P',fontName='ArB',fontSize=19,textColor=HexColor('#5e35b1'),alignment=TA_CENTER,spaceBefore=10,spaceAfter=12)
st_h1=ParagraphStyle('H1',fontName='ArB',fontSize=17,textColor=COL_H1,spaceBefore=16,spaceAfter=9)
st_h2=ParagraphStyle('H2',fontName='ArB',fontSize=13.5,textColor=COL_H2,spaceBefore=12,spaceAfter=7)
st_n=ParagraphStyle('N',fontName='Ar',fontSize=10.5,leading=14,alignment=TA_JUSTIFY,spaceAfter=6)
st_f=ParagraphStyle('F',fontName='Ar',fontSize=11.5,leading=17,alignment=TA_CENTER,spaceAfter=6,textColor=HexColor('#5d4037'))

def _caja(h,bg,br,st=st_f,anch=16*cm):
    t=Table([[Paragraph(h,st)]],colWidths=[anch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg),('BOX',(0,0),(-1,-1),1.3,br),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12)]))
    return t
def form(h): return _caja(h,FORM_BG,FORM_BR)
def info(h): return _caja(h,BOX_BG,BOX_BR,st=st_n)
def exito(h):return _caja(h,OK_BG,OK_BR,st=st_n)
def clave(h):return _caja(h,KEY_BG,KEY_BR,st=st_n)

RUTA=r'C:\Users\lydia\Downloads\tfg\documentos explicacion\modo_i_explicacion_COMPLETO.pdf'
doc=SimpleDocTemplate(RUTA,pagesize=A4,leftMargin=2.2*cm,rightMargin=2.2*cm,
    topMargin=2*cm,bottomMargin=2*cm,title='Modo I COMPLETO')
S=[]

# ===== PORTADA =====
S+=[Spacer(1,3*cm), Paragraph('MODO I',st_tit),
 Paragraph('Rotación diferencial solar',st_tit), Spacer(1,0.3*cm),
 Paragraph('Explicación completa — ecuaciones y errores',st_sub), Spacer(1,0.7*cm),
 clave('<b>IDEA CLAVE de los errores (dos magnitudes, dos métodos):</b><br/><br/>'
   '&bull; La <b>latitud Φ</b> se trata por <b>ESTADÍSTICA DESCRIPTIVA</b> '
   '(media ± desviación típica), porque de una misma mancha hay VARIAS medidas '
   'de Φ.<br/>'
   '&bull; El <b>periodo T</b> se trata por <b>PROPAGACIÓN ANALÍTICA</b> '
   '(derivadas parciales), porque es un ÚNICO valor por mancha.'),
 Spacer(1,0.4*cm),
 exito('<b>Resultado con tu base de datos:</b> A = +14,10 ± 0,28 °/día, '
   'B = −2,21 ± 2,47 °/día (27 manchas). Compatible con Faye (A=14,37, B=−2,30). '
   'Ajuste NO ponderado.'),
 PageBreak()]

# ===== 1. LEY =====
S+=[Paragraph('1. La ley de Carrington–Faye',st_h1),
 Paragraph('El Sol no gira como un sólido: su ecuador rota más rápido que los '
   'polos. La ley empírica que lo describe es:',st_n),
 form('<b>ω(Φ) = A + B · sin²(Φ)</b>'),
 Paragraph('ω = velocidad angular sidérea (°/día), Φ = latitud heliográfica, '
   'A = velocidad ecuatorial, B (negativo) = frenado hacia los polos. El Modo I '
   'mide A y B siguiendo manchas propias.',st_n)]

# ===== 2. CADENA GEOMETRICA =====
S+=[Paragraph('2. De píxel a coordenadas heliográficas',st_h1),
 Paragraph('Cada mancha medida en píxeles (x, y) recorre esta cadena:',st_n),
 form('(x, y) → (dx, dy) → (r, θ_m) → (ρ, A) → (φ_M, λ_M) → (Φ, L)'),
 form('dx = x − x_c ; dy = −(y − y_c) ; r = √(dx² + dy²) ; ρ = r / R_sol<br/>'
   'θ_m = atan2(dy, dx) ; A = θ_m + μ + β<br/>'
   'φ_M = arcsin(ρ·sin A) ; λ_M = arcsin(ρ·cos A / cos φ_M)<br/>'
   'Φ = arcsin(sinΦ_0·sinφ_M + cosΦ_0·cosφ_M·cosL_aux)<br/>'
   'L = 180° − atan2(cosφ_M·sinL_aux/cosΦ, (sinφ_M−sinΦ_0·sinΦ)/(cosΦ_0·cosΦ))'),
 Paragraph('con Φ_0 = 82°44′53,56″ y λ_N = −13°52′21,41″, y '
   'L_aux = (λ_sol+180°) + λ_M − λ_N. A partir de aquí se calculan los errores, '
   'distintos para Φ y para T.',st_n),
 PageBreak()]

# ====================================================================
# PARTE I — LATITUD Phi (ESTADISTICA DESCRIPTIVA)
# ====================================================================
S+=[Paragraph('PARTE I',st_part),
 Paragraph('Error en la latitud Φ: estadística descriptiva',st_h1),
 Paragraph('3. Por qué estadística y no propagación',st_h2),
 Paragraph('Una mancha solar gira con el Sol manteniendo su latitud Φ '
   'prácticamente constante. Si la seguimos durante N días, obtenemos N medidas '
   'de la MISMA cantidad física. Cuando se tienen varias medidas de lo mismo, lo '
   'correcto no es propagar errores variable a variable, sino hacer '
   '<b>estadística descriptiva</b>: la media como mejor estimación y la '
   'desviación típica como su incertidumbre. Esa dispersión observada ya recoge '
   'todas las fuentes de error juntas (ruido de píxel, proyección, centrado, '
   'pequeñas no linealidades).',st_n),
 Paragraph('4. Media aritmética',st_h2),
 form('<b>Φ_med = (1/N) · Σ Φ_i</b>'),
 Paragraph('5. Desviación típica muestral',st_h2),
 form('<b>S_Φ = √( (1/(N−1)) · Σ (Φ_i − Φ_med)² )</b>'),
 Paragraph('Se usa el denominador N−1 (estimador insesgado de Bessel) y no N, '
   'porque la propia media Φ_med se calcula a partir de los datos, lo que consume '
   'un grado de libertad.',st_n),
 Paragraph('6. Resultado',st_h2),
 form('<b>Φ = Φ_med ± S_Φ</b>'),
 Paragraph('Φ_med va al eje de la gráfica Φ–T y S_Φ es la semianchura de la barra '
   'de error vertical.',st_n),
 info('<b>Salvaguarda:</b> el código compara S_Φ con la propagación analítica de '
   'la incertidumbre de píxel (5 px) y se queda con la mayor, '
   'σ_Φ = max(S_Φ muestral, S_Φ propagación), por si las observaciones fueran '
   'demasiado consistentes. Pero el método de fondo para Φ es la estadística '
   'descriptiva.'),
 PageBreak()]

# ====================================================================
# PARTE II — PERIODO T (PROPAGACION ANALITICA)
# ====================================================================
S+=[Paragraph('PARTE II',st_part),
 Paragraph('Error en el periodo T: propagación analítica',st_h1),
 Paragraph('7. Por qué propagación y no estadística',st_h2),
 Paragraph('El periodo T no es una cantidad que se mida varias veces: para cada '
   'mancha se obtiene UN ÚNICO valor, a partir del desplazamiento de longitud ΔL '
   'entre el primer y el último día. No hay una muestra de T que promediar, así '
   'que su incertidumbre se obtiene <b>propagando</b> el error de medida del '
   'píxel a través de toda la cadena geométrica, con derivadas parciales.',st_n),
 Paragraph('8. Punto de partida e idea de propagación',st_h2),
 Paragraph('Lo único que se mide a mano es el píxel, con δ = 5 px en cada eje. '
   'Todo lo demás (R, μ, β, λ_sol…) se considera exacto. La regla general '
   '(cuadratura, errores independientes):',st_n),
 form('<b>σ_f² = (∂f/∂x)²·σ_x² + (∂f/∂y)²·σ_y²</b> &nbsp;(σ_x = σ_y = δ = 5 px)')]

S+=[Paragraph('9. Cadena de derivadas parciales',st_h2),
 Paragraph('(a) Error en r:',st_n),
 form('∂r/∂dx = dx/r ; ∂r/∂dy = dy/r → σ_r² = δ²(dx²+dy²)/r² = δ² → '
   '<b>σ_r = δ = 5 px</b>'),
 Paragraph('(b) Error en ρ = r/R_sol:',st_n),
 form('<b>σ_ρ = δ / R_sol</b>'),
 Paragraph('(c) Error en θ_m = atan2(dy, dx):',st_n),
 form('∂θ_m/∂dx = −dy/r² ; ∂θ_m/∂dy = dx/r² → σ_θm² = δ²/r² → '
   '<b>σ_θm = δ / r</b>'),
 Paragraph('(d) Error en φ_M = arcsin(ρ·sin A), con A = θ_m + μ + β:',st_n),
 form('∂φ_M/∂ρ = sin A / √(1−ρ²sin²A) ; ∂φ_M/∂θ_m = ρ·cos A / √(1−ρ²sin²A)<br/>'
   '<b>σ_φM² = [ (sin A)²·σ_ρ² + (ρ·cos A)²·σ_θm² ] / (1 − ρ²sin²A)</b>')]

S+=[PageBreak(),
 Paragraph('(e) Error en λ_M = arcsin(ρ·cos A / cos φ_M) — la más larga. '
   'Sea v = ρ·cos A / cos φ_M:',st_n),
 form('∂v/∂ρ = cos A / cos φ_M ; ∂v/∂A = −ρ·sin A / cos φ_M<br/>'
   '∂v/∂φ_M = ρ·cos A·sin φ_M / cos²φ_M ; ∂λ_M/∂v = 1/√(1−v²)'),
 form('<b>σ_λM² = [ 1/(1−v²) ] · {</b><br/>'
   '(cos A/cos φ_M)²·σ_ρ² + (ρ·sin A/cos φ_M)²·σ_θm²<br/>'
   '+ (ρ·cos A·sin φ_M/cos²φ_M)²·σ_φM² <b>}</b>'),
 Paragraph('(f) Error en la longitud Λ: como Λ = λ_T + λ_M − λ_N y los extremos '
   'son constantes,',st_n),
 form('<b>σ_Λ = σ_λM</b>'),
 Paragraph('Toda la incertidumbre del píxel se concentra en σ_Λ, que es la que '
   'arrastra el error del periodo.',st_n)]

S+=[Paragraph('10. De σ_Λ al periodo T',st_h2),
 Paragraph('Para una mancha con N observaciones, los extremos i=1 e i=N dan la '
   'pendiente. Como Δt es exacto, todo el error de ω y T viene de ΔL:',st_n),
 form('ω = ΔL/Δt ; T = 360/ω'),
 Paragraph('10.1. Método 1 puro (N = 2):',st_h2),
 form('σ_ΔL = √( σ_Λ1² + σ_Λ2² )<br/>'
   '<b>σ_T = T · σ_ΔL / |ΔL|</b> ; σ_ω = ω · σ_ΔL / |ΔL|'),
 Paragraph('10.2. Método 1 mejorado (N ≥ 3):',st_h2),
 Paragraph('Se traza la recta por los extremos y se miden los residuos de los '
   'puntos intermedios:',st_n),
 form('r_i = L_i − (L_1 + ω_ext·(t_i − t_1)) ; S_L = √( Σ r_i² / (N−2) )<br/>'
   '<b>σ_T = T · √2 · S_L / |ΔL|</b>'),
 Paragraph('Demostración de σ_T = T·σ_ΔL/|ΔL|: como T = 360/ω, ∂T/∂ω = −T/ω, '
   'luego σ_T = (T/ω)·σ_ω = T·σ_ΔL/|ΔL|.',st_n),
 PageBreak()]

# ===== AJUSTE =====
S+=[Paragraph('11. Ajuste por mínimos cuadrados NO ponderado',st_h1),
 Paragraph('Con cada (Φ_med, ω) y su error, se ajusta la ley de Faye. Cambio de '
   'variable: x_i = sin²(Φ_i), y_i = ω_i, modelo y = A + B·x. Todos los puntos '
   'pesan igual:',st_n),
 form('Δ = N·S_xx − S_x²<br/>'
   '<b>A = (S_xx·S_y − S_x·S_xy)/Δ</b> ; <b>B = (N·S_xy − S_x·S_y)/Δ</b><br/>'
   's² = Σ(y_i − A − B·x_i)²/(N−2)<br/>'
   '<b>σ_A = √(s²·S_xx/Δ)</b> ; <b>σ_B = √(s²·N/Δ)</b>'),
 Paragraph('11.1. Por qué NO ponderado',st_h2),
 info('El ponderado (pesos 1/σ_ω²) daba peso enorme a las manchas con N grande '
   '(σ_ω ≈ 0), que dominaban el ajuste y daban B con signo erróneo (+2,10). El no '
   'ponderado es robusto: cada mancha aporta lo mismo y reproduce Faye '
   '(A=14,10 a 1σ; B=−2,21 clavado a −2,30).'),
 Paragraph('11.2. Exclusiones',st_h2),
 Paragraph('Se excluyen solo las manchas con T fuera del rango físico [22, 32] d '
   '(rotación imposible): M8, M21, M22. Se pintan como rombos pero no entran en '
   'A, B. Sin filtros «a posteriori».',st_n)]

# ===== RESUMEN =====
S+=[Paragraph('12. Resumen',st_h1),
 clave('<b>Φ (latitud)</b> → estadística descriptiva: Φ_med ± S_Φ (denominador '
   'N−1). Porque hay VARIAS medidas por mancha.<br/><br/>'
   '<b>T (periodo)</b> → propagación analítica: 5 px → σ_r, σ_ρ, σ_θm → σ_φM, '
   'σ_λM → σ_Λ → σ_T (método 1). Porque es UN ÚNICO valor por mancha.<br/><br/>'
   '<b>A, B</b> → mínimos cuadrados NO ponderado, con la varianza de los residuos '
   'del ajuste.')]

doc.build(S)
print('PDF generado:', RUTA)
print('Tamano:', os.path.getsize(RUTA), 'bytes')
