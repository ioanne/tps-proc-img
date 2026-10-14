
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.errors import ScanNotFound
from app.repository import ScanRepository
from app.schemas import ScanOptions, ScanOut


def crear_escaneo(scan_id=None):
    """Genera metadatos válidos para un escaneo de prueba."""
    scan_id = scan_id or uuid4().hex

    return ScanOut(
        id=scan_id,
        original_name="documento.jpg",
        url=f"/media/{scan_id}.png",
        original_url=f"/media/{scan_id}-original.jpg",
        width=300,
        height=400,
        size_bytes=8,
        corners=[
            [0.0, 0.0],
            [299.0, 0.0],
            [299.0, 399.0],
            [0.0, 399.0],
        ],
        options=ScanOptions(
            color_mode="color",
            color_correction=True,
            soften_colors=0.0,
        ),
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def repositorio(tmp_path):
    """Almacenamiento temporal aislado para cada prueba."""
    return ScanRepository(storage_dir=tmp_path)


def test_guardar_escaneo(repositorio):
    escaneo = crear_escaneo()

    resultado = repositorio.save(
        escaneo,
        image_png=b"PNG_TEST",
        original_content=b"JPG_TEST",
    )

    assert resultado.id == escaneo.id
    assert (repositorio.storage_dir / f"{escaneo.id}.png").exists()
    assert (repositorio.storage_dir / f"{escaneo.id}.json").exists()
    assert (
        repositorio.storage_dir / f"{escaneo.id}-original.jpg"
    ).exists()


def test_recuperar_escaneo(repositorio):
    escaneo = crear_escaneo()
    repositorio.save(escaneo, b"PNG_TEST", b"JPG_TEST")

    recuperado = repositorio.get(escaneo.id)

    assert recuperado.id == escaneo.id
    assert recuperado.original_name == "documento.jpg"
    assert recuperado.width == 300
    assert recuperado.height == 400


def test_listar_escaneos(repositorio):
    primero = crear_escaneo()
    segundo = crear_escaneo()

    repositorio.save(primero, b"PNG_1", b"JPG_1")
    repositorio.save(segundo, b"PNG_2", b"JPG_2")

    resultados = repositorio.list()

    assert len(resultados) == 2
    assert {item.id for item in resultados} == {
        primero.id,
        segundo.id,
    }


def test_eliminar_escaneo(repositorio):
    escaneo = crear_escaneo()
    repositorio.save(escaneo, b"PNG_TEST", b"JPG_TEST")

    repositorio.delete(escaneo.id)

    assert not (repositorio.storage_dir / f"{escaneo.id}.png").exists()
    assert not (repositorio.storage_dir / f"{escaneo.id}.json").exists()
    assert not (
        repositorio.storage_dir / f"{escaneo.id}-original.jpg"
    ).exists()

    with pytest.raises(ScanNotFound):
        repositorio.get(escaneo.id)


def test_rechazar_identificador_invalido(repositorio):
    with pytest.raises(ScanNotFound):
        repositorio.get("../archivo-inexistente")

    with pytest.raises(ScanNotFound):
        repositorio.delete("../archivo-inexistente")
