import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import MEDIA_URL, STORAGE_DIR
from app.errors import ScanNotFound
from app.schemas import ScanOptions, ScanOut
from app.uploads import Upload
from docscan.imageio import encode_png
from docscan.scanner import ScanResult

ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


class ScanRepository:
    """Manages file persistence for scans without a database."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or STORAGE_DIR

    def _get_dir(self) -> Path:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        return self.storage_dir

    def _validate_id(self, scan_id: str) -> None:
        if not ID_PATTERN.match(scan_id):
            raise ScanNotFound(scan_id)

    def save(self, upload: Upload, result: ScanResult, options: ScanOptions) -> ScanOut:
        scan_id = uuid4().hex
        st_dir = self._get_dir()

        ext = upload.photo.format.lower()
        if ext == "jpeg":
            ext = "jpg"

        orig_filename = f"{scan_id}-original.{ext}"
        orig_path = st_dir / orig_filename
        orig_path.write_bytes(upload.content)

        scan_png_bytes = encode_png(result.image)
        scan_filename = f"{scan_id}.png"
        scan_path = st_dir / scan_filename
        scan_path.write_bytes(scan_png_bytes)

        height, width = result.image.shape[:2]
        scan_out = ScanOut(
            id=scan_id,
            original_name=upload.name,
            url=f"{MEDIA_URL}/{scan_filename}",
            original_url=f"{MEDIA_URL}/{orig_filename}",
            width=width,
            height=height,
            size_bytes=len(scan_png_bytes),
            corners=[[float(pt[0]), float(pt[1])] for pt in result.corners],
            options=options,
            created_at=datetime.now(timezone.utc),
        )

        json_path = st_dir / f"{scan_id}.json"
        json_path.write_text(scan_out.model_dump_json(), encoding="utf-8")

        return scan_out

    def get(self, scan_id: str) -> ScanOut:
        self._validate_id(scan_id)
        json_path = self._get_dir() / f"{scan_id}.json"
        if not json_path.is_file():
            raise ScanNotFound(scan_id)

        try:
            data = json_path.read_text(encoding="utf-8")
            return ScanOut.model_validate_json(data)
        except Exception:
            raise ScanNotFound(scan_id)

    def list(self) -> list[ScanOut]:
        st_dir = self._get_dir()
        scans: list[ScanOut] = []

        for json_path in st_dir.glob("*.json"):
            try:
                data = json_path.read_text(encoding="utf-8")
                scans.append(ScanOut.model_validate_json(data))
            except Exception:
                continue

        scans.sort(key=lambda s: s.created_at, reverse=True)
        return scans

    def delete(self, scan_id: str) -> None:
        self._validate_id(scan_id)
        st_dir = self._get_dir()

        json_path = st_dir / f"{scan_id}.json"
        if not json_path.is_file():
            raise ScanNotFound(scan_id)

        for path in st_dir.glob(f"{scan_id}*"):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass