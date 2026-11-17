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
