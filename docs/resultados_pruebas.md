# Resultados de pruebas del prototipo

Modelo: random_forest · versión 20261117-1633 · F1-macro 0,587

| Fecha | Prueba | Datos | Esperado | Obtenido | ¿Pasa? |
|---|---|---|---|---|---|
| 2026-11-17 | PS-03 Caso 1 | Antes Río Ovejas, 2023-07-03 | Bueno/Aceptable | Bueno/Aceptable (326,5 ms) | Sí |
| 2026-11-17 | PI-03 | Caso 1 | Predicción guardada en BD | Predicción n.º 1 guardada | Sí |
| 2026-11-17 | PS-03 Caso 2 | Paso de la Torre, 2023-06-21 | Regular |  |  |
| 2026-11-17 | PS-03 Caso 3 | Anacaro, 2021-03-17 | Malo |  |  |
| 2026-11-17 | Caso 4 | Puente La Virginia, 2019-10-23 | Regular (el modelo puede fallar) |  |  |
| 2026-11-17 | PS-01 Caso 5 | Formulario vacío | 4 errores "es obligatorio" |  |  |
| 2026-11-17 | PS-02 Caso 6 | Temperatura 80 | Error fuera de rango |  |  |
| 2026-11-17 | Caso 7 | Turbiedad -5, DBO 900 | Dos errores de rango |  |  |
| 2026-11-17 | Caso 8 | Solo 4 obligatorias | Clasifica + aviso de mediana |  |  |
| 2026-11-17 | PS-04 | Página Modelo y métricas | Muestra métricas, matriz, importancia y limitaciones |  |  |
