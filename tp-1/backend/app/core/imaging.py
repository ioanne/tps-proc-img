"""
Conversion between bytes and images in memory.

`ImageCodec` is used by the service to:
  - inspect an uploaded file (is it an image? which format and size?),
  - open a stored file as an image ready to be processed,
  - encode the result of an operation back to bytes, in memory, before the
    storage writes it to disk.
"""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.exceptions import InvalidFile


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
        """Opens the bytes of a stored file as an image ready to be processed.

        The color mode is normalized to L, RGB or RGBA, so the operations only
        have to deal with those three.
        """
        try:
            image = Image.open(BytesIO(content))
            image.load()
        except Exception as exc:
            raise InvalidFile() from exc

        # Si ya está en uno de los 3 modos estándar, la devolvemos tal cual
        if image.mode in ("L", "RGB", "RGBA"):
            return image

        # Normalización a L, RGB o RGBA
        if image.mode == "1":
            return image.convert("L")

        if image.mode in ("LA", "PA") or (image.mode == "P" and "transparency" in image.info):
            return image.convert("RGBA")

        return image.convert("RGB")

    def encode(self, image: Image.Image, image_format: str) -> bytes:
        """Encodes `image` in `image_format`, converting its color mode if that format
        cannot store it (e.g. RGBA in JPEG)."""
        """if image_format == "JPEG" and image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        elif image.mode not in ("L", "RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.mode else "RGB")
        buffer = BytesIO()
        image.save(buffer, format=image_format)
        return buffer.getvalue()"""
        fmt = image_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"

        # JPEG no permite canales Alfa (RGBA, LA)
        if fmt == "JPEG":
            if image.mode in ("RGBA", "LA"):
                # Fondo blanco para no dejar fondo negro en áreas transparentes
                background = Image.new("RGB", image.size, (255, 255, 255))
                alpha = image.split()[-1]
                background.paste(image, mask=alpha)
                image = background
            elif image.mode != "L":
                image = image.convert("RGB")
        elif image.mode not in ("L", "RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.mode else "RGB")

        buffer = BytesIO()
        image.save(buffer, format=fmt)
        return buffer.getvalue()
