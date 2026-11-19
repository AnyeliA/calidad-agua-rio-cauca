# Diccionario de datos

Base de datos: **SQLite** (`bd/calidad_agua.db`). Se crea desde cero con `py src\cargar_bd.py` a partir de `bd/esquema.sql`.  
Requisito: RF-02 · Componente: C2 · Fuente de los datos: CVC, calidad del agua del río Cauca, 1990–2025 (datos públicos).

## Modelo de datos

| Tabla | Qué guarda | Registros tras la carga | Relación |
|---|---|---|---|
| estacion | Estaciones de monitoreo de la CVC | 19 | 1 estación → N muestreos |
| muestreo | Un muestreo por estación y fecha, con las variables depuradas | 2.368 | N → 1 estacion; 1 → 0..1 clasificacion_ica |
| clasificacion_ica | ICA calculado y clase para el modelo (variable objetivo) | 2.183 | 1 → 1 muestreo |
| modelo | Modelos entrenados, versionados con sus métricas | 5 por cada entrenamiento | 1 modelo → N predicciones |
| prediccion | Clasificaciones hechas desde el prototipo | Crece con el uso | N → 1 modelo |
| registro_carga | Trazabilidad de cada carga de datos | 1 por carga | — |

Convenciones: `PK` llave primaria, `FK` llave foránea. Los valores reportados como «<LD» (bajo el límite de detección) se guardan como LD × 0,5; el detalle de qué celdas venían así queda en `datos/procesados/banderas_censura.csv`.

## Tabla `estacion`

| Campo | Tipo | Unidad | Descripción | Restricciones y reglas |
|---|---|---|---|---|
| id_estacion | INTEGER | — | Identificador de la estación | PK, autoincremental |
| nombre | TEXT | — | Nombre de la estación según la CVC, normalizado (sin espacios dobles) | NOT NULL, UNIQUE |
| cercana_puerto_tejada | INTEGER | 0/1 | 1 si la estación está aguas arriba o cerca de Puerto Tejada | NOT NULL, CHECK 0 o 1; por defecto 0 |

## Tabla `muestreo`

| Campo | Tipo | Unidad | Descripción | Restricciones y reglas |
|---|---|---|---|---|
| id_muestreo | INTEGER | — | Identificador del muestreo (orden del archivo de la CVC) | PK |
| id_estacion | INTEGER | — | Estación donde se tomó la muestra | FK → estacion, NOT NULL |
| fecha | TEXT | AAAA-MM-DD | Fecha del muestreo; años mal digitados corregidos (1193→1993, 1194→1994, 1290→1990) | NOT NULL |
| anio | INTEGER | año | Año del muestreo; define la división entrenamiento (≤ 2015) / prueba (≥ 2016) | NOT NULL, CHECK 1990 a 2100 |
| mes | INTEGER | mes | Mes del muestreo | NOT NULL, CHECK 1 a 12 |
| duplicado_fecha_estacion | INTEGER | 0/1 | 1 si hay otro muestreo con la misma estación y fecha y valores distintos | NOT NULL, CHECK 0 o 1 |
| ph | REAL | — | Potencial de hidrógeno: acidez o alcalinidad del agua. Uso: Cálculo del ICA (no es entrada del modelo) | Depuración: fuera de [4, 10] → nulo; CHECK en BD: 4 a 10 |
| od | REAL | mg O2/l | Oxígeno disuelto. Uso: Cálculo del ICA (no es entrada del modelo) | Depuración: fuera de [0, 15] → nulo; CHECK en BD: 0 a 15 |
| sst | REAL | mg SS/l | Sólidos suspendidos totales. Uso: Cálculo del ICA (no es entrada del modelo) | Depuración: fuera de [0, 10000] → nulo; CHECK en BD: ≥ 0 |
| dqo | REAL | mg O2/l | Demanda química de oxígeno. Uso: Cálculo del ICA (no es entrada del modelo) | Depuración: fuera de [0, 1000] → nulo; CHECK en BD: ≥ 0 |
| conductividad | REAL | µS/cm | Conductividad eléctrica. Uso: Cálculo del ICA (no es entrada del modelo) | Depuración: fuera de [10, 2000] → nulo; CHECK en BD: 10 a 2.000 |
| temperatura | REAL | °C | Temperatura del agua. Uso: Entrada del modelo (obligatoria en el formulario) | Depuración: fuera de [15, 35] → nulo; CHECK en BD: 15 a 35 |
| color | REAL | UPC | Color aparente. Uso: Entrada del modelo | Real ≥ 0 o nulo |
| turbiedad | REAL | UNT | Turbiedad. Uso: Entrada del modelo (obligatoria en el formulario) | Depuración: fuera de [0, 5000] → nulo |
| solidos_totales | REAL | mg SST/l | Sólidos totales. Uso: Excluida: fuga de información del ICA | Real ≥ 0 o nulo |
| solidos_disueltos | REAL | mg SD/l | Sólidos disueltos. Uso: Excluida: fuga de información del ICA | Real ≥ 0 o nulo |
| dbo | REAL | mg O2/l | Demanda bioquímica de oxígeno a 5 días (DBO5). Uso: Entrada del modelo (obligatoria en el formulario) | Depuración: fuera de [0, 500] → nulo; CHECK en BD: ≥ 0 |
| dureza_total | REAL | mg CaCO3/l | Dureza total. Uso: Entrada del modelo | Real ≥ 0 o nulo |
| dureza_calcica | REAL | mg CaCO3/l | Dureza cálcica. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| dureza_magnesica | REAL | mg CaCO3/l | Dureza magnésica. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| calcio | REAL | mg Ca/l | Calcio. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| magnesio | REAL | mg Mg/l | Magnesio. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| alcalinidad | REAL | mg CaCO3/l | Alcalinidad total. Uso: Entrada del modelo (obligatoria en el formulario) | Depuración: fuera de [0, 500] → nulo |
| bicarbonatos | REAL | mg CaCO3/l | Bicarbonatos. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| hierro_total | REAL | mg Fe/l | Hierro total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| manganeso_total | REAL | mg Mn/l | Manganeso total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| sodio_total | REAL | mg Na/l | Sodio total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| potasio_total | REAL | mg K/l | Potasio total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| cobre_total | REAL | mg Cu/l | Cobre total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| zinc_total | REAL | mg Zn/l | Zinc total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| nitrogeno_total | REAL | mg N/l | Nitrógeno total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| nitrogeno_amoniacal | REAL | mg N-NH3/l | Nitrógeno amoniacal. Uso: Entrada del modelo | Depuración: fuera de [0, 50] → nulo |
| nitritos | REAL | mg N-NO2/l | Nitritos. Uso: Entrada del modelo | Depuración: fuera de [0, 5] → nulo |
| nitratos | REAL | mg N-NO3/l | Nitratos. Uso: Entrada del modelo | Depuración: fuera de [0, 50] → nulo |
| cloruros | REAL | mg Cl/l | Cloruros. Uso: Entrada del modelo | Depuración: fuera de [0, 500] → nulo |
| fosforo_total | REAL | mg P/l | Fósforo total. Uso: Entrada del modelo | Real ≥ 0 o nulo |
| fosfatos | REAL | mg PO4/l | Fosfatos. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| sulfatos | REAL | mg SO4/l | Sulfatos. Uso: Entrada del modelo | Depuración: fuera de [0, 500] → nulo |
| cadmio_total | REAL | mg Cd/l | Cadmio total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| cromo_total | REAL | mg Cr/l | Cromo total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| niquel_total | REAL | mg Ni/l | Níquel total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| plomo_total | REAL | mg Pb/l | Plomo total. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |
| coliformes_totales | REAL | NMP/100 ml | Coliformes totales. Uso: Entrada del modelo | Depuración: fuera de [0, 10¹⁰] → nulo |
| coliformes_fecales | REAL | NMP/100 ml | Coliformes fecales (termotolerantes). Uso: Entrada del modelo | Depuración: fuera de [0, 10⁹] → nulo |
| caudal | REAL | m3/s | Caudal del río. Uso: Almacenada; no usada por el modelo | Real ≥ 0 o nulo |

## Tabla `clasificacion_ica`

| Campo | Tipo | Unidad | Descripción | Restricciones y reglas |
|---|---|---|---|---|
| id_muestreo | INTEGER | — | Muestreo clasificado | PK y FK → muestreo; se borra en cascada |
| od_pct_sat | REAL | % | Oxígeno disuelto en % de saturación (calculado con temperatura y altitud de 950 m) | — |
| i_od, i_sst, i_dqo, i_ce, i_ph | REAL | 0 a 1 | Subíndices del ICA del IDEAM para cada variable | — |
| ica | REAL | 0 a 1 | Índice de Calidad del Agua (promedio de los 5 subíndices, peso 0,2 cada uno) | NOT NULL, CHECK 0 a 1 |
| categoria | TEXT | — | Categoría IDEAM: Muy malo, Malo, Regular, Aceptable o Bueno | NOT NULL, CHECK lista cerrada |
| clase_modelo | TEXT | — | Clase usada por el modelo: Malo, Regular o Bueno/Aceptable | NOT NULL, CHECK lista cerrada; índice |
| metodo | TEXT | — | Método de cálculo | NOT NULL; por defecto «ICA IDEAM 5 variables» |

## Tabla `modelo`

| Campo | Tipo | Unidad | Descripción | Restricciones y reglas |
|---|---|---|---|---|
| id_modelo | INTEGER | — | Identificador del modelo | PK, autoincremental |
| nombre | TEXT | — | Nombre del experimento (p. ej., random_forest) | NOT NULL; UNIQUE junto con version |
| algoritmo | TEXT | — | Clase de scikit-learn usada | NOT NULL |
| version | TEXT | AAAAMMDD-HHMM | Versión del entrenamiento | NOT NULL |
| fecha_entrenamiento | TEXT | fecha y hora | Momento del entrenamiento | NOT NULL; por defecto la hora local |
| periodo_entrenamiento, periodo_prueba | TEXT | años | Años usados para entrenar y para evaluar | NOT NULL |
| variables_entrada | TEXT | — | Variables de entrada separadas por comas | NOT NULL |
| parametros | TEXT | JSON | Hiperparámetros elegidos | — |
| accuracy, precision_macro, recall_macro, f1_macro | REAL | 0 a 1 | Métricas en el conjunto de prueba | CHECK 0 a 1 |
| ruta_archivo | TEXT | — | Ruta del archivo .joblib del modelo | NOT NULL |
| es_control | INTEGER | 0/1 | 1 si es el modelo de control que usa las variables del ICA | CHECK 0 o 1 |
| activo | INTEGER | 0/1 | 1 para el modelo que usa el prototipo (uno solo) | CHECK 0 o 1 |

## Tabla `prediccion`

| Campo | Tipo | Unidad | Descripción | Restricciones y reglas |
|---|---|---|---|---|
| id_prediccion | INTEGER | — | Identificador de la predicción | PK, autoincremental |
| id_modelo | INTEGER | — | Modelo que hizo la predicción | FK → modelo, NOT NULL; índice |
| fecha_hora | TEXT | fecha y hora | Momento de la clasificación | NOT NULL; por defecto la hora local |
| entradas | TEXT | JSON | Valores ingresados en el formulario | NOT NULL |
| categoria_predicha | TEXT | — | Clase resultante | NOT NULL, CHECK lista cerrada |
| tiempo_respuesta_ms | REAL | ms | Tiempo de la clasificación (RF-05: menos de 2 s) | — |

## Tabla `registro_carga`

| Campo | Tipo | Unidad | Descripción | Restricciones y reglas |
|---|---|---|---|---|
| id_carga | INTEGER | — | Identificador de la carga | PK, autoincremental |
| fecha_hora | TEXT | fecha y hora | Momento de la carga | NOT NULL |
| archivo_origen | TEXT | — | Archivo de datos cargado | NOT NULL |
| registros_cargados, registros_con_ica | INTEGER | registros | Conteos de la carga | NOT NULL |
| observacion | TEXT | — | Nota libre | — |

## Índices

| Índice | Tabla | Campos | Para qué |
|---|---|---|---|
| idx_muestreo_estacion_fecha | muestreo | id_estacion, fecha | Consulta histórica por estación (RF-07) |
| idx_muestreo_anio | muestreo | anio | División cronológica para el entrenamiento |
| idx_clasificacion_clase | clasificacion_ica | clase_modelo | Conteos por clase |
| idx_prediccion_modelo | prediccion | id_modelo | Predicciones por modelo |

## Seguridad y permisos

- Los datos son **públicos** (CVC) y **no contienen datos personales**, por lo que no se requiere carta de aval ni anonimización (Ley 1712 de 2014).
- SQLite no maneja usuarios ni roles. El control de acceso se hace así: la base es un archivo local que solo leen y escriben los scripts del proyecto y el prototipo; el prototipo solo **inserta** en `prediccion` y **lee** las demás tablas; y la base no se publica en el repositorio (`.gitignore`), sino que se reconstruye con el script.
- La integridad se protege con llaves foráneas activas (`PRAGMA foreign_keys = ON`), restricciones `CHECK` y validación de rangos en el formulario antes de escribir.
- Las consultas usan parámetros (`?`) y no concatenan texto del usuario, lo que evita inyección SQL.

## Comprobación

`bd/consultas_comprobacion.sql` (7 consultas) y las pruebas PI-01 de `tests/test_bd_y_modelo.py` verifican: 19 estaciones, 2.368 muestreos, 2.183 con ICA, 0 muestreos sin estación y rechazo de valores fuera de rango.
