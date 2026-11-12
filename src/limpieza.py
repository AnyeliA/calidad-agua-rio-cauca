"""
Módulo de depuración de datos CVC - Calidad del agua del río Cauca.
Requisitos que cubre: RF-01 (carga y depuración con reporte), RNF-03 (integridad).

Uso:
    python src/limpieza.py datos/crudos/Calidad_del_agua_del_Rio_Cauca.csv datos/procesados

Salidas:
    datos_limpios.csv        -> un registro por muestreo, valores numéricos
    banderas_censura.csv     -> qué celdas venían como "<x" (bajo límite de detección) o ">x"
    reporte_limpieza.csv     -> cada corrección o descarte, con su causa (trazabilidad)
"""
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Reglas de negocio (documentarlas en el Método y en el diccionario de datos)
# ---------------------------------------------------------------------------
NOMBRES_CORTOS = {
    "FECHA DE MUESTREO": "fecha_raw", "ESTACIONES": "estacion", "pH": "ph",
    "TEMPERATURA (°C)": "temperatura", "COLOR (UPC)": "color", "TURBIEDAD (UNT)": "turbiedad",
    "SOLIDOS TOTALES (mg SST/l)": "solidos_totales",
    "SOLIDOS SUSPENDIDOS TOTALES (mg SS/l)": "sst",
    "SOLIDOS DISUELTOS (mg SD/l)": "solidos_disueltos",
    "DEMANDA BIOQUIMICA DE OXIGENO (mg O2/l)": "dbo",
    "DEMANDA QUIMICA DE OXIGENO (mg O2/l)": "dqo",
    "OXIGENO DISUELTO (mg O2/l)": "od",
    "DUREZA TOTAL (mg CaCO3/l)": "dureza_total", "DUREZA CALCICA (mg CaCO3/l)": "dureza_calcica",
    "DUREZA MAGNESICA (mg CaCO3/l)": "dureza_magnesica", "CALCIO (mg Ca/l)": "calcio",
    "MAGNESIO (mg Mg/l)": "magnesio", "ALCALINIDAD TOTAL (mg CaCO3/l)": "alcalinidad",
    "BICARBONATOS (mg CaCO3/l)": "bicarbonatos",
    "CONDUCTIVIDAD ELÉCTRICA (µS/cm)": "conductividad",
    "HIERRO TOTAL (mg Fe/l)": "hierro_total", "MANGANESO TOTAL (mg Mn/l)": "manganeso_total",
    "SODIO TOTAL (mg Na/l)": "sodio_total", "POTASIO TOTAL (mg K/l)": "potasio_total",
    "COBRE TOTAL (mg Cu/l)": "cobre_total", "ZINC TOTAL (mg Zn/l)": "zinc_total",
    "NITROGENO TOTAL (mg N/l)": "nitrogeno_total",
    "NITROGENO AMONIACAL (mg N-NH3/l)": "nitrogeno_amoniacal",
    "NITRITOS (mg N-NO2/l)": "nitritos", "NITRATOS (mg N-NO3/l)": "nitratos",
    "CLORUROS (mg Cl/l)": "cloruros", "FOSFORO TOTAL (mg P/l)": "fosforo_total",
    "FOSFATOS (mg PO4/l)": "fosfatos", "SULFATOS (mg SO4/l)": "sulfatos",
    "CADMIO TOTAL (mg Cd/l)": "cadmio_total", "CROMO TOTAL (mg Cr/l)": "cromo_total",
    "NIQUEL TOTAL (mg Ni/l)": "niquel_total", "PLOMO TOTAL (mg Pb/l)": "plomo_total",
    "COLIFORMES TOTALES (NMP/100 ml)": "coliformes_totales",
    "COLIFORMES FECALES (NMP/100 ml)": "coliformes_fecales", "CAUDAL (m3/s)": "caudal",
}

# Rangos plausibles para agua superficial de río (ajustar y justificar con la directora).
RANGOS = {
    "ph": (4.0, 10.0), "temperatura": (15.0, 35.0), "od": (0.0, 15.0),
    "conductividad": (10.0, 2000.0), "sst": (0.0, 10000.0), "dqo": (0.0, 1000.0),
    "dbo": (0.0, 500.0), "turbiedad": (0.0, 5000.0),
}

# Corrección de nombres de estación (espacios dobles y variantes).
ESTACIONES = {
    "ANTES INTERCEPTOR": "ANTES INTERCEPTOR SUR",
    "VIJES LA TORRE": "VIJES",  # <- verificar con la CVC antes de unificar
}

FACTOR_LD = 0.5  # valor "<LD" se reemplaza por LD * 0.5 (convención usual; documentarla)


# ---------------------------------------------------------------------------
# 2. Lectura: el archivo trae cada fila envuelta en comillas dobles
# ---------------------------------------------------------------------------
def leer_cvc(ruta: Path) -> pd.DataFrame:
    filas = []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for linea in f.read().splitlines():
            r = next(csv.reader([linea]))
            if len(r) == 1:              # fila envuelta: se vuelve a separar
                r = next(csv.reader([r[0]]))
            filas.append(r)
    cab, datos = filas[0], filas[1:]
    datos = [r + [""] * (len(cab) - len(r)) for r in datos]
    return pd.DataFrame(datos, columns=cab).replace("", np.nan)


# ---------------------------------------------------------------------------
# 3. Conversión de una celda de texto a número + bandera
# ---------------------------------------------------------------------------
NULOS = {"N.D", "N.D.", "ND", "*", "---", "´", "-", "S.D"}


def convertir(valor):
    """Devuelve (numero, bandera). bandera: '' normal, '<' bajo LD, '>' sobre rango, 'nulo'."""
    if pd.isna(valor):
        return np.nan, ""
    s = str(valor).strip().replace(" ", "")
    if s in NULOS:
        return np.nan, "nulo"
    bandera = ""
    if s.startswith("*"):            # asterisco de observación del laboratorio
        s = s[1:]
    if s[:1] in "<>":
        bandera, s = s[0], s[1:]
    s = s.replace(",", ".").replace("..", ".")
    s = re.sub(r"[a-zA-Z]+$", "", s) if not re.search(r"E[+-]?\d", s) else s  # '55g' -> 55
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\*10E([+-]?\d+)", s)   # '2.4*10E4' = 2.4 x 10^4
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2)), bandera
    try:
        return float(s), bandera
    except ValueError:
        return np.nan, "no_convertible"


# ---------------------------------------------------------------------------
# 4. Pipeline
# ---------------------------------------------------------------------------
def depurar(df: pd.DataFrame):
    log = []  # (fila, columna, valor_original, accion, causa)

    df = df.rename(columns=NOMBRES_CORTOS)
    vacias = [c for c in df.columns if df[c].isna().all()]
    df = df.drop(columns=vacias)
    for c in vacias:
        log.append(("*", c, "", "columna eliminada", "100 % vacía"))

    # Estaciones
    est = df["estacion"].str.strip().str.replace(r"\s+", " ", regex=True)
    df["estacion"] = est.replace(ESTACIONES)

    # Fechas: años mal digitados (1193 -> 1993, 1194 -> 1994, 1290 -> 1990)
    fechas = pd.to_datetime(df["fecha_raw"], format="%Y %b %d %I:%M:%S %p", errors="coerce")
    año = fechas.dt.year
    corr = {1193: 1993, 1194: 1994, 1290: 1990}
    for i in df.index[año.isin(corr)]:
        log.append((i, "fecha", df.at[i, "fecha_raw"], f"año -> {corr[año[i]]}", "año fuera de rango (digitación)"))
    fechas = pd.to_datetime({
        "year": año.replace(corr), "month": fechas.dt.month, "day": fechas.dt.day})
    df["fecha"] = fechas
    df["anio"] = fechas.dt.year
    df["mes"] = fechas.dt.month
    df = df.drop(columns="fecha_raw")

    # Valores numéricos
    numericas = [c for c in df.columns if c not in ("estacion", "fecha", "anio", "mes")]
    banderas = pd.DataFrame(index=df.index)
    for c in numericas:
        pares = df[c].map(convertir)
        nums = pares.map(lambda p: p[0]).astype(float)
        flags = pares.map(lambda p: p[1])
        orig = df[c]
        for i in df.index[flags == "no_convertible"]:
            log.append((i, c, orig[i], "-> nulo", "texto no convertible"))
        bajo_ld = flags == "<"
        nums[bajo_ld] = nums[bajo_ld] * FACTOR_LD
        banderas[c] = flags.replace({"nulo": "", "no_convertible": ""})
        df[c] = nums

    # Rangos plausibles
    for c, (lo, hi) in RANGOS.items():
        fuera = df[c].notna() & ~df[c].between(lo, hi)
        for i in df.index[fuera]:
            log.append((i, c, df.at[i, c], "-> nulo", f"fuera de rango plausible [{lo}, {hi}]"))
        df.loc[fuera, c] = np.nan

    # Duplicados fecha + estación: se conservan pero se marcan (revisar con la CVC)
    dup = df.duplicated(["fecha", "estacion"], keep=False)
    df["duplicado_fecha_estacion"] = dup
    for i in df.index[dup]:
        log.append((i, "fecha+estacion", "", "marcado", "misma estación y fecha con valores distintos"))

    df.insert(0, "id_muestreo", range(1, len(df) + 1))
    reporte = pd.DataFrame(log, columns=["fila_original", "columna", "valor_original", "accion", "causa"])
    banderas.insert(0, "id_muestreo", df["id_muestreo"])
    return df, banderas, reporte


def main():
    origen = Path(sys.argv[1])
    destino = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("datos/procesados")
    destino.mkdir(parents=True, exist_ok=True)
    df, banderas, reporte = depurar(leer_cvc(origen))
    df.to_csv(destino / "datos_limpios.csv", index=False)
    banderas.to_csv(destino / "banderas_censura.csv", index=False)
    reporte.to_csv(destino / "reporte_limpieza.csv", index=False)
    print(f"Registros: {len(df)} | Columnas útiles: {df.shape[1]} | Correcciones registradas: {len(reporte)}")
    print(reporte.groupby("causa").size().to_string())


if __name__ == "__main__":
    main()
