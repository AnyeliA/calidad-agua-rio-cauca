# Bitácora del proyecto

## 2026-11-12
- Hecho: repositorio creado; instalación de Python 3.10 y librerías; ejecución de limpieza.py e ica.py.
- Resultado: 2.368 registros, 168 correcciones registradas, 2.183 registros con ICA calculable.
- Defecto encontrado: con pandas 2.3 los años mal digitados (1193, 1194, 1290) quedaban sin fecha en lugar de corregirse.
- Corrección: el año se lee como texto y se corrige antes de convertir la fecha.
- Decisión: se conservan todos los registros; solo se excluyen del modelo los 185 sin ICA.
- Siguiente paso: crear la base de datos.

## 2026-11-17
- Hecho: base de datos SQLite (6 tablas) y script de entrenamiento.
- Resultado: comprobaciones de la BD correctas (19 estaciones, 2.368 muestreos, 2.183 con ICA).
  Modelo activo: regresión logística, F1-macro 0,600 vs. 0,199 del modelo base.
  Modelo de control (con variables ICA): F1-macro 0,823.
- Decisión: excluir de Git la BD y los modelos .joblib porque se regeneran con los scripts.
- Limitación detectada: la clase "Malo" (30 casos de prueba) tiene precisión baja (0,31).
- Siguiente paso: prototipo Streamlit.

- Defecto encontrado: en 2022 los coliformes estaban en las columnas de nitritos/nitratos (57 registros)
  y en 2001-2005 los nitritos venían en µg/L (273 registros). Se corrigió en limpieza.py; pendiente confirmar con la CVC.
- Resultado: con datos corregidos el modelo activo es Random Forest, F1-macro 0,587 (antes regresión logística 0,600
  con datos erróneos). Control con variables ICA: 0,833. Modelo base: 0,199.
- Variables más importantes: alcalinidad, turbiedad, fósforo total, sulfatos.
- Decisión: fijar versiones de librerías en requirements.txt para reproducibilidad.

## 2026-11-25
- Hecho: análisis exploratorio y de calidad de los datos (src/exploratorio.py, docs/eda/), fases 2 y 3 de CRISP-DM.
- Resultado: el ICA baja a lo largo del río (mediana 0,81–0,86 aguas arriba, 0,58–0,71 aguas abajo de Cali);
  la clase Malo bajó de 15 % (1990–1994) a menos de 5 % (2020–2025); alcalinidad, dureza, fósforo y DBO5
  son las variables más correlacionadas con el ICA (−0,51 a −0,57).
- Decisión: DEC-17, selección de las demás variables del archivo. Se versiona datos_con_ica.csv como dataset preparado.
- Organización del repositorio: .gitignore para temporales de Python; se eliminan copias sobrantes.
- Siguiente paso: bloque C (modelado y evaluación).
