# Manual técnico

**Sistema:** Modelo predictivo para la clasificación de la calidad del agua del río Cauca
**Autora:** Anyeli Tatiana Angulo Paz · Ingeniería en Sistemas, UNIAJC
**Versión del documento:** 1.0 (26 de noviembre de 2026) · **Repositorio:** https://github.com/AnyeliA/calidad-agua-rio-cauca

---

## 1. Propósito y alcance

Este manual explica cómo instalar, configurar, ejecutar, probar y mantener el sistema. Está dirigido al **administrador del modelo**: una persona con conocimientos básicos de sistemas que sabe usar la consola de Windows (cmd).

El sistema tiene tres partes:

| Capa | Qué hace | Archivos |
|---|---|---|
| Datos | Depura el archivo de la CVC, calcula el ICA, carga la base de datos y genera el análisis exploratorio | `src/limpieza.py`, `src/ica.py`, `src/cargar_bd.py`, `src/exploratorio.py` |
| Modelo | Entrena, valida, compara, versiona y registra los modelos | `src/entrenar.py` |
| Presentación | Prototipo web local para clasificar muestras y consultar información | `app/app.py` (interfaz), `app/servicio.py` (lógica) |

La arquitectura, el modelo entidad-relación y el diagrama de secuencia están en `docs/diseno/`.

## 2. Requisitos del entorno

| Elemento | Requisito |
|---|---|
| Sistema operativo | Windows 10 u 11 (probado en Windows 11) |
| Python | 3.10 (probado con 3.10.11), instalado con la opción *Add Python to PATH* |
| Espacio en disco | 2 GB libres, como mínimo, para las librerías |
| Memoria | 4 GB de RAM |
| Navegador | Chrome, Edge o Firefox actualizados |
| Git | Opcional, para clonar el repositorio |
| Internet | Solo para instalar las librerías; el sistema funciona sin conexión |

Librerías, con las versiones fijadas en `requirements.txt` (RNF-02):

```
pandas==2.3.3        numpy==2.2.6        scikit-learn==1.7.2   scipy==1.15.3
joblib==1.6.0        streamlit==1.65.0   SQLAlchemy==2.0.57    pytest==9.2.0
```

> Las versiones están fijadas porque los resultados del modelo cambian con otras versiones de scikit-learn. No actualice las librerías sin volver a entrenar y registrar el cambio en `docs/decisiones.md`.

## 3. Instalación

Ejecute un comando por línea en el cmd.

1. **Obtener el código**
   ```
   git clone https://github.com/AnyeliA/calidad-agua-rio-cauca.git proyecto_calidad_agua
   cd proyecto_calidad_agua
   ```
   Si no usa Git, descargue el ZIP del repositorio (botón *Code → Download ZIP*), descomprímalo y entre a la carpeta con `cd`.

2. **Comprobar Python**
   ```
   py --version
   ```
   Debe mostrar `Python 3.10.x`.

3. **Instalar las librerías**
   ```
   py -m pip install --no-cache-dir -r requirements.txt
   ```

4. **Ubicar los datos de la CVC**
   Debe existir el archivo `datos\crudos\Calidad_del_agua_del_Rio_Cauca.csv`. Este archivo no se modifica nunca.

## 4. Ejecución del flujo completo

Desde la carpeta del proyecto, en este orden:

| Paso | Comando | Resultado esperado |
|---|---|---|
| 1. Depurar | `py src\limpieza.py datos\crudos\Calidad_del_agua_del_Rio_Cauca.csv datos\procesados` | `Registros: 2368 \| Columnas útiles: 45 \| Correcciones registradas: 531` |
| 2. Calcular el ICA | `py src\ica.py datos\procesados\datos_limpios.csv datos\procesados\datos_con_ica.csv` | 2.183 registros con ICA calculable |
| 3. Análisis exploratorio | `py src\exploratorio.py` | `Registros: 2368 \| con ICA: 2183 \| estaciones: 19` y las figuras en `docs\eda` |
| 4. Crear la base de datos | `py src\cargar_bd.py` | Comprobaciones correctas: 19 estaciones, 2.368 muestreos |
| 5. Entrenar | `py src\entrenar.py` | `MODELO ACTIVO: regresion_logistica (F1 validación 0.636, F1 prueba 0.554)` |
| 6. Abrir el prototipo | `py -m streamlit run app\app.py` | Se abre el navegador en `http://localhost:8501` |

Para cerrar el prototipo, presione `Ctrl + C` en el cmd.

## 5. Archivos que genera el sistema

| Archivo o carpeta | Contenido | ¿Se versiona en Git? |
|---|---|---|
| `datos/procesados/datos_limpios.csv` | Datos depurados | No (se regenera) |
| `datos/procesados/reporte_limpieza.csv` | Cada corrección con su causa | No |
| `datos/procesados/banderas_censura.csv` | Celdas reportadas como `<LD` o `>x` | No |
| `datos/procesados/datos_con_ica.csv` | Dataset preparado con el ICA y su clase | **Sí** |
| `bd/calidad_agua.db` | Base de datos SQLite (6 tablas) | No (se regenera) |
| `modelos/*.joblib` | Modelos entrenados, con versión `AAAAMMDD-HHMM` | No (se regeneran) |
| `docs/comparacion_modelos.csv`, `registro_experimentos.csv`, `reporte_por_clase.csv`, `matriz_confusion.csv`, `importancia_variables.csv` | Resultados del entrenamiento | Sí |
| `docs/eda/` | Figuras y tablas del análisis exploratorio | Sí |

## 6. Base de datos

SQLite, archivo `bd/calidad_agua.db`. Tablas: `estacion`, `muestreo`, `clasificacion_ica`, `modelo`, `prediccion` y `registro_carga` (registro de cada carga de datos). El detalle de cada campo, su unidad y sus restricciones está en `docs/diccionario_datos.md`.

- Para recrearla desde cero, borre `bd\calidad_agua.db` y ejecute `py src\cargar_bd.py` y luego `py src\entrenar.py`.
- Las consultas de comprobación están en `bd/consultas_comprobacion.sql`.
- La tabla `modelo` guarda cada entrenamiento (parámetros, métricas, versión y archivo). Solo un registro tiene `activo = 1`.
- La tabla `prediccion` guarda cada clasificación hecha en el prototipo, con el modelo usado, las entradas, la categoría y el tiempo de respuesta.

## 7. Parámetros de configuración

| Parámetro | Archivo | Valor | Para qué sirve |
|---|---|---|---|
| `ANIO_CORTE` | `src/entrenar.py` | 2015 | Último año del entrenamiento; la prueba empieza al año siguiente |
| `SEMILLA` | `src/entrenar.py` | 42 | Hace que los resultados se puedan repetir |
| `MODELOS` | `src/entrenar.py` | 4 modelos y sus rejillas | Algoritmos e hiperparámetros evaluados |
| `VARIABLES` | `src/entrenar.py` | 14 variables | Entradas del modelo (sin las variables del ICA) |
| `ALTITUD_M` | `src/ica.py` | 950 m | Altitud usada para el oxígeno disuelto en % de saturación |
| `RANGOS` | `src/limpieza.py` | Por variable | Rangos plausibles; los valores fuera de rango se anulan |
| `VARIABLES` | `app/servicio.py` | 14 variables | Etiqueta, unidad, rango y si es obligatoria en el formulario |

Cada cambio de configuración debe registrarse como una decisión nueva en `docs/decisiones.md`.

## 8. Pruebas

```
py -m pytest -v
```

Ejecuta 27 pruebas automatizadas (unitarias, de integración y de sistema). Resultado esperado: `27 passed`. Las pruebas que escriben en la base de datos usan una copia temporal, así que no la modifican. Las pruebas manuales del prototipo están en `docs/Pruebas_prototipo_calidad_agua.docx`.

## 9. Mantenimiento

**Actualizar los datos de la CVC**
1. Guarde el archivo nuevo en `datos\crudos\` y deje el anterior sin modificar.
2. Ejecute los pasos 1 a 5 de la sección 4 con el nombre del archivo nuevo.
3. Revise `reporte_limpieza.csv`: si aparecen causas nuevas de corrección, analícelas antes de entrenar.
4. Ejecute las pruebas.
5. Registre en la bitácora la fecha, el archivo y el nuevo modelo activo.

**Reentrenar el modelo**
1. Ejecute `py src\entrenar.py`. Cada entrenamiento crea una versión nueva y no borra las anteriores.
2. Si el prototipo está abierto, ciérrelo y vuelva a abrirlo. El modelo queda en memoria y solo se recarga al reiniciar.
3. Verifique que el modelo activo cumpla los criterios de éxito (F1-macro ≥ 0,55 en la prueba).

**Volver a una versión anterior del modelo**
En la base de datos, ponga `activo = 0` en todos los modelos y `activo = 1` en el que quiere usar. Su archivo `.joblib` debe existir en `modelos/`.

**Copias de seguridad**
El código y los documentos están en GitHub. La base de datos y los modelos se regeneran con los scripts, por eso no se versionan.

## 10. Solución de problemas

| Problema | Causa | Solución |
|---|---|---|
| `"python" no se reconoce...` | Python no está en el PATH | Use `py` en lugar de `python`, o reinstale Python marcando *Add Python to PATH* |
| `No space left on device` al instalar | Falta espacio en disco | Libere espacio e instale con `--no-cache-dir` |
| `No existe la base de datos` en el prototipo | No se ejecutó `cargar_bd.py` | Ejecute los pasos 4 y 5 de la sección 4 |
| `No hay un modelo activo` | No se ejecutó `entrenar.py` | Ejecute el paso 5 |
| `fatal: not a git repository` | El cmd no está en la carpeta del proyecto | Entre con `cd proyecto_calidad_agua` |
| `IndentationError` | Un archivo `.py` se editó a mano y perdió la sangría | Recupere el archivo desde GitHub |
| El prototipo muestra el modelo anterior | El modelo quedó en memoria | Cierre el prototipo (`Ctrl + C`) y ábralo de nuevo |
| Métricas distintas a las documentadas | Versiones de librerías distintas | Reinstale con `requirements.txt` |
