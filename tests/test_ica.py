"""Prueba unitaria PU-04 del componente C3 (ica.py) · RF-03.
Valores calculados a mano con las fórmulas del IDEAM."""
import numpy as np
import pytest

from ica import categoria, i_ce, i_dqo, i_od, i_ph, i_sst


def test_PU04_subindices():
    assert i_ph(np.array([7.5]))[0] == pytest.approx(1.0)
    assert i_sst(np.array([10.0]))[0] == pytest.approx(0.99)
    assert i_dqo(np.array([15.0]))[0] == pytest.approx(0.91)
    assert i_od(np.array([90.0]))[0] == pytest.approx(0.90)
    assert i_ce(np.array([100.0]))[0] == pytest.approx(1 - 10 ** -0.58, abs=1e-3)


def test_PU04_ica_y_categoria():
    # pH 7,5 · SST 10 · DQO 15 · OD 80 % · CE 100 µS/cm
    ica = (1.0 + 0.99 + 0.91 + 0.80 + (1 - 10 ** -0.58)) / 5     # ≈ 0,887
    assert ica == pytest.approx(0.887, abs=1e-3)
    assert categoria(ica) == "Aceptable"


@pytest.mark.parametrize("valor,esperada", [
    (0.20, "Muy malo"), (0.40, "Malo"), (0.60, "Regular"), (0.80, "Aceptable"), (0.95, "Bueno")])
def test_limites_de_categoria(valor, esperada):
    assert categoria(valor) == esperada
