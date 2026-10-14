"""
Image input/output. Given.

The whole core works with numpy arrays of shape (height, width, 3), dtype
uint8, in RGB order: the same order as the palettes. Careful if you use
OpenCV: its own functions to read and write files work in BGR. Here the
files are opened with Pillow, so that never happens.
"""

from dataclasses import dataclass
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from retro.exceptions import InvalidImage

# Photos are shrunk to at most this size when they are opened: the avatar has at
# most 128 pixels per side, so a 12-megapixel photo would only slow things down.
MAX_SIDE = 1024


@dataclass(frozen=True)
class Photo:
    """A photo ready to be processed."""

    format: str        # "PNG", "JPEG", "WEBP", "BMP", "GIF"… detected by content
    image: np.ndarray  # RGB uint8, upright according to its EXIF orientation

    @property
    def width(self) -> int:
        return self.image.shape[1]

    @property
    def height(self) -> int:
        return self.image.shape[0]


def read_photo(content: bytes, max_side: int = MAX_SIDE) -> Photo:
    """
    Opens the bytes of a photo with Pillow.

    - The format is detected by content, not by the file name.
    - The EXIF orientation is applied: phones store the pixels rotated and write
      in the EXIF how to display them.
    - Transparent pixels are put over a white background, and any color mode
      (P, L, CMYK…) is converted to RGB.
    - If a side is longer than `max_side`, the photo is shrunk keeping its proportions.

    Raises InvalidImage if the bytes are not an image. It does not filter
    formats: that is up to the caller.
    """
    try:
        with Image.open(BytesIO(content)) as img:
            img.load()
            fmt = img.format or ""
            rgb = _flatten(ImageOps.exif_transpose(img))
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidImage("El archivo no es una imagen válida o está dañado.") from exc
    rgb.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return Photo(format=fmt, image=np.array(rgb, dtype=np.uint8))


def _flatten(img: Image.Image) -> Image.Image:
    """Any mode → RGB, with transparency over white."""
    if img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return img.convert("RGB")


def to_pil(image: np.ndarray) -> Image.Image:
    """RGB array → Pillow RGB image."""
    return Image.fromarray(image, "RGB")


def encode_png(image: np.ndarray) -> bytes:
    """Encodes an RGB array as PNG, in memory."""
    buf = BytesIO()
    to_pil(image).save(buf, format="PNG")
    return buf.getvalue()


def count_colors(image: np.ndarray) -> int:
    """How many different colors the image has. Handy to check a palette was respected."""
    rgb = image.reshape(-1, 3).astype(np.uint32)
    return int(np.unique((rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]).size)
