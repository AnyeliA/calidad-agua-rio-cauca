"""
Lógica del prototipo (sin interfaz): validación, clasificación y acceso a la base de datos.
Se separa de app.py para poder probarla con pytest.
Componentes C6 (validación), C7 (clasificación y registro), C8 (métricas), C9 (histórico).
"""
import json
import sqlite3
import time
from pathlib import Path

import joblib
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BD = RAIZ / "bd" / "calidad_agua.db"
DOCS = RAIZ / "docs"

# Variables que pide el formulario: (etiqueta, unidad, mínimo, máximo, obligatoria)
# Rangos iguales a los de limpieza.py. Las no obligatorias se imputan con la mediana.
VARIABLES = {
    "temperatura":         ("Temperatura", "°C", 15.0, 35.0, True),
    "turbiedad":           ("Turbiedad", "UNT", 0.0, 5000.0, True),
    "alcalinidad":         ("Alcalinidad total", "mg CaCO3/L", 0.0, 500.0, True),
    "dbo":                 ("DBO5", "mg O2/L", 0.0, 500.0, True),
    "color":               ("Color", "UPC", 0.0, 3000.0, False),
    "dureza_total":        ("Dureza total", "mg CaCO3/L", 0.0, 500.0, False),
    "fosforo_total":       ("Fósforo total", "mg P/L", 0.0, 20.0, False),
    "nitrogeno_amoniacal": ("Nitrógeno amoniacal", "mg N-NH3/L", 0.0, 50.0, False),
    "nitratos":            ("Nitratos", "mg N-NO3/L", 0.0, 50.0, False),
    "nitritos":            ("Nitritos", "mg N-NO2/L", 0.0, 5.0, False),
    "cloruros":            ("Cloruros", "mg Cl/L", 0.0, 500.0, False),
    "sulfatos":            ("Sulfatos", "mg SO4/L", 0.0, 500.0, False),
    "coliformes_fecales":  ("Coliformes fecales", "NMP/100 mL", 0.0, 1e9, False),
    "coliformes_totales":  ("Coliformes totales", "NMP/100 mL", 0.0, 1e10, False),
}

DESCRIPCION_CLASE = {
    "Bueno/Aceptable": "ICA entre 0,71 y 1,00: calidad buena o aceptable.",
    "Regular": "ICA entre 0,51 y 0,70: calidad regular.",
    "Malo": "ICA entre 0,00 y 0,50: calidad mala o muy mala.",
}


def conectar():
    if not BD.exists():
        raise FileNotFoundError("No existe la base de datos. Ejecute src/cargar_bd.py y src/entrenar.py.")
    con = sqlite3.connect(BD)
    con.execute("PRAGMA foreign_keys = ON")
    return con


# ----------------------------- C6: validación ------------------------------
def validar(entradas: dict) -> list:
    """Devuelve la lista de errores. Lista vacía = datos válidos."""
    errores = []
    for clave, (etiqueta, unidad, minimo, maximo, obligatoria) in VARIABLES.items():
        valor = entradas.get(clave)
        if valor is None:
            if obligatoria:
                errores.append(f"{etiqueta}: es obligatorio.")
            continue
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            errores.append(f"{etiqueta}: debe ser un número.")
            continue
        if not minimo <= valor <= maximo:
            errores.append(f"{etiqueta}: fuera de rango ({minimo:g} a {maximo:g} {unidad}).")
    return errores


# ------------------------ C7: clasificación y registro ---------------------
def modelo_activo():
    """Devuelve (info del modelo como dict, objeto cargado de joblib)."""
    with conectar() as con:
        fila = pd.read_sql_query(
            "SELECT * FROM modelo WHERE activo = 1 ORDER BY id_modelo DESC LIMIT 1", con)
    if fila.empty:
        raise RuntimeError("No hay un modelo activo. Ejecute src/entrenar.py.")
    info = fila.iloc[0].to_dict()
    paquete = joblib.load(RAIZ / info["ruta_archivo"])
    return info, paquete


def clasificar(entradas: dict, info=None, paquete=None):
    """Clasifica un registro. Devuelve dict con categoría, probabilidades y tiempo en ms."""
    errores = validar(entradas)
    if errores:
        raise ValueError("; ".join(errores))
    if paquete is None:
        info, paquete = modelo_activo()
    inicio = time.perf_counter()
    fila = pd.DataFrame([{v: entradas.get(v) for v in paquete["variables"]}], dtype=float)
    pipe = paquete["pipeline"]
    categoria = pipe.predict(fila)[0]
    probabilidades = dict(zip(pipe.classes_, pipe.predict_proba(fila)[0].round(3)))
    ms = (time.perf_counter() - inicio) * 1000
    return {"categoria": categoria, "probabilidades": probabilidades,
            "tiempo_ms": round(ms, 1), "id_modelo": int(info["id_modelo"])}


def guardar_prediccion(entradas: dict, resultado: dict) -> int:
    with conectar() as con:
        cur = con.execute(
            "INSERT INTO prediccion (id_modelo, entradas, categoria_predicha, tiempo_respuesta_ms) "
            "VALUES (?, ?, ?, ?)",
            (resultado["id_modelo"], json.dumps(entradas), resultado["categoria"], resultado["tiempo_ms"]))
        return cur.lastrowid


def ejemplo_real(semilla=None):
    """Toma un muestreo real del periodo de prueba (2016-2025) para demostrar el prototipo."""
    columnas = ", ".join(f"m.{v}" for v in VARIABLES)
    with conectar() as con:
        df = pd.read_sql_query(
            f"SELECT m.id_muestreo, m.fecha, e.nombre AS estacion, {columnas}, c.clase_modelo, c.ica "
            "FROM muestreo m JOIN clasificacion_ica c ON c.id_muestreo = m.id_muestreo "
            "JOIN estacion e ON e.id_estacion = m.id_estacion "
            "WHERE m.anio >= 2016 AND m.temperatura IS NOT NULL AND m.turbiedad IS NOT NULL "
            "AND m.alcalinidad IS NOT NULL AND m.dbo IS NOT NULL", con)
    fila = df.sample(1, random_state=semilla).iloc[0]
    valores = {v: (None if pd.isna(fila[v]) else float(fila[v])) for v in VARIABLES}
    return valores, {"estacion": fila.estacion, "fecha": fila.fecha,
                     "clase_real": fila.clase_modelo, "ica": float(fila.ica)}


# ------------------------------ C8: métricas -------------------------------
def comparacion_modelos():
    """Modelos de la última versión entrenada."""
    with conectar() as con:
        return pd.read_sql_query(
            "SELECT nombre, algoritmo, accuracy, precision_macro, recall_macro, f1_macro, "
            "es_control, activo, version, periodo_entrenamiento, periodo_prueba, parametros "
            "FROM modelo WHERE version = (SELECT MAX(version) FROM modelo) "
            "ORDER BY es_control, f1_macro DESC", con)


def leer_reporte(nombre):
    ruta = DOCS / nombre
    return pd.read_csv(ruta, index_col=0) if ruta.exists() else None


def total_predicciones():
    with conectar() as con:
        return con.execute("SELECT COUNT(*) FROM prediccion").fetchone()[0]


# ------------------------------ C9: histórico ------------------------------
def estaciones():
    with conectar() as con:
        return [r[0] for r in con.execute("SELECT nombre FROM estacion ORDER BY nombre")]


def historico(estacion, anio_desde, anio_hasta):
    with conectar() as con:
        return pd.read_sql_query(
            "SELECT m.fecha, m.anio, c.ica, c.categoria, m.temperatura, m.turbiedad, m.od, m.dbo "
            "FROM muestreo m JOIN estacion e ON e.id_estacion = m.id_estacion "
            "LEFT JOIN clasificacion_ica c ON c.id_muestreo = m.id_muestreo "
            "WHERE e.nombre = ? AND m.anio BETWEEN ? AND ? ORDER BY m.fecha",
            con, params=(estacion, anio_desde, anio_hasta), parse_dates=["fecha"])
