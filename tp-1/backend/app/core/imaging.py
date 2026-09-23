"""
Conversion between bytes and images in memory.

`ImageCodec` is used by the service to:
  - inspect an uploaded file (is it an image? which format and size?) [given],
  - open a stored file as an image ready to be processed [TODO (teams)],
  - encode the result of an operation back to bytes, in memory, before the
    storage writes it to disk [TODO (teams)].
"""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.exceptions import InvalidFile, NotImplementedFeature


@dataclass(frozen=True)
class ImageInfo:
    format: str  # as in Pillow's `Image.format` ("PNG", "JPEG", "GIF", ...)
    width: int
    height: int


class ImageCodec:
    def inspect(self, content: bytes) -> ImageInfo:
        """Opens `content` and returns its format (detected by content) and size.

        Raises `InvalidFile` if it cannot be opened as an image (includes empty
        content). It does NOT check the allowed formats: that is done by the service.
        """
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
                return ImageInfo(format=image.format, width=image.width, height=image.height)
        except Exception as exc:
            raise InvalidFile() from exc

    def open(self, content: bytes) -> Image.Image:
        """Opens the bytes of a stored file as an image ready to be processed."""
        raise NotImplementedFeature("Open image")

    def encode(self, image: Image.Image, image_format: str) -> bytes:
        """Encodes `image` in `image_format`, converting its color mode if that format
        cannot store it (e.g. RGBA in JPEG)."""
        raise NotImplementedFeature("Encode image")
