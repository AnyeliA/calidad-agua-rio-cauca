"""
Prototipo: clasificación de la calidad del agua del río Cauca.
Ejecutar desde la carpeta del proyecto:
    py -m streamlit run app\\app.py
"""
import pandas as pd
import streamlit as st

import servicio as sv

st.set_page_config(page_title="Calidad del agua · río Cauca", page_icon="💧", layout="wide")

COLOR = {"Bueno/Aceptable": "green", "Regular": "orange", "Malo": "red"}
AVISO = ("Herramienta de apoyo académico. Estima la categoría del ICA a partir de variables "
         "que no forman parte del índice; no reemplaza el análisis de laboratorio ni el ICA oficial.")


def inicial(clave):
    """Valor inicial vacío, salvo que ya venga de 'Cargar un muestreo real'."""
    return {} if clave in st.session_state else {"value": None}


@st.cache_resource
def cargar_modelo():
    return sv.modelo_activo()


# =============================== C6 + C7 ===================================
def pagina_clasificar():
    st.title("Clasificar una muestra")
    st.caption(AVISO)
    try:
        info, paquete = cargar_modelo()
    except Exception as e:
        st.error(str(e))
        st.stop()
    st.write(f"Modelo activo: **{info['nombre']}** · versión {info['version']} · "
             f"F1-macro {info['f1_macro']:.3f}")

    if st.button("Cargar un muestreo real de prueba (2016–2025)"):
        valores, contexto = sv.ejemplo_real()
        for clave, valor in valores.items():
            st.session_state[clave] = valor
        st.session_state["contexto"] = contexto

    if "contexto" in st.session_state:
        c = st.session_state["contexto"]
        st.info(f"Ejemplo cargado: {c['estacion']}, {str(c['fecha'])[:10]}. "
                f"Categoría real según el ICA: **{c['clase_real']}** (ICA {c['ica']:.2f}).")

    with st.form("formulario"):
        st.subheader("Variables obligatorias")
        columnas = st.columns(4)
        obligatorias = [k for k, v in sv.VARIABLES.items() if v[4]]
        opcionales = [k for k, v in sv.VARIABLES.items() if not v[4]]
        entradas = {}
        for i, clave in enumerate(obligatorias):
            etiqueta, unidad, *_ = sv.VARIABLES[clave]
            entradas[clave] = columnas[i % 4].number_input(
                f"{etiqueta} ({unidad})", key=clave, format="%.3f", **inicial(clave))
        st.subheader("Variables opcionales")
        st.caption("Si no se miden, el modelo usa la mediana del periodo de entrenamiento.")
        columnas = st.columns(4)
        for i, clave in enumerate(opcionales):
            etiqueta, unidad, *_ = sv.VARIABLES[clave]
            entradas[clave] = columnas[i % 4].number_input(
                f"{etiqueta} ({unidad})", key=clave, format="%.4g", **inicial(clave))
        enviado = st.form_submit_button("Clasificar", type="primary")

    if not enviado:
        return
    errores = sv.validar(entradas)
    if errores:
        st.error("Revise los datos:\n\n" + "\n".join(f"- {e}" for e in errores))
        return

    resultado = sv.clasificar(entradas, info, paquete)
    id_pred = sv.guardar_prediccion(entradas, resultado)
    categoria = resultado["categoria"]
    st.subheader("Resultado")
    st.markdown(f"### :{COLOR[categoria]}[{categoria}]")
    st.write(sv.DESCRIPCION_CLASE[categoria])
    st.bar_chart(pd.Series(resultado["probabilidades"], name="probabilidad"), horizontal=True)
    st.caption(f"Tiempo de respuesta: {resultado['tiempo_ms']} ms · "
               f"Predicción n.º {id_pred} guardada en la base de datos.")
    faltantes = [sv.VARIABLES[k][0] for k in opcionales if entradas[k] is None]
    if faltantes:
        st.warning("Valores estimados con la mediana: " + ", ".join(faltantes) + ".")


# =================================== C8 ====================================
def pagina_modelo():
    st.title("Modelo y métricas")
    st.caption(AVISO)
    tabla = sv.comparacion_modelos()
    activo = tabla[tabla.activo == 1].iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Modelo activo", activo.algoritmo)
    b.metric("F1-macro", f"{activo.f1_macro:.3f}")
    c.metric("Accuracy", f"{activo.accuracy:.3f}")
    d.metric("Predicciones registradas", sv.total_predicciones())
    st.write(f"Entrenamiento: {activo.periodo_entrenamiento} · Prueba: {activo.periodo_prueba} · "
             f"Versión {activo.version}")

    st.subheader("Comparación de modelos (conjunto de prueba)")
    vista = tabla.assign(tipo=tabla.es_control.map({0: "Principal", 1: "Control (con variables ICA)"}))
    st.dataframe(vista[["nombre", "tipo", "f1_macro", "accuracy", "precision_macro", "recall_macro"]],
                 hide_index=True, width="stretch")

    izq, der = st.columns(2)
    with izq:
        st.subheader("Matriz de confusión")
        matriz = sv.leer_reporte("matriz_confusion.csv")
        if matriz is not None:
            st.dataframe(matriz, width="stretch")
    with der:
        st.subheader("Importancia de variables")
        imp = sv.leer_reporte("importancia_variables.csv")
        if imp is not None:
            st.bar_chart(imp["importancia"].head(8), horizontal=True)

    st.subheader("Limitaciones")
    st.markdown(
        "- La clase **Malo** tiene pocos casos (30 en prueba): su precisión es baja.\n"
        "- El modelo se entrenó con 1990–2015; los cambios recientes del río pueden reducir su desempeño.\n"
        "- Algunas correcciones de los datos de la CVC (2022 y 2001–2005) están pendientes de confirmación.\n"
        "- El resultado es orientativo y no sustituye la medición de las cinco variables del ICA.")


# =================================== C9 ====================================
def pagina_historico():
    st.title("Consulta histórica")
    estacion = st.selectbox("Estación", sv.estaciones())
    desde, hasta = st.slider("Años", 1990, 2025, (2010, 2025))
    datos = sv.historico(estacion, desde, hasta)
    if datos.empty:
        st.info("No hay muestreos para esa estación y periodo.")
        return
    st.metric("Muestreos", len(datos))
    st.line_chart(datos.set_index("fecha")["ica"], y_label="ICA")
    st.dataframe(datos, hide_index=True, width="stretch")


st.navigation([
    st.Page(pagina_clasificar, title="Clasificar", icon="💧", default=True),
    st.Page(pagina_modelo, title="Modelo y métricas", icon="📊"),
    st.Page(pagina_historico, title="Consulta histórica", icon="📅"),
]).run()
