from datetime import datetime
from uuid import uuid4

import app.storage as storage
from app.schemas import ScanOptions, ScanOut


def create_sample_scan():
    scan_id = uuid4().hex

    return ScanOut(
        id=scan_id,
        original_name="documento.jpg",
        url=f"/media/{scan_id}.png",
        original_url=f"/media/{scan_id}-original.jpg",
        width=100,
        height=150,
        size_bytes=1024,
        corners=[
            [10.0, 10.0],
            [90.0, 10.0],
            [90.0, 140.0],
            [10.0, 140.0],
        ],
        options=ScanOptions(
            color_mode="color",
            color_correction=False,
            soften_colors=0.0,
        ),
        created_at=datetime(2026, 10, 13, 12, 0, 0),
    )


def test_save_and_get_scan(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)
    scan = create_sample_scan()
    png = b"processed image"
    original = b"original image"

    saved = storage.save_scan(scan, png, original)
    retrieved = storage.get_scan(scan.id)

    assert saved.id == scan.id
    assert retrieved.id == scan.id
    assert retrieved.original_name == "documento.jpg"
    assert (tmp_path / f"{scan.id}.png").read_bytes() == png
    assert (tmp_path / f"{scan.id}-original.jpg").read_bytes() == original
    assert (tmp_path / f"{scan.id}.json").is_file()


def test_list_scans(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)
    scan = create_sample_scan()

    storage.save_scan(scan, b"processed image", b"original image")

    scans = storage.list_scans()

    assert len(scans) == 1
    assert scans[0].id == scan.id


def test_delete_scan_files(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)
    scan = create_sample_scan()

    storage.save_scan(scan, b"processed image", b"original image")
    storage.delete_scan_files(scan.id)

    assert not (tmp_path / f"{scan.id}.json").exists()
    assert not (tmp_path / f"{scan.id}.png").exists()
    assert not (tmp_path / f"{scan.id}-original.jpg").exists()
    assert storage.list_scans() == []
