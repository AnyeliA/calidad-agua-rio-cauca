-- Consultas de comprobación (PI-01): los resultados deben coincidir con los archivos CSV.

-- 1. Totales por tabla (esperado: 19 estaciones, 2368 muestreos, 2183 con ICA)
SELECT (SELECT COUNT(*) FROM estacion)          AS estaciones,
       (SELECT COUNT(*) FROM muestreo)          AS muestreos,
       (SELECT COUNT(*) FROM clasificacion_ica) AS con_ica;

-- 2. Distribución de categorías ICA (esperado: Regular 977, Aceptable 949, Malo 195, Bueno 62)
SELECT categoria, COUNT(*) AS registros
FROM clasificacion_ica GROUP BY categoria ORDER BY registros DESC;

-- 3. Clases para el modelo (3 clases)
SELECT clase_modelo, COUNT(*) AS registros
FROM clasificacion_ica GROUP BY clase_modelo ORDER BY registros DESC;

-- 4. Rango de años (esperado: 1990 a 2025)
SELECT MIN(anio) AS primer_anio, MAX(anio) AS ultimo_anio FROM muestreo;

-- 5. División cronológica: entrenamiento hasta 2015, prueba desde 2016
SELECT CASE WHEN m.anio <= 2015 THEN 'Entrenamiento 1990-2015' ELSE 'Prueba 2016-2025' END AS conjunto,
       COUNT(*) AS registros_con_ica
FROM muestreo m JOIN clasificacion_ica c ON c.id_muestreo = m.id_muestreo
GROUP BY conjunto;

-- 6. Integridad referencial (esperado: 0 muestreos sin estación)
SELECT COUNT(*) AS muestreos_sin_estacion
FROM muestreo m LEFT JOIN estacion e ON e.id_estacion = m.id_estacion
WHERE e.id_estacion IS NULL;

-- 7. Muestreos por estación cercana a Puerto Tejada
SELECT e.nombre, COUNT(*) AS muestreos, ROUND(AVG(c.ica), 3) AS ica_promedio
FROM estacion e
JOIN muestreo m ON m.id_estacion = e.id_estacion
LEFT JOIN clasificacion_ica c ON c.id_muestreo = m.id_muestreo
WHERE e.cercana_puerto_tejada = 1
GROUP BY e.nombre ORDER BY e.nombre;
