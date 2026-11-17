"""
Entrenamiento, comparación y versionado de modelos de clasificación del ICA.
Componentes C4 (entrenamiento) y C5 (versionado) · OE3 · RNF-02, RNF-04.

Uso (desde la carpeta del proyecto):
    py src\\entrenar.py

Requiere haber ejecutado antes cargar_bd.py.

Qué hace:
 1. Lee de la base de datos los muestreos con ICA calculable.
 2. Divide por año: entrenamiento 1990-2015, prueba 2016-2025 (sin mezclar).
 3. Ajusta hiperparámetros solo con el entrenamiento (validación cruzada temporal).
 4. Compara: modelo base, árbol de decisión, Random Forest y regresión logística.
 5. Entrena un modelo de CONTROL con todas las variables (incluidas las del ICA).
 6. Guarda cada modelo en modelos/ y registra sus métricas en la tabla `modelo`.
 7. Marca como activo el de mayor F1-macro (sin contar base ni control).
 8. Escribe en docs/: comparación, matriz de confusión e importancia de variables.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.tree import DecisionTreeClassifier

RAIZ = Path(__file__).resolve().parent.parent
BD = RAIZ / "bd" / "calidad_agua.db"
CARPETA_MODELOS = RAIZ / "modelos"
CARPETA_DOCS = RAIZ / "docs"

ANIO_CORTE = 2015                      # entrenamiento <= 2015 < prueba
CLASES = ["Malo", "Regular", "Bueno/Aceptable"]
SEMILLA = 42

# Variables de entrada del modelo principal.
# Se EXCLUYEN las 5 del ICA (od, sst, dqo, conductividad, ph) y también
# solidos_totales y solidos_disueltos, porque contienen información del ICA
# (los totales incluyen los SST; los disueltos se relacionan con la conductividad).
VARIABLES = [
    "temperatura", "turbiedad", "color", "dbo", "nitrogeno_amoniacal", "nitratos",
    "nitritos", "fosforo_total", "coliformes_fecales", "coliformes_totales",
    "cloruros", "sulfatos", "alcalinidad", "dureza_total",
]
VARIABLES_ICA = ["od", "sst", "dqo", "conductividad", "ph"]
LOGARITMICAS = ["coliformes_fecales", "coliformes_totales"]   # varían en órdenes de magnitud

# Modelos a comparar y su rejilla de hiperparámetros (pequeña a propósito).
MODELOS = {
    "base_mayoritaria": (DummyClassifier(strategy="most_frequent"), {}),
    "arbol_decision": (
        DecisionTreeClassifier(class_weight="balanced", random_state=SEMILLA),
        {"modelo__max_depth": [3, 5, 8], "modelo__min_samples_leaf": [5, 20]},
    ),
    "random_forest": (
        RandomForestClassifier(class_weight="balanced", random_state=SEMILLA, n_jobs=-1),
        {"modelo__n_estimators": [200], "modelo__max_depth": [None, 10],
         "modelo__min_samples_leaf": [1, 5]},
    ),
    "regresion_logistica": (
        LogisticRegression(class_weight="balanced", max_iter=3000),
        {"modelo__C": [0.1, 1, 10]},
    ),
}


# ---------------------------------------------------------------------------
def leer_datos():
    columnas = ", ".join(f"m.{c}" for c in VARIABLES + VARIABLES_ICA)
    sql = f"""
        SELECT m.id_muestreo, m.fecha, m.anio, e.nombre AS estacion, {columnas},
               c.clase_modelo
        FROM muestreo m
        JOIN clasificacion_ica c ON c.id_muestreo = m.id_muestreo
        JOIN estacion e ON e.id_estacion = m.id_estacion
        ORDER BY m.fecha, m.id_muestreo
    """
    with sqlite3.connect(BD) as con:
        return pd.read_sql_query(sql, con)


def construir_pipeline(variables, modelo):
    logs = [v for v in variables if v in LOGARITMICAS]
    resto = [v for v in variables if v not in LOGARITMICAS]
    preparacion = ColumnTransformer([
        ("log", make_pipeline(SimpleImputer(strategy="median"), FunctionTransformer(np.log1p)), logs),
        ("num", SimpleImputer(strategy="median"), resto),
    ])
    # La imputación y el escalado se ajustan SOLO con los datos de entrenamiento.
    return Pipeline([("preparacion", preparacion), ("escalado", StandardScaler()), ("modelo", modelo)])


def metricas(y_real, y_pred):
    return {
        "accuracy": accuracy_score(y_real, y_pred),
        "precision_macro": precision_score(y_real, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_real, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_real, y_pred, average="macro", zero_division=0),
    }


def entrenar(nombre, modelo, rejilla, variables, X_tr, y_tr):
    pipe = construir_pipeline(variables, modelo)
    if not rejilla:
        return pipe.fit(X_tr[variables], y_tr), {}
    busqueda = GridSearchCV(pipe, rejilla, scoring="f1_macro", cv=TimeSeriesSplit(n_splits=4), n_jobs=-1)
    busqueda.fit(X_tr[variables], y_tr)
    return busqueda.best_estimator_, busqueda.best_params_


def registrar(con, fila):
    columnas = ", ".join(fila)
    con.execute(f"INSERT INTO modelo ({columnas}) VALUES ({', '.join('?' * len(fila))})", list(fila.values()))
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


# ---------------------------------------------------------------------------
def main():
    datos = leer_datos()
    entrenamiento = datos[datos["anio"] <= ANIO_CORTE]
    prueba = datos[datos["anio"] > ANIO_CORTE]
    assert set(entrenamiento["id_muestreo"]).isdisjoint(prueba["id_muestreo"])   # sin cruce (PU-05)

    y_tr, y_te = entrenamiento["clase_modelo"], prueba["clase_modelo"]
    print(f"Entrenamiento {entrenamiento.anio.min()}-{entrenamiento.anio.max()}: {len(entrenamiento)} registros")
    print(f"Prueba        {prueba.anio.min()}-{prueba.anio.max()}: {len(prueba)} registros")
    print("Clases en prueba:", y_te.value_counts().to_dict(), "\n")

    version = datetime.now().strftime("%Y%m%d-%H%M")
    periodo_tr = f"{entrenamiento.anio.min()}-{entrenamiento.anio.max()}"
    periodo_te = f"{prueba.anio.min()}-{prueba.anio.max()}"
    CARPETA_MODELOS.mkdir(exist_ok=True)
    CARPETA_DOCS.mkdir(exist_ok=True)

    experimentos = [(n, m, r, VARIABLES, 0) for n, (m, r) in MODELOS.items()]
    experimentos.append(("control_con_variables_ica", *MODELOS["random_forest"], VARIABLES + VARIABLES_ICA, 1))

    resultados, ajustados = [], {}
    with sqlite3.connect(BD) as con:
        con.execute("UPDATE modelo SET activo = 0")
        for nombre, modelo, rejilla, variables, es_control in experimentos:
            pipe, params = entrenar(nombre, modelo, rejilla, variables, entrenamiento, y_tr)
            m = metricas(y_te, pipe.predict(prueba[variables]))
            ruta = CARPETA_MODELOS / f"{nombre}_{version}.joblib"
            joblib.dump({"pipeline": pipe, "variables": variables, "clases": CLASES, "version": version}, ruta)
            id_modelo = registrar(con, {
                "nombre": nombre, "algoritmo": type(modelo).__name__, "version": version,
                "periodo_entrenamiento": periodo_tr, "periodo_prueba": periodo_te,
                "variables_entrada": ",".join(variables),
                "parametros": json.dumps({k.replace("modelo__", ""): v for k, v in params.items()}),
                **{k: round(v, 4) for k, v in m.items()},
                "ruta_archivo": str(ruta.relative_to(RAIZ)), "es_control": es_control,
            })
            ajustados[nombre] = pipe
            resultados.append({"id_modelo": id_modelo, "modelo": nombre, "control": es_control,
                               **{k: round(v, 3) for k, v in m.items()}, "parametros": params})
            print(f"{nombre:28s} F1-macro={m['f1_macro']:.3f}  Accuracy={m['accuracy']:.3f}")

        tabla = pd.DataFrame(resultados)
        candidatos = tabla[(tabla.control == 0) & (tabla.modelo != "base_mayoritaria")]
        mejor = candidatos.sort_values("f1_macro", ascending=False).iloc[0]
        con.execute("UPDATE modelo SET activo = 1 WHERE id_modelo = ?", (int(mejor.id_modelo),))
        con.commit()

    # ------------------------- Reportes para el documento --------------------
    pipe = ajustados[mejor.modelo]
    y_pred = pipe.predict(prueba[VARIABLES])
    matriz = pd.DataFrame(confusion_matrix(y_te, y_pred, labels=CLASES),
                          index=[f"real {c}" for c in CLASES], columns=[f"pred {c}" for c in CLASES])
    imp = permutation_importance(pipe, prueba[VARIABLES], y_te, scoring="f1_macro",
                                 n_repeats=10, random_state=SEMILLA)
    importancia = (pd.DataFrame({"variable": VARIABLES, "importancia": imp.importances_mean,
                                 "desviacion": imp.importances_std})
                   .sort_values("importancia", ascending=False).round(4))

    tabla.drop(columns="id_modelo").to_csv(CARPETA_DOCS / "comparacion_modelos.csv", index=False)
    matriz.to_csv(CARPETA_DOCS / "matriz_confusion.csv")
    importancia.to_csv(CARPETA_DOCS / "importancia_variables.csv", index=False)

    print(f"\nMODELO ACTIVO: {mejor.modelo} (F1-macro {mejor.f1_macro:.3f})")
    print("\nReporte por clase (conjunto de prueba):")
    print(classification_report(y_te, y_pred, labels=CLASES, zero_division=0))
    print("Matriz de confusión:")
    print(matriz.to_string())
    print("\nVariables más importantes:")
    print(importancia.head(6).to_string(index=False))
    print("\nArchivos: modelos/*.joblib, docs/comparacion_modelos.csv, "
          "docs/matriz_confusion.csv, docs/importancia_variables.csv")


if __name__ == "__main__":
    main()
