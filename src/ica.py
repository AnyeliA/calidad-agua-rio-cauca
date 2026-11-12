"""
Cálculo del ICA (IDEAM) en su versión de 5 variables y asignación de la categoría.
Requisito que cubre: RF-03.

IMPORTANTE: verifique cada fórmula y cada rango contra la Hoja Metodológica del
Índice de Calidad del Agua del IDEAM que cita en su documento. Si algún coeficiente
difiere, corrija aquí y registre el cambio en la bitácora.

Uso:
    python src/ica.py datos/procesados/datos_limpios.csv datos/procesados/datos_con_ica.csv
"""
import sys

import numpy as np
import pandas as pd

ALTITUD_M = 950  # altitud media aproximada del tramo vallecaucano; mejor usar la de cada estación


def od_saturacion(temp_c, altitud_m=ALTITUD_M):
    """Concentración de saturación de O2 (mg/L), APHA 4500-O, corregida por presión."""
    t = temp_c + 273.15
    ln_cs = (-139.34411 + 1.575701e5 / t - 6.642308e7 / t**2
             + 1.243800e10 / t**3 - 8.621949e11 / t**4)
    presion_atm = (1 - 2.25577e-5 * altitud_m) ** 5.25588
    return np.exp(ln_cs) * presion_atm


def i_od(pct):
    return np.where(pct <= 100, 1 - (1 - 0.01 * pct), 1 - (0.01 * pct - 1)).clip(0, 1)


def i_sst(sst):
    v = 1 - (-0.02 + 0.003 * sst)
    v = np.where(sst <= 4.5, 1, v)
    v = np.where(sst >= 320, 0, v)
    return np.clip(v, 0, 1)


def i_dqo(dqo):
    return np.select([dqo <= 20, dqo <= 25, dqo <= 40, dqo <= 80], [0.91, 0.71, 0.51, 0.26], 0.125)


def i_ce(ce):
    return np.clip(1 - 10 ** (-3.26 + 1.34 * np.log10(ce)), 0, 1)


def i_ph(ph):
    return np.select(
        [ph < 4, ph <= 7, ph <= 8, ph <= 11],
        [0.1, 0.02628419 * np.exp(ph * 0.520025), 1, np.exp((ph - 8) * -0.5187742)],
        0.1,
    )


CATEGORIAS = [(0.25, "Muy malo"), (0.50, "Malo"), (0.70, "Regular"), (0.90, "Aceptable"), (1.00, "Bueno")]


def categoria(ica):
    if pd.isna(ica):
        return np.nan
    for limite, nombre in CATEGORIAS:
        if ica <= limite:
            return nombre
    return "Bueno"


def calcular_ica(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Temperatura faltante: solo para calcular la saturación, se usa la mediana de la estación y mes.
    temp = df["temperatura"].fillna(df.groupby(["estacion", "mes"])["temperatura"].transform("median"))
    temp = temp.fillna(df["temperatura"].median())
    df["od_pct_sat"] = 100 * df["od"] / od_saturacion(temp)
    sub = pd.DataFrame({
        "i_od": i_od(df["od_pct_sat"]), "i_sst": i_sst(df["sst"]), "i_dqo": i_dqo(df["dqo"]),
        "i_ce": i_ce(df["conductividad"]), "i_ph": i_ph(df["ph"]),
    }, index=df.index)
    completos = df[["od", "sst", "dqo", "conductividad", "ph"]].notna().all(axis=1)
    df[sub.columns] = sub.where(completos)
    df["ica"] = (sub.mean(axis=1)).where(completos).round(3)   # pesos iguales: 0,2 cada uno
    df["categoria_ica"] = df["ica"].map(categoria)
    return df


if __name__ == "__main__":
    entrada, salida = sys.argv[1], sys.argv[2]
    df = calcular_ica(pd.read_csv(entrada, parse_dates=["fecha"]))
    df.to_csv(salida, index=False)
    print(f"Registros con ICA calculable: {df['ica'].notna().sum()} de {len(df)}")
    print(df["categoria_ica"].value_counts(dropna=False).to_string())
