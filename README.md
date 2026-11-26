# Modelo de clasificación de la calidad del agua – río Cauca

Trabajo de grado – Anyeli Tatiana Angulo Paz – Ingeniería en Sistemas, UNIAJC.
Metodología: CRISP-DM. Datos: red de monitoreo de la CVC (1990–2025, 19 estaciones).

## Instalación
    py -m pip install -r requirements.txt

## Ejecución (en orden, desde esta carpeta)
    py src\limpieza.py datos\crudos\Calidad_del_agua_del_Rio_Cauca.csv datos\procesados
    py src\ica.py datos\procesados\datos_limpios.csv datos\procesados\datos_con_ica.csv
    py src\exploratorio.py
    py src\cargar_bd.py
    py src\entrenar.py
    py -m streamlit run app\app.py

## Pruebas
    py -m pytest -v

## Estructura
    datos/crudos/        archivo original de la CVC (no se modifica)
    datos/procesados/    salidas de limpieza e ICA; solo datos_con_ica.csv se versiona
    src/                 limpieza.py, ica.py, exploratorio.py, cargar_bd.py, entrenar.py
    bd/                  esquema.sql y consultas de comprobación (la .db se regenera)
    modelos/             modelos entrenados .joblib (se regeneran, no se versionan)
    app/                 prototipo Streamlit (app.py) y lógica (servicio.py)
    tests/               pruebas automáticas pytest
    notebooks/           reservado para análisis exploratorio adicional
    docs/
      bitacora.md, decisiones.md, diccionario_datos.md
      eda/               figuras y tablas del análisis exploratorio (fase 2)
      diseno/            arquitectura, modelo E-R y secuencia (OE2)
      capturas/          evidencias de pruebas
      comparacion_modelos.csv, matriz_confusion.csv, importancia_variables.csv  (salidas de entrenar.py)
      Pruebas_prototipo_calidad_agua.docx, resultados_pruebas.md
