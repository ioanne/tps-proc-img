"""
File handling: reading uploads into memory and saving, reading and deleting
files in `config.STORAGE_DIR`.

Everything that touches the disk goes through this module. It works with raw
bytes and does not know what an image is.
"""

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app import config
from app.core.exceptions import FileTooLarge

CHUNK_SIZE = 1024 * 1024

# Extension used on disk for each format (names as in Pillow's `Image.format`).
EXTENSIONS = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "BMP": ".bmp"}


def read_upload(stream: BinaryIO, max_bytes: int = config.MAX_SIZE_BYTES) -> bytes:
    """Reads an uploaded file into memory, failing as soon as it exceeds `max_bytes`."""
    buffer = bytearray()
    while chunk := stream.read(CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise FileTooLarge(max_bytes)
    return bytes(buffer)


@dataclass(frozen=True)
class StoredFile:
    """A file saved in the storage: what has to be recorded in the database."""

    file_name: str
    url: str
    size_bytes: int


class FileStorage:
    """Saves, reads and deletes files in a folder served under `media_url`."""

    def __init__(self, directory: Path | None = None, media_url: str = config.MEDIA_URL) -> None:
        self._directory = directory if directory is not None else config.STORAGE_DIR
        self._media_url = media_url
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, image_format: str) -> StoredFile:
        """Writes `content` with a unique name (UUID + extension of `image_format`)."""
        file_name = uuid.uuid4().hex + EXTENSIONS[image_format]
        self.path(file_name).write_bytes(content)
        return StoredFile(file_name=file_name, url=self.url(file_name), size_bytes=len(content))

    def read(self, file_name: str) -> bytes:
        return self.path(file_name).read_bytes()

    def delete(self, file_name: str) -> None:
        self.path(file_name).unlink(missing_ok=True)

    def path(self, file_name: str) -> Path:
        return self._directory / file_name

    def url(self, file_name: str) -> str:
        return f"{self._media_url}/{file_name}"
