# Registro de aprobación del modelo (fase 5 de CRISP-DM)

| Campo | Contenido |
|---|---|
| Fecha | 26 de noviembre de 2026 |
| Modelo aprobado | Regresión logística multinomial, C = 10, pesos de clase balanceados |
| Versión | 20261126-0000 (`modelos/regresion_logistica_20261126-0000.joblib`) |
| Datos | Entrenamiento: 1.668 muestreos (1990–2015). Prueba: 515 muestreos (2016–2025). 14 variables de entrada, sin las variables del ICA |
| Resultados | F1-macro 0,636 en validación cruzada temporal (4 bloques); 0,554 en prueba; exactitud 0,631 |
| Criterios cumplidos | F1-macro ≥ 0,55; mejora frente al modelo base (0,199) > 0,25; sin fuga de información; semilla fija (42) |
| Condiciones de uso | Herramienta de apoyo: no reemplaza el ICA oficial. Las clasificaciones "Malo" deben confirmarse con laboratorio (precisión 0,21) |
| Decisión | Aprobado como versión preliminar para el prototipo. Selección definitiva en Trabajo de Grado II (OE4) |
| Responsable | Anyeli Tatiana Angulo Paz, estudiante |
| Revisión | Pendiente del visto bueno de la docente de Trabajo de Grado I |

Evidencia: `docs/comparacion_modelos.csv`, `docs/registro_experimentos.csv`, `docs/reporte_por_clase.csv`, `docs/matriz_confusion.csv`, `docs/importancia_variables.csv`, decisión DEC-18 en `docs/decisiones.md`.
