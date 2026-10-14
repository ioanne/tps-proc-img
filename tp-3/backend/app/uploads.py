"""
Reading and validation of an uploaded photo. Given.

Validated in this order:

1. larger than config.MAX_UPLOAD_BYTES  → 413 FILE_TOO_LARGE
2. cannot be opened as an image         → 400 INVALID_FILE (InvalidImage, from retro)
3. format not in config.ALLOWED_FORMATS → 400 UNSUPPORTED_FORMAT
"""

from dataclasses import dataclass

from fastapi import UploadFile

from app.config import ALLOWED_FORMATS, MAX_UPLOAD_BYTES
from app.errors import ApiError
from retro import Photo, read_photo


@dataclass(frozen=True)
class Upload:
    name: str     # file name sent by the user
    photo: Photo  # format + upright RGB image, ready for the core


async def read_upload(file: UploadFile) -> Upload:
    # Reads at most one byte more than the limit, so a huge file is not loaded whole.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ApiError(413, "FILE_TOO_LARGE", f"La foto supera el máximo de {limit_mb} MB.")

    photo = read_photo(content)
    if photo.format not in ALLOWED_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_FORMATS))
        raise ApiError(400, "UNSUPPORTED_FORMAT",
                       f"El formato {photo.format or 'desconocido'} no está soportado. Usá {allowed}.")
    return Upload(name=file.filename or "photo", photo=photo)
