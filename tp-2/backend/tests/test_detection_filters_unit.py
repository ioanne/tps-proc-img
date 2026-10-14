
import cv2
import numpy as np
import pytest

from docscan.detect import detect_document
from docscan.exceptions import DocumentNotFound
from docscan.filters import (
    BWFilter,
    Color,
    GrayscaleFilter,
    SoftenColorsFilter,
)


def test_detectar_documento_rectangular():
    imagen = np.full((500, 500, 3), 40, dtype=np.uint8)

    cv2.rectangle(
        imagen, (90, 70), (410, 430),
        (245, 245, 245), -1
    )

    esquinas = np.asarray(detect_document(imagen))

    assert esquinas.shape == (4, 2)
    assert np.all(np.isfinite(esquinas))


def test_imagen_sin_documento():
    imagen = np.full((500, 500, 3), 120, dtype=np.uint8)

    with pytest.raises(DocumentNotFound):
        detect_document(imagen)


def test_filtro_escala_grises():
    imagen = np.full((60, 80, 3), 150, dtype=np.uint8)

    resultado = GrayscaleFilter().apply(imagen)

    assert resultado.shape == (60, 80)
    assert resultado.dtype == np.uint8


def test_filtro_blanco_negro():
    imagen = np.full((60, 80, 3), 150, dtype=np.uint8)

    resultado = BWFilter().apply(imagen)

    assert resultado.shape == (60, 80)
    assert set(np.unique(resultado)).issubset({0, 255})


def test_filtro_color_original():
    imagen = np.full((60, 80, 3), 150, dtype=np.uint8)

    resultado = Color().apply(imagen)

    assert np.array_equal(resultado, imagen)


def test_suavizado_factor_cero():
    imagen = np.full((60, 80, 3), (30, 80, 200), dtype=np.uint8)

    resultado = SoftenColorsFilter(0.0).apply(imagen)

    assert np.array_equal(resultado, imagen)
