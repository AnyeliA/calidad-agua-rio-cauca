"""Pruebas unitarias del componente C1 (limpieza.py) · RF-01."""
import math

import pandas as pd

from limpieza import convertir, depurar


def test_PU01_coma_decimal():
    assert convertir("6,87") == (6.87, "")


def test_PU02_bajo_limite_de_deteccion():
    valor, bandera = convertir("<1,0")
    assert valor == 1.0 and bandera == "<"     # el factor 0,5 se aplica en depurar()


def test_PU03_notacion_coliformes():
    valor, _ = convertir("2.4*10E4")
    assert valor == 24000


def test_textos_de_nulo():
    for texto in ["N.D.", "*", "---", "´"]:
        valor, _ = convertir(texto)
        assert math.isnan(valor)


def _fila(fecha, estacion="YOTOCO", **valores):
    base = {"FECHA DE MUESTREO": fecha, "ESTACIONES": estacion, "pH": "7", "TEMPERATURA (°C)": "24",
            "NITRITOS (mg N-NO2/l)": None, "NITRATOS (mg N-NO3/l)": None,
            "COLIFORMES TOTALES (NMP/100 ml)": None, "COLIFORMES FECALES (NMP/100 ml)": None,
            # columnas con rango plausible en limpieza.py (valores normales)
            "OXIGENO DISUELTO (mg O2/l)": "6", "CONDUCTIVIDAD ELÉCTRICA (µS/cm)": "120",
            "SOLIDOS SUSPENDIDOS TOTALES (mg SS/l)": "40", "DEMANDA QUIMICA DE OXIGENO (mg O2/l)": "15",
            "DEMANDA BIOQUIMICA DE OXIGENO (mg O2/l)": "2", "TURBIEDAD (UNT)": "30",
            "NITROGENO AMONIACAL (mg N-NH3/l)": "0,2", "CLORUROS (mg Cl/l)": "5",
            "SULFATOS (mg SO4/l)": "12", "ALCALINIDAD TOTAL (mg CaCO3/l)": "40"}
    base.update(valores)
    return base


# Fila de relleno: la limpieza elimina columnas 100 % vacías, así que cada columna necesita un dato.
RELLENO = _fila("2020 Feb 01 12:00:00 AM", "JUANCHITO", **{"NITRITOS (mg N-NO2/l)": "0,02",
              "NITRATOS (mg N-NO3/l)": "0,3", "COLIFORMES TOTALES (NMP/100 ml)": "9300",
              "COLIFORMES FECALES (NMP/100 ml)": "1500"})


def _df(fila):
    return pd.DataFrame([fila, RELLENO], dtype=object)


def test_correccion_de_anio_mal_digitado():
    df = _df(_fila("1193 Oct 19 12:00:00 AM"))
    limpio, _, reporte = depurar(df)
    assert limpio.loc[0, "anio"] == 1993
    assert "año fuera de rango (digitación)" in set(reporte["causa"])


def test_temperatura_fuera_de_rango_queda_nula():
    df = _df(_fila("2020 Jan 10 12:00:00 AM", **{"TEMPERATURA (°C)": "2"}))
    limpio, _, _ = depurar(df)
    assert pd.isna(limpio.loc[0, "temperatura"])


def test_coliformes_corridos_2022():
    df = _df(_fila("2022 Aug 03 12:00:00 AM",
                   **{"NITRITOS (mg N-NO2/l)": "2.40E+03", "NITRATOS (mg N-NO3/l)": "4.30E+02"}))
    limpio, _, _ = depurar(df)
    assert limpio.loc[0, "coliformes_totales"] == 2400
    assert limpio.loc[0, "coliformes_fecales"] == 430
    assert pd.isna(limpio.loc[0, "nitritos"])
