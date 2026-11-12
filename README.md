# Modelo de clasificación de la calidad del agua – río Cauca

Trabajo de grado – Anyeli Tatiana Angulo Paz – Ingeniería en Sistemas, UNIAJC.

## Instalación
    pip install -r requirements.txt

## Ejecución (en orden)
    python src/limpieza.py datos/crudos/Calidad_del_agua_del_Rio_Cauca.csv datos/procesados
    python src/ica.py datos/procesados/datos_limpios.csv datos/procesados/datos_con_ica.csv

## Estructura
    datos/crudos      archivo original de la CVC (no se modifica)
    datos/procesados  salidas generadas por los scripts
    src/              código (limpieza, ICA, carga a BD, entrenamiento)
    notebooks/        análisis exploratorio
    bd/               esquema.sql y consultas de comprobación
    app/              prototipo Streamlit
    modelos/          modelos entrenados (.joblib)
    tests/            pruebas pytest
    docs/             bitácora, decisiones, resultados de pruebas
