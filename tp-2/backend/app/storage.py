"""Persistent storage for scans, their originals, and their metadata."""

import json
import re
from pathlib import Path

from app.config import MEDIA_URL, STORAGE_DIR
from app.errors import ScanNotFound
from app.schemas import ScanOut

_SCAN_ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")


def _metadata_path(scan_id: str) -> Path:
    if not _SCAN_ID_PATTERN.fullmatch(scan_id):
        raise ScanNotFound(scan_id)
    return STORAGE_DIR / f"{scan_id}.json"


def _media_path(url: str, scan_id: str) -> Path:
    prefix = f"{MEDIA_URL}/{scan_id}"
    filename = url.removeprefix(f"{MEDIA_URL}/")
    if not filename.startswith(f"{scan_id}-") and filename != f"{scan_id}.png":
        raise ValueError("La URL del archivo no corresponde al escaneo.")
    if "/" in filename or "\\" in filename or not url.startswith(prefix):
        raise ValueError("La URL del archivo no es válida.")
    return STORAGE_DIR / filename


def save_scan(scan: ScanOut, png: bytes, original: bytes) -> ScanOut:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    result_path = _media_path(scan.url, scan.id)
    original_path = _media_path(scan.original_url, scan.id)
    metadata_path = _metadata_path(scan.id)

    result_path.write_bytes(png)
    original_path.write_bytes(original)
    metadata_path.write_text(
        json.dumps(scan.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )
    return scan


def _read_scan(metadata_path: Path) -> ScanOut:
    return ScanOut.model_validate(json.loads(metadata_path.read_text(encoding="utf-8")))


def list_scans() -> list[ScanOut]:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    scans = [_read_scan(path) for path in STORAGE_DIR.glob("*.json")]
    return sorted(scans, key=lambda scan: scan.created_at, reverse=True)


def get_scan(scan_id: str) -> ScanOut:
    metadata_path = _metadata_path(scan_id)
    if not metadata_path.is_file():
        raise ScanNotFound(scan_id)
    return _read_scan(metadata_path)


def delete_scan_files(scan_id: str) -> None:
    get_scan(scan_id)
    metadata_path = _metadata_path(scan_id)
    for path in (
        STORAGE_DIR / f"{scan_id}.png",
        *STORAGE_DIR.glob(f"{scan_id}-original.*"),
        metadata_path,
    ):
        path.unlink(missing_ok=True)
