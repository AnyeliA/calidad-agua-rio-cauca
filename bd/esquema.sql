-- =====================================================================
-- Base de datos: calidad del agua del río Cauca (CVC)
-- Componente C2 · Requisito RF-02 · Motor: SQLite 3
-- Se crea desde cero con:  py src\cargar_bd.py
-- =====================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS prediccion;
DROP TABLE IF EXISTS modelo;
DROP TABLE IF EXISTS clasificacion_ica;
DROP TABLE IF EXISTS muestreo;
DROP TABLE IF EXISTS estacion;
DROP TABLE IF EXISTS registro_carga;

-- ---------------------------------------------------------------------
-- 1. Estaciones de monitoreo de la CVC
-- ---------------------------------------------------------------------
CREATE TABLE estacion (
    id_estacion            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                 TEXT    NOT NULL UNIQUE,
    cercana_puerto_tejada  INTEGER NOT NULL DEFAULT 0
                           CHECK (cercana_puerto_tejada IN (0, 1))
);

-- ---------------------------------------------------------------------
-- 2. Muestreos: una fila por estación y fecha, con las variables depuradas
--    Los valores "<LD" ya vienen como LD x 0,5 (ver limpieza.py)
-- ---------------------------------------------------------------------
CREATE TABLE muestreo (
    id_muestreo          INTEGER PRIMARY KEY,
    id_estacion          INTEGER NOT NULL REFERENCES estacion(id_estacion),
    fecha                TEXT    NOT NULL,                 -- AAAA-MM-DD
    anio                 INTEGER NOT NULL CHECK (anio BETWEEN 1990 AND 2100),
    mes                  INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    duplicado_fecha_estacion INTEGER NOT NULL DEFAULT 0 CHECK (duplicado_fecha_estacion IN (0, 1)),
    -- Variables del ICA (5 variables IDEAM)
    ph                   REAL CHECK (ph IS NULL OR ph BETWEEN 4 AND 10),
    od                   REAL CHECK (od IS NULL OR od BETWEEN 0 AND 15),             -- mg O2/l
    sst                  REAL CHECK (sst IS NULL OR sst >= 0),                       -- mg/l
    dqo                  REAL CHECK (dqo IS NULL OR dqo >= 0),                       -- mg O2/l
    conductividad        REAL CHECK (conductividad IS NULL OR conductividad BETWEEN 10 AND 2000), -- µS/cm
    -- Otras variables fisicoquímicas y microbiológicas
    temperatura          REAL CHECK (temperatura IS NULL OR temperatura BETWEEN 15 AND 35), -- °C
    color                REAL, turbiedad REAL, solidos_totales REAL, solidos_disueltos REAL,
    dbo                  REAL CHECK (dbo IS NULL OR dbo >= 0),
    dureza_total REAL, dureza_calcica REAL, dureza_magnesica REAL, calcio REAL, magnesio REAL,
    alcalinidad REAL, bicarbonatos REAL, hierro_total REAL, manganeso_total REAL,
    sodio_total REAL, potasio_total REAL, cobre_total REAL, zinc_total REAL,
    nitrogeno_total REAL, nitrogeno_amoniacal REAL, nitritos REAL, nitratos REAL,
    cloruros REAL, fosforo_total REAL, fosfatos REAL, sulfatos REAL,
    cadmio_total REAL, cromo_total REAL, niquel_total REAL, plomo_total REAL,
    coliformes_totales REAL, coliformes_fecales REAL, caudal REAL
);
CREATE INDEX idx_muestreo_estacion_fecha ON muestreo (id_estacion, fecha);
CREATE INDEX idx_muestreo_anio ON muestreo (anio);

-- ---------------------------------------------------------------------
-- 3. Clasificación ICA (variable objetivo) · RF-03
-- ---------------------------------------------------------------------
CREATE TABLE clasificacion_ica (
    id_muestreo    INTEGER PRIMARY KEY REFERENCES muestreo(id_muestreo) ON DELETE CASCADE,
    od_pct_sat     REAL,
    i_od REAL, i_sst REAL, i_dqo REAL, i_ce REAL, i_ph REAL,
    ica            REAL NOT NULL CHECK (ica BETWEEN 0 AND 1),
    categoria      TEXT NOT NULL CHECK (categoria IN ('Muy malo','Malo','Regular','Aceptable','Bueno')),
    clase_modelo   TEXT NOT NULL CHECK (clase_modelo IN ('Malo','Regular','Bueno/Aceptable')),
    metodo         TEXT NOT NULL DEFAULT 'ICA IDEAM 5 variables'
);
CREATE INDEX idx_clasificacion_clase ON clasificacion_ica (clase_modelo);

-- ---------------------------------------------------------------------
-- 4. Modelos entrenados (versionado y métricas) · C5 · RNF-02, RNF-04
-- ---------------------------------------------------------------------
CREATE TABLE modelo (
    id_modelo            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre               TEXT NOT NULL,
    algoritmo            TEXT NOT NULL,
    version              TEXT NOT NULL,
    fecha_entrenamiento  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    periodo_entrenamiento TEXT NOT NULL,      -- ej. '1990-2015'
    periodo_prueba       TEXT NOT NULL,       -- ej. '2016-2025'
    variables_entrada    TEXT NOT NULL,       -- lista separada por comas
    parametros           TEXT,                -- JSON
    accuracy             REAL CHECK (accuracy IS NULL OR accuracy BETWEEN 0 AND 1),
    precision_macro      REAL CHECK (precision_macro IS NULL OR precision_macro BETWEEN 0 AND 1),
    recall_macro         REAL CHECK (recall_macro IS NULL OR recall_macro BETWEEN 0 AND 1),
    f1_macro             REAL CHECK (f1_macro IS NULL OR f1_macro BETWEEN 0 AND 1),
    ruta_archivo         TEXT NOT NULL,
    es_control           INTEGER NOT NULL DEFAULT 0 CHECK (es_control IN (0, 1)),
    activo               INTEGER NOT NULL DEFAULT 0 CHECK (activo IN (0, 1)),
    UNIQUE (nombre, version)
);

-- ---------------------------------------------------------------------
-- 5. Predicciones hechas desde el prototipo · C7 · RF-05
-- ---------------------------------------------------------------------
CREATE TABLE prediccion (
    id_prediccion        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_modelo            INTEGER NOT NULL REFERENCES modelo(id_modelo),
    fecha_hora           TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    entradas             TEXT NOT NULL,       -- JSON con los valores ingresados
    categoria_predicha   TEXT NOT NULL CHECK (categoria_predicha IN ('Malo','Regular','Bueno/Aceptable')),
    tiempo_respuesta_ms  REAL
);
CREATE INDEX idx_prediccion_modelo ON prediccion (id_modelo);

-- ---------------------------------------------------------------------
-- 6. Registro de cargas (trazabilidad de la fuente) · RNF-04
-- ---------------------------------------------------------------------
CREATE TABLE registro_carga (
    id_carga           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    archivo_origen     TEXT NOT NULL,
    registros_cargados INTEGER NOT NULL,
    registros_con_ica  INTEGER NOT NULL,
    observacion        TEXT
);
