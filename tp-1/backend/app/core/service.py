"""
Use cases of the application: upload, list, get, delete and edit images.

`ImageService` coordinates the other pieces and holds no logic of its own about
pixels, files or SQL:
  - `ImageDAL`     reads and writes the records (`app/dal.py`),
  - `FileStorage`  reads and writes the files (`core/storage.py`),
  - `ImageCodec`   converts between bytes and images (`core/imaging.py`),
  - `Operation`    transforms an image (`core/operations.py`).
"""

from typing import BinaryIO

from app import config
from app.core.exceptions import ImageNotFound, UnsupportedFormat
from app.core.imaging import ImageCodec
from app.core.operations import Operation
from app.core.storage import FileStorage, read_upload
from app.dal import ImageDAL
from app.models import ImageRecord


class ImageService:
    def __init__(self, dal: ImageDAL, storage: FileStorage, codec: ImageCodec) -> None:
        self._dal = dal
        self._storage = storage
        self._codec = codec

    def upload(self, original_name: str, stream: BinaryIO) -> ImageRecord:
        """Validates (size -> is an image -> allowed format), saves the file as received
        and records it."""
        content = read_upload(stream, config.MAX_SIZE_BYTES)
        info = self._codec.inspect(content)
        if info.format not in config.ALLOWED_FORMATS:
            raise UnsupportedFormat(info.format)
        stored = self._storage.save(content, info.format)
        return self._dal.create(
            original_name=original_name,
            file_name=stored.file_name,
            url=stored.url,
            width=info.width,
            height=info.height,
            format=info.format,
            size_bytes=stored.size_bytes,
        )

    def list(self) -> list[ImageRecord]:
        return self._dal.list()

    def get(self, image_id: int) -> ImageRecord:
        record = self._dal.get(image_id)
        if record is None:
            raise ImageNotFound(image_id)
        return record

    def delete(self, image_id: int) -> None:
        record = self.get(image_id)
        self._dal.delete(record)
        self._storage.delete(record.file_name)

    def apply(self, image_id: int, operation: Operation) -> ImageRecord:
        """Applies `operation` to the image `image_id` and records the result as a new image."""
        source = self.get(image_id)
        image = self._codec.open(self._storage.read(source.file_name))
        content = self._codec.encode(operation.apply(image), source.format)
        info = self._codec.inspect(content)
        stored = self._storage.save(content, source.format)
        return self._dal.create(
            original_name=source.original_name,
            file_name=stored.file_name,
            url=stored.url,
            width=info.width,
            height=info.height,
            format=source.format,
            size_bytes=stored.size_bytes,
            operation=operation.name,
            parameters=operation.parameters,
            source_id=source.id,
        )
