"""Pruebas de integración PI-01, PI-02 y unitaria PU-05 (componentes C2, C4, C5).
Requieren haber ejecutado cargar_bd.py y entrenar.py."""
import sqlite3

import pytest

from entrenar import ANIO_CORTE, BD, leer_datos

pytestmark = pytest.mark.skipif(not BD.exists(), reason="Primero ejecute cargar_bd.py y entrenar.py")


def consulta(sql):
    with sqlite3.connect(BD) as con:
        return con.execute(sql).fetchone()


def test_PI01_conteos_de_la_base():
    assert consulta("SELECT COUNT(*) FROM estacion")[0] == 19
    assert consulta("SELECT COUNT(*) FROM muestreo")[0] == 2368
    assert consulta("SELECT COUNT(*) FROM clasificacion_ica")[0] == 2183


def test_PI01_integridad_referencial():
    sin_estacion = consulta("SELECT COUNT(*) FROM muestreo m LEFT JOIN estacion e "
                            "ON e.id_estacion = m.id_estacion WHERE e.id_estacion IS NULL")[0]
    assert sin_estacion == 0


def test_PI01_restriccion_check_rechaza_ph_imposible():
    with sqlite3.connect(":memory:") as con:
        con.executescript(BD.parent.joinpath("esquema.sql").read_text(encoding="utf-8"))
        con.execute("INSERT INTO estacion (nombre) VALUES ('PRUEBA')")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO muestreo (id_muestreo, id_estacion, fecha, anio, mes, ph) "
                        "VALUES (1, 1, '2020-01-01', 2020, 1, 14)")


def test_PI02_hay_un_modelo_activo_con_metricas():
    activos, f1 = consulta("SELECT COUNT(*), MAX(f1_macro) FROM modelo WHERE activo = 1")
    assert activos == 1 and 0 < f1 <= 1


def test_PU05_entrenamiento_y_prueba_sin_cruce():
    datos = leer_datos()
    entrenamiento = set(datos[datos.anio <= ANIO_CORTE].id_muestreo)
    prueba = set(datos[datos.anio > ANIO_CORTE].id_muestreo)
    assert entrenamiento and prueba and entrenamiento.isdisjoint(prueba)


def test_modelo_supera_al_modelo_base():
    base = consulta("SELECT f1_macro FROM modelo WHERE nombre = 'base_mayoritaria' "
                    "ORDER BY id_modelo DESC LIMIT 1")[0]
    activo = consulta("SELECT f1_macro FROM modelo WHERE activo = 1")[0]
    assert activo > base
