"""Pruebas de la lógica del prototipo (C6, C7, C9) sin abrir la interfaz.
Usan una COPIA de la base de datos para no alterar la real."""
import shutil

import pytest

import servicio as sv

pytestmark = pytest.mark.skipif(not sv.BD.exists(), reason="Primero ejecute cargar_bd.py y entrenar.py")

CASO_1 = {"temperatura": 21.2, "turbiedad": 11, "alcalinidad": 20.9, "dbo": 1.21, "color": 28,
          "dureza_total": 25.4, "fosforo_total": 0.0473, "nitrogeno_amoniacal": 0.125,
          "nitratos": 0.404, "nitritos": 0.00505, "cloruros": 4.26, "sulfatos": 12.6,
          "coliformes_fecales": 1500, "coliformes_totales": 9300}


@pytest.fixture
def bd_copia(tmp_path, monkeypatch):
    copia = tmp_path / "copia.db"
    shutil.copy(sv.BD, copia)
    monkeypatch.setattr(sv, "BD", copia)
    return copia


def test_PS01_obligatorias_vacias():
    errores = sv.validar({})
    assert len(errores) == 4 and all("obligatorio" in e for e in errores)


def test_PS02_fuera_de_rango():
    errores = sv.validar({**CASO_1, "temperatura": 80})
    assert errores == ["Temperatura: fuera de rango (15 a 35 °C)."]


def test_datos_validos_sin_errores():
    assert sv.validar(CASO_1) == []


def test_clasificar_devuelve_categoria_y_tiempo(bd_copia):
    resultado = sv.clasificar(CASO_1)
    assert resultado["categoria"] in {"Malo", "Regular", "Bueno/Aceptable"}
    assert resultado["tiempo_ms"] < 2000                                   # RF-05
    assert sum(resultado["probabilidades"].values()) == pytest.approx(1, abs=0.01)


def test_clasificar_rechaza_datos_invalidos(bd_copia):
    with pytest.raises(ValueError):
        sv.clasificar({**CASO_1, "dbo": 900})


def test_PI03_la_prediccion_queda_guardada(bd_copia):
    antes = sv.total_predicciones()
    sv.guardar_prediccion(CASO_1, sv.clasificar(CASO_1))
    assert sv.total_predicciones() == antes + 1


def test_consulta_historica(bd_copia):
    datos = sv.historico("ANTES RIO OVEJAS", 2010, 2025)
    assert len(datos) > 0 and datos["anio"].between(2010, 2025).all()
