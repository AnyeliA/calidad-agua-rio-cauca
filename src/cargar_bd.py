"""
Crea la base de datos desde cero y carga los datos depurados con ICA.
Componente C2 · Requisito RF-02 · Prueba de integración PI-01.

Uso (desde la carpeta del proyecto):
    py src\\cargar_bd.py

Requiere haber ejecutado antes limpieza.py e ica.py.
Resultado: bd/calidad_agua.db
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ESQUEMA = RAIZ / "bd" / "esquema.sql"
COMPROBACION = RAIZ / "bd" / "consultas_comprobacion.sql"
DATOS = RAIZ / "datos" / "procesados" / "datos_con_ica.csv"
BD = RAIZ / "bd" / "calidad_agua.db"

COLUMNAS_MEDICION = [
    "ph", "od", "sst", "dqo", "conductividad", "temperatura", "color", "turbiedad",
    "solidos_totales", "solidos_disueltos", "dbo", "dureza_total", "dureza_calcica",
    "dureza_magnesica", "calcio", "magnesio", "alcalinidad", "bicarbonatos", "hierro_total",
    "manganeso_total", "sodio_total", "potasio_total", "cobre_total", "zinc_total",
    "nitrogeno_total", "nitrogeno_amoniacal", "nitritos", "nitratos", "cloruros",
    "fosforo_total", "fosfatos", "sulfatos", "cadmio_total", "cromo_total", "niquel_total",
    "plomo_total", "coliformes_totales", "coliformes_fecales", "caudal",
]
COLUMNAS_ICA = ["od_pct_sat", "i_od", "i_sst", "i_dqo", "i_ce", "i_ph", "ica"]

# Clases del modelo: se agrupan Bueno y Aceptable (solo 62 registros "Bueno")
CLASE_MODELO = {"Muy malo": "Malo", "Malo": "Malo", "Regular": "Regular",
                "Aceptable": "Bueno/Aceptable", "Bueno": "Bueno/Aceptable"}

# Estaciones aguas arriba de Puerto Tejada / cercanas. CONFIRMAR EN EL MAPA.
CERCANAS_PUERTO_TEJADA = {"ANTES SUAREZ", "ANTES RIO OVEJAS", "ANTES RIO TIMBA", "PASO DE LA BALSA"}


def a_none(valor):
    """SQLite necesita None en lugar de NaN."""
    return None if pd.isna(valor) else valor


def crear_bd(con):
    con.executescript(ESQUEMA.read_text(encoding="utf-8"))


def cargar(con, df):
    cur = con.cursor()

    # Estaciones
    for nombre in sorted(df["estacion"].unique()):
        cur.execute("INSERT INTO estacion (nombre, cercana_puerto_tejada) VALUES (?, ?)",
                    (nombre, int(nombre in CERCANAS_PUERTO_TEJADA)))
    ids = dict(cur.execute("SELECT nombre, id_estacion FROM estacion").fetchall())

    # Muestreos
    cols = ["id_muestreo", "id_estacion", "fecha", "anio", "mes", "duplicado_fecha_estacion"] + COLUMNAS_MEDICION
    sql = f"INSERT INTO muestreo ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    filas = []
    for r in df.itertuples(index=False):
        filas.append([int(r.id_muestreo), ids[r.estacion], str(r.fecha)[:10], int(r.anio), int(r.mes),
                      int(bool(r.duplicado_fecha_estacion))] + [a_none(getattr(r, c)) for c in COLUMNAS_MEDICION])
    cur.executemany(sql, filas)

    # Clasificación ICA (solo registros con ICA calculable)
    con_ica = df[df["categoria_ica"].notna()]
    cols = ["id_muestreo"] + COLUMNAS_ICA + ["categoria", "clase_modelo"]
    sql = f"INSERT INTO clasificacion_ica ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    cur.executemany(sql, [
        [int(r.id_muestreo)] + [a_none(getattr(r, c)) for c in COLUMNAS_ICA]
        + [r.categoria_ica, CLASE_MODELO[r.categoria_ica]]
        for r in con_ica.itertuples(index=False)
    ])

    cur.execute("INSERT INTO registro_carga (archivo_origen, registros_cargados, registros_con_ica, observacion) "
                "VALUES (?, ?, ?, ?)",
                (DATOS.name, len(df), len(con_ica), "Carga completa desde datos depurados"))
    con.commit()


def comprobar(con):
    print("\nConsultas de comprobación:")
    for bloque in COMPROBACION.read_text(encoding="utf-8").split(";"):
        lineas = [l for l in bloque.strip().splitlines() if l.strip()]
        comentarios = [l[2:].strip() for l in lineas if l.startswith("--")]
        titulo = comentarios[-1] if comentarios else ""
        sql = "\n".join(l for l in lineas if not l.startswith("--"))
        if not sql:
            continue
        cur = con.execute(sql)
        nombres = [d[0] for d in cur.description]
        print(f"\n> {titulo}")
        print(pd.DataFrame(cur.fetchall(), columns=nombres).to_string(index=False))


def main():
    if not DATOS.exists():
        sys.exit(f"No existe {DATOS}. Ejecute primero limpieza.py e ica.py.")
    df = pd.read_csv(DATOS)
    if BD.exists():
        BD.unlink()  # se reconstruye desde cero: reproducible
    with sqlite3.connect(BD) as con:
        con.execute("PRAGMA foreign_keys = ON")
        crear_bd(con)
        cargar(con, df)
        print(f"Base de datos creada: {BD}")
        comprobar(con)


if __name__ == "__main__":
    main()
