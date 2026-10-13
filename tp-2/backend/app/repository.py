import re
from datetime import datetime
from uuid import uuid4

import numpy as np

from app.config import MEDIA_URL, STORAGE_DIR
from app.errors import ScanNotFound
from app.schemas import ScanOptions, ScanOut
from app.uploads import Upload
from docscan.imageio import encode_png


class ScanRepository:
    def save(
        self,
        upload: Upload,
        image: np.ndarray,
        corners: list[tuple[float, float]],
        options: ScanOptions,
    ) -> ScanOut:
        scan_id = uuid4().hex
        image_bytes = encode_png(image)

        extensions = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WEBP": ".webp",
            "BMP": ".bmp",
        }
        original_extension = extensions[upload.photo.format]

        scan = ScanOut(
            id=scan_id,
            original_name=upload.name,
            url=f"{MEDIA_URL}/{scan_id}.png",
            original_url=f"{MEDIA_URL}/{scan_id}-original{original_extension}",
            width=image.shape[1],
            height=image.shape[0],
            size_bytes=len(image_bytes),
            corners=[list(point) for point in corners],
            options=options,
            created_at=datetime.now(),
        )

        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        (STORAGE_DIR / f"{scan_id}.png").write_bytes(image_bytes)
        (STORAGE_DIR / f"{scan_id}-original{original_extension}").write_bytes(upload.content)
        (STORAGE_DIR / f"{scan_id}.json").write_text(
            scan.model_dump_json(),
            encoding="utf-8",
        )

        return scan

    def get(self, scan_id: str) -> ScanOut:
        if re.fullmatch(r"[0-9a-f]{32}", scan_id) is None:
            raise ScanNotFound(scan_id)

        metadata_path = STORAGE_DIR / f"{scan_id}.json"
        if not metadata_path.is_file():
            raise ScanNotFound(scan_id)

        return ScanOut.model_validate_json(
            metadata_path.read_text(encoding="utf-8")
        )

    def list(self) -> list[ScanOut]:
        metadata_files = STORAGE_DIR.glob("*.json")
        scans = [
            ScanOut.model_validate_json(path.read_text(encoding="utf-8"))
            for path in metadata_files
        ]
        return sorted(scans, key=lambda scan: scan.created_at, reverse=True)

    def delete(self, scan_id: str) -> None:
        scan = self.get(scan_id)
        original_filename = scan.original_url.rsplit("/", 1)[-1]

        (STORAGE_DIR / f"{scan_id}.png").unlink()
        (STORAGE_DIR / original_filename).unlink()
        (STORAGE_DIR / f"{scan_id}.json").unlink()