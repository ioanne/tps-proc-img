
import numpy as np
import pytest

from docscan.perspective import PerspectiveCorrector


def test_perspectiva_rectangulo():
    """La corrección debe conservar las dimensiones de un rectángulo."""
    imagen = np.zeros((100, 200, 3), dtype=np.uint8)

    esquinas = np.array([
        [0, 0],
        [199, 0],
        [199, 99],
        [0, 99],
    ], dtype=np.float32)

    resultado = PerspectiveCorrector().correct(imagen, esquinas)

    assert resultado.shape == (99, 199, 3)
    assert resultado.dtype == np.uint8


def test_perspectiva_conserva_color():
    """La transformación debe conservar un color uniforme."""
    imagen = np.full((100, 200, 3), 150, dtype=np.uint8)

    esquinas = np.array([
        [0, 0],
        [199, 0],
        [199, 99],
        [0, 99],
    ], dtype=np.float32)

    resultado = PerspectiveCorrector().correct(imagen, esquinas)

    assert np.all(resultado == 150)


def test_perspectiva_documento_degenerado():
    """Un documento sin superficie válida debe rechazarse."""
    imagen = np.zeros((100, 100, 3), dtype=np.uint8)

    esquinas = np.array([
        [10, 10],
        [10, 10],
        [10, 10],
        [10, 10],
    ], dtype=np.float32)

    with pytest.raises(ValueError):
        PerspectiveCorrector().correct(imagen, esquinas)
