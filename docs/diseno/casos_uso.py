# Diagrama de casos de uso. Ejecutar desde la carpeta del proyecto: py docs\diseno\casos_uso.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch
plt.rcParams['font.family'] = 'Liberation Sans'
fig, ax = plt.subplots(figsize=(11, 7.6)); ax.set_xlim(0, 110); ax.set_ylim(0, 76); ax.axis('off')
ax.add_patch(Rectangle((20, 2), 66, 71, fill=False, lw=1.3))
ax.text(53, 70.5, 'Sistema de clasificación de la calidad del agua', ha='center', fontsize=11, weight='bold')

def actor(x, y, nombre):
    ax.add_patch(plt.Circle((x, y + 5.2), 1.4, fill=False, lw=1.3))
    ax.plot([x, x], [y + 3.8, y], 'k', lw=1.3); ax.plot([x - 2.6, x + 2.6], [y + 2.6, y + 2.6], 'k', lw=1.3)
    ax.plot([x, x - 2.2], [y, y - 3.2], 'k', lw=1.3); ax.plot([x, x + 2.2], [y, y - 3.2], 'k', lw=1.3)
    ax.text(x, y - 5, nombre, ha='center', va='top', fontsize=9.5)
    return (x, y + 2)

CU = {}
def cu(c, x, y, t, pend=False, w=24):
    ax.add_patch(Ellipse((x, y), w, 6.4, fill=True, fc='#f2f2f2' if pend else '#e8eef7',
                         ec='#888888' if pend else '#2f5597', lw=1.2, ls='--' if pend else '-'))
    ax.text(x, y, f'{c}\n{t}', ha='center', va='center', fontsize=8.6, color='#666666' if pend else 'black')
    CU[c] = (x, y, w)

cu('CU-01', 40, 61, 'Clasificar una muestra')
cu('CU-02', 70, 64, 'Validar los datos')
cu('CU-03', 70, 54.5, 'Registrar la predicción')
cu('CU-04', 40, 50.5, 'Cargar un muestreo real')
cu('CU-05', 40, 40.5, 'Consultar modelo y métricas')
cu('CU-06', 40, 30.5, 'Consultar histórico por estación')
cu('CU-07', 67, 40, 'Cargar y depurar\ndatos de la CVC')
cu('CU-08', 66, 30, 'Calcular el ICA')
cu('CU-09', 66, 20, 'Entrenar y comparar modelos')
cu('CU-10', 53, 9, 'Reentrenar desde la interfaz\n(pendiente, C10)', pend=True, w=27)

tec = actor(9, 46, 'Técnico de\nmonitoreo ambiental')
adm = actor(100, 32, 'Administrador\ndel modelo')
cvc = actor(100, 58, 'CVC\n(fuente de datos)')

def linea(a, c, ls='-', col='black'):
    x, y, w = CU[c]
    ex = x - w / 2 if a[0] < x else x + w / 2
    ax.plot([a[0] + (2.8 if a[0] < x else -2.8), ex], [a[1], y], color=col, lw=0.9, ls=ls)

for c in ('CU-01', 'CU-04', 'CU-05', 'CU-06'):
    linea(tec, c)
for c in ('CU-07', 'CU-08', 'CU-09'):
    linea(adm, c)
linea(adm, 'CU-10', ls='--', col='#888888')
linea(cvc, 'CU-07')

def incluye(a, b, texto='«include»'):
    x1, y1, w1 = CU[a]; x2, y2, w2 = CU[b]
    ax.add_patch(FancyArrowPatch((x1 + w1 / 2, y1), (x2 - w2 / 2, y2), arrowstyle='->', mutation_scale=11,
                                 ls='--', lw=0.9, color='#333333'))
    ax.text((x1 + w1 / 2 + x2 - w2 / 2) / 2 - 1.5, (y1 + y2) / 2 + (2.0 if y2 > y1 else -2.6), texto, ha='center', fontsize=7.8, color='#333333')
incluye('CU-01', 'CU-02'); incluye('CU-01', 'CU-03')
ax.add_patch(FancyArrowPatch((40, 53.7), (40, 57.8), arrowstyle='->', mutation_scale=11, ls='--', lw=0.9, color='#333333'))
ax.text(41, 55.6, '«extend»', fontsize=7.8, color='#333333')
fig.savefig('docs/diseno/Figura_casos_uso.png', dpi=200, bbox_inches='tight', facecolor='white')
