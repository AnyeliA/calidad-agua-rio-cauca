# Registro de decisiones técnicas

Cada decisión indica la fecha, las alternativas consideradas, la razón y dónde queda la evidencia.
Las decisiones que cambian algo del diseño aprobado se marcan como **Cambio frente al diseño**.

| ID | Fecha | Fase CRISP-DM | Decisión |
|---|---|---|---|
| DEC-01 | 2026-11-18 | Transversal | Usar CRISP-DM como metodología |
| DEC-02 | 2026-11-12 | Preparación de los datos | Conservar todos los registros e imputar faltantes con la mediana |
| DEC-03 | 2026-11-12 | Preparación de los datos | Reemplazar los valores bajo el límite de detección por LD × 0,5 |
| DEC-04 | 2026-11-12 | Preparación de los datos | Anular los valores fuera de rangos plausibles |
| DEC-05 | 2026-11-12 | Preparación de los datos | Corregir años mal digitados |
| DEC-06 | 2026-11-17 | Preparación de los datos | Corregir coliformes corridos (2022) y nitritos en µg/L (2001–2005) |
| DEC-07 | 2026-11-12 | Preparación de los datos | Calcular el OD en % de saturación con altitud de 950 m |
| DEC-08 | 2026-11-12 | Preparación de los datos | Agrupar las categorías del ICA en tres clases |
| DEC-09 | 2026-11-12 | Modelado | Excluir las variables del ICA y los sólidos totales y disueltos |
| DEC-10 | 2026-11-17 | Modelado | Dividir los datos por año: 1990–2015 y 2016–2025 |
| DEC-11 | 2026-11-17 | Evaluación | Usar F1-macro como métrica principal |
| DEC-12 | 2026-11-17 | Evaluación | Dejar Random Forest como modelo activo |
| DEC-13 | 2026-11-17 | Preparación de los datos | Usar SQLite como motor de base de datos |
| DEC-14 | 2026-11-17 | Despliegue | Construir el prototipo con Streamlit y separar la lógica |
| DEC-15 | 2026-11-17 | Despliegue | Definir 4 variables obligatorias en el formulario |
| DEC-16 | 2026-11-17 | Transversal | No versionar la base de datos ni los modelos; fijar versiones de librerías |
| DEC-17 | 2026-11-25 | Preparación de los datos | Excluir componentes redundantes, metales traza, fosfatos, nitrógeno total y caudal; dejar hierro, manganeso, sodio y potasio para TG II |

---

### DEC-01. Usar CRISP-DM como metodología
- **Alternativas:** Scrum, ICONIX, XP o DevOps (rutas de la guía de entregables).
- **Razón:** el núcleo del proyecto es construir y evaluar un modelo a partir de datos históricos, y CRISP-DM organiza justamente ese ciclo (negocio, datos, preparación, modelado, evaluación y despliegue).
- **Condición:** la docente lo aprobó en la reunión del 18-nov-2026, con el compromiso de cumplir todos los entregables comunes de cada corte. Confirmación solicitada por correo.
- **Evidencia:** punto 3.6 del documento; correo de confirmación en `docs/evidencias/`.

### DEC-02. Conservar todos los registros e imputar faltantes con la mediana
- **Alternativas:** eliminar todo registro incompleto.
- **Razón:** eliminar incompletos reduciría los datos etiquetados de 2.183 a 1.399 (−36 %) y el conjunto de prueba de 515 a 260, y sesgaría el modelo hacia ciertas estaciones y años. Solo se excluyen los 185 registros sin ICA (no tienen variable objetivo). La mediana se calcula solo con el entrenamiento, dentro del pipeline, para evitar fuga de información.
- **Evidencia:** `src/entrenar.py` (SimpleImputer en el pipeline).

### DEC-03. Valores bajo el límite de detección = LD × 0,5
- **Alternativas:** dejarlos vacíos; usar el valor del límite.
- **Razón:** convención usual para datos censurados; dejarlos vacíos perdería la información de que el valor era bajo. Se guarda una bandera por celda para poder probar otra regla.
- **Evidencia:** `src/limpieza.py` (FACTOR_LD), `banderas_censura.csv`.

### DEC-04. Anular valores fuera de rangos plausibles
- **Alternativas:** conservarlos; recortarlos al límite.
- **Razón:** valores como 2 °C o 216 mg/L de oxígeno disuelto son errores de registro, no mediciones reales. Se anulan y quedan en el reporte con su causa.
- **Evidencia:** `src/limpieza.py` (RANGOS), `reporte_limpieza.csv`.

### DEC-05. Corregir años mal digitados (1193, 1194, 1290)
- **Razón:** los demás campos y el orden del archivo indican 1993, 1994 y 1990. Se corrigen 11 registros.
- **Defecto asociado:** D-01 (con pandas 2.3 la fecha quedaba nula; se corrigió leyendo el año como texto).
- **Evidencia:** `src/limpieza.py`, prueba `test_correccion_de_anio_mal_digitado`.

### DEC-06. Corregir coliformes corridos (2022) y nitritos en µg/L (2001–2005)
- **Razón:** en 2022 los valores de coliformes (2,3 · 4,3 · 9,3 × 10ⁿ) aparecen en las columnas de nitritos y nitratos (57 registros), y en 2001–2005 los nitritos tienen mediana 24 frente a 0,03 mg/L en los demás años (273 registros).
- **Cambio frente al diseño:** sí; se agregaron reglas de depuración no previstas. Se encontró al definir los rangos del prototipo y obligó a repetir la preparación, el modelado y la evaluación (iteración de CRISP-DM).
- **Pendiente:** confirmar con la CVC.
- **Evidencia:** `src/limpieza.py`, defectos D-02 y D-03, prueba `test_coliformes_corridos_2022`.

### DEC-07. Oxígeno disuelto en % de saturación con altitud de 950 m
- **Razón:** el ICA del IDEAM usa el OD en % de saturación y la CVC lo reporta en mg/L. Se usa la temperatura del agua y una altitud media del tramo vallecaucano.
- **Limitación:** usar la altitud de cada estación es una mejora para Trabajo de Grado II.
- **Evidencia:** `src/ica.py` (ALTITUD_M).

### DEC-08. Agrupar las categorías del ICA en tres clases
- **Alternativas:** las cinco categorías del IDEAM.
- **Razón:** solo 62 registros quedaron como Bueno y ninguno como Muy malo; el modelo no podría aprender esas clases. Clases: Bueno/Aceptable (1.011), Regular (977) y Malo (195).
- **Cambio frente al diseño:** sí; el diseño planteaba las cinco categorías.
- **Evidencia:** `src/cargar_bd.py` (CLASE_MODELO), tabla `clasificacion_ica`.

### DEC-09. Excluir las variables del ICA y los sólidos totales y disueltos
- **Razón:** usar las variables con las que se calcula el ICA haría que el modelo reprodujera la fórmula. Los sólidos totales incluyen a los SST y los disueltos se relacionan con la conductividad: en la prueba de viabilidad subían el F1 por fuga de información.
- **Evidencia:** `src/entrenar.py` (VARIABLES); modelo de control con las variables del ICA (F1 0,833) para comparar.

### DEC-10. División cronológica 1990–2015 / 2016–2025
- **Alternativas:** división aleatoria.
- **Razón:** una división aleatoria mezclaría años y daría métricas optimistas; la cronológica simula el uso real (predecir datos nuevos). Entrenamiento: 1.668 registros; prueba: 515. Los hiperparámetros se ajustan con validación cruzada temporal solo dentro del entrenamiento.
- **Evidencia:** `src/entrenar.py` (ANIO_CORTE), prueba PU-05.

### DEC-11. F1-macro como métrica principal
- **Alternativas:** exactitud (accuracy).
- **Razón:** las clases están desbalanceadas (Malo es solo 9 %); la exactitud premiaría ignorar la clase Malo. El F1-macro pesa igual las tres clases. Criterio de viabilidad propuesto: F1-macro ≥ 0,55 y mejora > 0,25 frente al modelo base.
- **Evidencia:** `docs/comparacion_modelos.csv`.

### DEC-12. Random Forest como modelo activo
- **Razón:** obtuvo el mayor F1-macro sin variables del ICA (0,587, exactitud 0,670) frente a regresión logística (0,554), árbol de decisión (0,447) y modelo base (0,199).
- **Nota:** con los datos sin corregir la regresión logística quedaba primera (0,600); la corrección de DEC-06 cambió el resultado.
- **Evidencia:** tabla `modelo` (activo = 1), `docs/comparacion_modelos.csv`.

### DEC-13. SQLite como motor de base de datos
- **Alternativas:** PostgreSQL, MySQL.
- **Razón:** proyecto individual y local; SQLite viene incluido en Python, no requiere servidor y la base se reconstruye con un script. Soporta llaves foráneas, CHECK e índices.
- **Limitación:** no maneja usuarios ni roles; el control de acceso se hace a nivel de aplicación (ver `diccionario_datos.md`, Seguridad y permisos).
- **Evidencia:** `bd/esquema.sql`, `src/cargar_bd.py`.

### DEC-14. Prototipo en Streamlit con la lógica separada
- **Alternativas:** Flask o Django con HTML propio.
- **Razón:** Streamlit permite construir la interfaz en Python con poco código, adecuado para un prototipo individual. La lógica (validar, clasificar, consultar) está en `app/servicio.py`, separada de las pantallas, para probarla con pytest sin abrir el navegador.
- **Evidencia:** `app/app.py`, `app/servicio.py`, `tests/test_prototipo.py`.

### DEC-15. Cuatro variables obligatorias en el formulario
- **Razón:** temperatura, turbiedad, alcalinidad y DBO5 son de medición común y están entre las más influyentes del modelo; las otras diez son opcionales y se imputan con la mediana, con aviso al usuario. La prueba PS-08 mostró que con solo las obligatorias el modelo acierta, pero con menos seguridad (0,49 frente a 0,79).
- **Evidencia:** `app/servicio.py` (VARIABLES), pruebas PS-05 y PS-08.

### DEC-16. No versionar la base ni los modelos; fijar versiones de librerías
- **Razón:** la base y los `.joblib` se regeneran con los scripts y cambian en cada ejecución; versionarlos llenaría el historial. Las versiones exactas en `requirements.txt` (Python 3.10.11, pandas 2.3.3, scikit-learn 1.7.2, Streamlit 1.65.0) permiten reproducir las métricas.
- **Evidencia:** `.gitignore`, `requirements.txt`.

### DEC-17. Selección de las demás variables del archivo
- **Decisión:** no usar como entrada calcio, magnesio, dureza cálcica y magnésica ni bicarbonatos; tampoco los metales traza (cadmio, cromo, níquel, plomo, cobre, zinc), los fosfatos, el nitrógeno total ni el caudal. Hierro, manganeso, sodio y potasio quedan pendientes para Trabajo de Grado II.
- **Razón:** los componentes de la dureza y la alcalinidad son redundantes con la dureza total y la alcalinidad (Spearman 0,67–0,96). En los metales traza, entre 55 % y 95 % de los valores están bajo el límite de detección y su correlación con el ICA es |ρ| ≤ 0,13. Los fosfatos y el nitrógeno total repiten la información del fósforo total y de las formas de nitrógeno (el nitrógeno total además tiene 29,4 % faltante). El caudal tiene 90,5 % faltante. Hierro, manganeso, sodio y potasio tienen correlación moderada (−0,37 a −0,47) y se probarán en la siguiente iteración.
- **Evidencia:** docs/eda/correlaciones_ica.csv, datos/procesados/banderas_censura.csv; ejecución de src/exploratorio.py.
