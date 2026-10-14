from pathlib import Path

import cv2
import pytest

from docscan import DocumentDetector, DocumentNotFound, Scanner, ScanOptions


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "filename",
    ["frente.png", "inclinado.png", "pers1.png"],
    #["frente.png", "inclinado.png", "pers2.jpeg", "pers1.png"],
)
def test_real_photos_detect_document(filename):
    image_path = FIXTURES_DIR / filename
    image = cv2.imread(str(image_path))

    assert image is not None, f"No se pudo cargar la imagen: {filename}"

    result = Scanner().scan(
        image,
        ScanOptions(color_correction=False),
    )

    assert result.corners.shape == (4, 2)


def test_photo_without_document_is_not_detected():
    image_path = FIXTURES_DIR / "vacio.png"
    image = cv2.imread(str(image_path))

    assert image is not None, "No se pudo cargar vacio.png"

    with pytest.raises(DocumentNotFound):
        DocumentDetector().detect(image)
