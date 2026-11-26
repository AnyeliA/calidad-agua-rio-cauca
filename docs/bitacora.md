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

## 2026-11-18
- Hecho: prototipo Streamlit con clasificación de una muestra, métricas del modelo e histórico (RF-04 a RF-07).
- Hecho: pruebas del prototipo con muestreos reales de la CVC y fichas con capturas (docs/Pruebas_prototipo_calidad_agua.docx).
- Hecho: 27 pruebas automáticas con pytest (limpieza, ICA, base de datos, modelo y prototipo): 27 passed.
- Hecho: diccionario de datos y permisos de la base (docs/diccionario_datos.md).
- Hecho: registro de decisiones técnicas DEC-01 a DEC-16 (docs/decisiones.md).
- Siguiente paso: diseño del sistema.

## 2026-11-21
- Hecho: paquete de diseño (OE2) en docs/diseno: diagrama de arquitectura en tres capas, modelo entidad-relación
  de las 6 tablas y diagrama de secuencia de la clasificación de una muestra.
- Siguiente paso: definir la metodología con la docente.

## 2026-11-23
- Hecho: la docente Maribel Liliana Díaz Yunda aprobó CRISP-DM como metodología, con la condición de cumplir todos
  los entregables de sus seis fases y los componentes de ingeniería de software (evidencia en docs/evidencias).
- Hecho: en el documento de trabajo de grado se completaron referencias, capítulo 3 (Método, con la aplicación de
  CRISP-DM), alcance, estudio de viabilidad, plan de trabajo, criterios de éxito y capítulo 4 (Resultados).
- Hecho: tablero de Trello y hoja de seguimiento de entregables por fase; entrega estimada: primera semana de diciembre.
- Siguiente paso: informe exploratorio y de calidad de los datos (fases 2 y 3).

## 2026-11-25
- Hecho: análisis exploratorio y de calidad de los datos (src/exploratorio.py, docs/eda/), fases 2 y 3 de CRISP-DM.
- Resultado: el ICA baja a lo largo del río (mediana 0,81–0,86 aguas arriba, 0,58–0,71 aguas abajo de Cali);
  la clase Malo bajó de 15 % (1990–1994) a menos de 5 % (2020–2025); alcalinidad, dureza, fósforo y DBO5
  son las variables más correlacionadas con el ICA (−0,51 a −0,57).
- Decisión: DEC-17, selección de las demás variables del archivo. Se versiona datos_con_ica.csv como dataset preparado.
- Organización del repositorio: .gitignore para temporales de Python; se eliminan copias sobrantes.
- Siguiente paso: bloque C (modelado y evaluación).
- Hecho: evidencia en PDF de la aprobación de la metodología (docs/evidencias).
- En curso: sección 4.1 del documento con los entregables de las fases 2 y 3 (inventario de fuentes, exploración,
  calidad, selección y transformación de los datos).
- Siguiente paso: bloque C, fases 4 y 5 (selección de técnicas, diseño experimental, registro de experimentos,
  evaluación, cumplimiento de objetivos y aprobación del modelo).
