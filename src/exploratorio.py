"""
Análisis exploratorio y de calidad de los datos (Fase 2 de CRISP-DM · OE1).

Uso (desde la carpeta del proyecto, después de limpieza.py e ica.py):
    py src\\exploratorio.py

Genera en docs/eda/:
    estadisticas_descriptivas.csv   n, % faltante, mediana, percentiles 5 y 95 por variable
    correlaciones_ica.csv           correlación de Spearman de cada variable de entrada con el ICA
    fig_eda_1_muestreos_anio.png    muestreos por año
    fig_eda_2_completitud.png       porcentaje de datos disponibles por variable
    fig_eda_3_ica_estacion.png      ICA por estación, en orden aguas abajo
    fig_eda_4_clases_periodo.png    proporción de clases por quinquenio
    fig_eda_5_correlaciones.png     correlación de las variables de entrada con el ICA
    fig_eda_6_variables_clase.png   distribución de cuatro variables por clase
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / 'datos' / 'procesados' / 'datos_con_ica.csv'
SALIDA = RAIZ / 'docs' / 'eda'

ENTRADAS = ['temperatura', 'turbiedad', 'color', 'dbo', 'nitrogeno_amoniacal', 'nitratos', 'nitritos',
            'fosforo_total', 'coliformes_fecales', 'coliformes_totales', 'cloruros', 'sulfatos',
            'alcalinidad', 'dureza_total']
ICA = ['od', 'sst', 'dqo', 'conductividad', 'ph']
NOMBRES = {
    'temperatura': 'Temperatura', 'turbiedad': 'Turbiedad', 'color': 'Color', 'dbo': 'DBO5',
    'nitrogeno_amoniacal': 'Nitrógeno amoniacal', 'nitratos': 'Nitratos', 'nitritos': 'Nitritos',
    'fosforo_total': 'Fósforo total', 'coliformes_fecales': 'Coliformes fecales',
    'coliformes_totales': 'Coliformes totales', 'cloruros': 'Cloruros', 'sulfatos': 'Sulfatos',
    'alcalinidad': 'Alcalinidad total', 'dureza_total': 'Dureza total', 'od': 'Oxígeno disuelto*',
    'sst': 'Sólidos suspendidos*', 'dqo': 'DQO*', 'conductividad': 'Conductividad*', 'ph': 'pH*'}
# Orden aproximado de las estaciones a lo largo del río (de aguas arriba hacia aguas abajo). Verificar con la CVC.
ORDEN_RIO = ['ANTES SUAREZ', 'ANTES RIO OVEJAS', 'ANTES RIO TIMBA', 'PASO DE LA BALSA', 'PASO DE LA BOLSA',
             'PUENTE HORMIGUERO', 'ANTES INTERCEPTOR SUR', 'JUANCHITO', 'PASO DEL COMERCIO', 'PUERTO ISAACS',
             'PASO DE LA TORRE', 'VIJES', 'YOTOCO', 'MEDIACANOA', 'RIOFRIO', 'PUENTE GUAYABAL', 'LA VICTORIA',
             'ANACARO', 'PUENTE LA VIRGINIA']
CERCANAS = {'ANTES SUAREZ', 'ANTES RIO OVEJAS', 'ANTES RIO TIMBA', 'PASO DE LA BALSA'}
CLASES = ['Bueno/Aceptable', 'Regular', 'Malo']
COLOR_CLASE = {'Bueno/Aceptable': '#4a7fb5', 'Regular': '#e0a33a', 'Malo': '#c0504d'}
GRIS, ACENTO = '#9a9a9a', '#2f5597'

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titlesize': 10, 'figure.dpi': 100})


def clase(ica):
    if pd.isna(ica):
        return np.nan
    return 'Malo' if ica <= 0.50 else ('Regular' if ica <= 0.70 else 'Bueno/Aceptable')


def guardar(fig, nombre):
    fig.savefig(SALIDA / nombre, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(DATOS)
    d['clase'] = d['ica'].map(clase)
    c = d.dropna(subset=['ica'])

    # --- Tablas ---
    variables = ENTRADAS + ICA
    est = pd.DataFrame({
        'variable': variables,
        'registros': [int(d[v].notna().sum()) for v in variables],
        'faltante_pct': [round(d[v].isna().mean() * 100, 1) for v in variables],
        'mediana': [d[v].median() for v in variables],
        'p5': [d[v].quantile(.05) for v in variables],
        'p95': [d[v].quantile(.95) for v in variables],
        'uso': ['entrada del modelo'] * len(ENTRADAS) + ['cálculo del ICA'] * len(ICA)})
    est.to_csv(SALIDA / 'estadisticas_descriptivas.csv', index=False)
    corr = c[ENTRADAS + ['ica']].corr(method='spearman')['ica'].drop('ica').sort_values()
    corr.rename('spearman_con_ica').to_csv(SALIDA / 'correlaciones_ica.csv')

    # --- Figura 1: muestreos por año ---
    por_anio = d.groupby('anio').size()
    fig, ax = plt.subplots(figsize=(8, 3))
    colores = [GRIS if a <= 2015 else ACENTO for a in por_anio.index]
    ax.bar(por_anio.index, por_anio.values, color=colores, width=0.8)
    ax.set_xlabel('Año'); ax.set_ylabel('Muestreos')
    ax.text(2002.5, por_anio.max() + 4, 'Entrenamiento 1990–2015', ha='center', color='#555555')
    ax.text(2020.5, por_anio.max() + 4, 'Prueba 2016–2025', ha='center', color=ACENTO)
    ax.set_ylim(0, por_anio.max() + 14)
    guardar(fig, 'fig_eda_1_muestreos_anio.png')

    # --- Figura 2: completitud por variable ---
    disp = (100 - est.set_index('variable')['faltante_pct']).sort_values()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([NOMBRES[v] for v in disp.index], disp.values,
            color=[GRIS if v in ICA else ACENTO for v in disp.index])
    for i, val in enumerate(disp.values):
        ax.text(val + 0.5, i, f'{val:.1f} %', va='center', fontsize=8)
    ax.set_xlim(0, 108); ax.set_xlabel('Registros con dato (%)')
    guardar(fig, 'fig_eda_2_completitud.png')

    # --- Figura 3: ICA por estación (aguas abajo) ---
    orden = [e for e in ORDEN_RIO if e in set(c['estacion'])]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bp = ax.boxplot([c.loc[c.estacion == e, 'ica'] for e in orden], patch_artist=True,
                    showfliers=False, widths=0.6, medianprops={'color': 'black'})
    for caja, e in zip(bp['boxes'], orden):
        caja.set_facecolor(ACENTO if e in CERCANAS else '#d9d9d9'); caja.set_alpha(0.8)
    ax.axhline(0.70, color='#e0a33a', lw=0.9, ls='--'); ax.axhline(0.50, color='#c0504d', lw=0.9, ls='--')
    ax.text(len(orden) + 0.6, 0.70, 'Regular', va='center', fontsize=8, color='#a8741c')
    ax.text(len(orden) + 0.6, 0.50, 'Malo', va='center', fontsize=8, color='#c0504d')
    ax.set_xticks(range(1, len(orden) + 1))
    nombre = lambda e: e.title().replace(' De La ', ' de la ').replace(' Del ', ' del ').replace('Riofrio', 'Riofrío').replace('Rio ', 'Río ').replace('Suarez', 'Suárez')
    ax.set_xticklabels([nombre(e) for e in orden], rotation=60, ha='right', fontsize=8)
    ax.set_ylabel('ICA'); ax.set_xlabel('Estación (de aguas arriba hacia aguas abajo)')
    guardar(fig, 'fig_eda_3_ica_estacion.png')

    # --- Figura 4: clases por quinquenio ---
    q = (c.assign(periodo=np.minimum((c.anio // 5) * 5, 2020))   # 2025 se une a 2020–2025
          .groupby('periodo')['clase'].value_counts(normalize=True).unstack().reindex(columns=CLASES).fillna(0))
    fig, ax = plt.subplots(figsize=(8, 3.2))
    base = np.zeros(len(q))
    etiquetas = [f'{p}–{str(p + 4)[2:]}' if p < 2020 else '2020–25' for p in q.index]
    for k in CLASES:
        ax.bar(etiquetas, q[k] * 100, bottom=base, color=COLOR_CLASE[k], label=k, width=0.7)
        base += q[k].values * 100
    ax.set_ylabel('Muestreos (%)'); ax.set_ylim(0, 100)
    ax.legend(ncol=3, frameon=False, loc='upper center', bbox_to_anchor=(0.5, 1.15))
    guardar(fig, 'fig_eda_4_clases_periodo.png')

    # --- Figura 5: correlaciones con el ICA ---
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.barh([NOMBRES[v] for v in corr.index], corr.values,
            color=[ACENTO if abs(x) >= 0.4 else GRIS for x in corr.values])
    for i, val in enumerate(corr.values):
        ax.text(val - 0.01, i, f'{val:.2f}'.replace('.', ','), va='center', ha='right', fontsize=8)
    ax.axvline(0, color='black', lw=0.8); ax.set_xlim(-0.7, 0.05)
    ax.set_xlabel('Correlación de Spearman con el ICA')
    guardar(fig, 'fig_eda_5_correlaciones.png')

    # --- Figura 6: variables por clase ---
    vars6 = [('alcalinidad', 'Alcalinidad total (mg CaCO3/L)', False), ('turbiedad', 'Turbiedad (UNT)', True),
             ('dbo', 'DBO5 (mg O2/L)', False), ('coliformes_fecales', 'Coliformes fecales (NMP/100 mL)', True)]
    fig, ejes = plt.subplots(1, 4, figsize=(10, 3.3))
    for ax, (v, titulo, log) in zip(ejes, vars6):
        grupos = [c.loc[c.clase == k, v].dropna() for k in CLASES]
        bp = ax.boxplot(grupos, patch_artist=True, showfliers=False, widths=0.6, medianprops={'color': 'black'})
        for caja, k in zip(bp['boxes'], CLASES):
            caja.set_facecolor(COLOR_CLASE[k]); caja.set_alpha(0.8)
        if log:
            ax.set_yscale('log')
        ax.set_title(titulo, fontsize=9)
        ax.set_xticks([1, 2, 3]); ax.set_xticklabels(['Bueno/\nAcept.', 'Regular', 'Malo'], fontsize=8)
    fig.tight_layout()
    guardar(fig, 'fig_eda_6_variables_clase.png')

    print(f'Registros: {len(d)} | con ICA: {len(c)} | estaciones: {d.estacion.nunique()}')
    print('Variables con más faltantes:', est.sort_values('faltante_pct', ascending=False).head(3)[['variable', 'faltante_pct']].values.tolist())
    print('Correlación más fuerte con el ICA:', corr.index[0], round(corr.iloc[0], 2))
    print(f'Archivos en {SALIDA}')


if __name__ == '__main__':
    main()
