"""
Team tests: `ImageCodec.open` and `ImageCodec.encode`.

- `encode` can store an RGBA image as JPEG (JPEG has no alpha channel).
- `open` returns the image in a mode the operations can process (L, RGB or RGBA).

Everything runs in memory, without touching the disk or the database.
"""

from io import BytesIO

import pytest
from PIL import Image

from app.core.exceptions import InvalidFile
from app.core.imaging import ImageCodec
from app.core.operations import Brightness, Grayscale, Mirror

PROCESSABLE_MODES = {"L", "RGB", "RGBA"}


def to_bytes(img: Image.Image, fmt: str = "PNG", **save_args) -> bytes:
    buffer = BytesIO()
    img.save(buffer, format=fmt, **save_args)
    return buffer.getvalue()


def from_bytes(data: bytes) -> Image.Image:
    img = Image.open(BytesIO(data))
    img.load()
    return img


@pytest.fixture
def codec() -> ImageCodec:
    return ImageCodec()


# --- encode ------------------------------------------------------------------

def test_encode_rgba_as_jpeg(codec):
    img = Image.new("RGBA", (40, 20), (255, 0, 0, 255))

    data = codec.encode(img, "JPEG")

    result = from_bytes(data)
    assert result.format == "JPEG"
    assert result.mode == "RGB"  # the alpha channel was removed
    assert result.size == (40, 20)


def test_encode_rgba_as_jpeg_transparent_area_is_not_black(codec):
    # A fully transparent image: after removing alpha it should not become black.
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))

    result = from_bytes(codec.encode(img, "JPEG"))

    r, g, b = result.getpixel((5, 5))
    assert min(r, g, b) > 200  # white background (JPEG may vary a few levels)


def test_encode_rgba_as_png_keeps_alpha(codec):
    img = Image.new("RGBA", (10, 10), (0, 255, 0, 128))

    result = from_bytes(codec.encode(img, "PNG"))

    assert result.mode == "RGBA"
    assert result.getpixel((0, 0))[3] == 128


def test_encode_grayscale_as_jpeg_stays_single_channel(codec):
    img = Image.new("L", (10, 10), 76)

    result = from_bytes(codec.encode(img, "JPEG"))

    assert result.mode == "L"


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP", "BMP"])
def test_encode_supported_formats(codec, fmt):
    img = Image.new("RGB", (30, 20), "blue")

    data = codec.encode(img, fmt)

    info = codec.inspect(data)
    assert info.format == fmt
    assert (info.width, info.height) == (30, 20)


def test_encode_does_not_modify_input(codec):
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 100))
    copy = img.copy()

    codec.encode(img, "JPEG")

    assert img.mode == "RGBA"
    assert img.tobytes() == copy.tobytes()


# --- open --------------------------------------------------------------------

def p_with_transparency() -> bytes:
    img = Image.new("P", (10, 10), 0)
    return to_bytes(img, "PNG", transparency=0)


CASES = [
    # (description, file bytes, expected mode)
    ("rgb", to_bytes(Image.new("RGB", (10, 10), "red")), "RGB"),
    ("rgba", to_bytes(Image.new("RGBA", (10, 10), (255, 0, 0, 128))), "RGBA"),
    ("l", to_bytes(Image.new("L", (10, 10), 128)), "L"),
    ("1_bilevel", to_bytes(Image.new("1", (10, 10), 1)), "L"),
    ("la", to_bytes(Image.new("LA", (10, 10), (128, 100))), "RGBA"),
    ("p_palette", to_bytes(Image.new("RGB", (10, 10), "red").convert("P")), "RGB"),
    ("p_with_transparency", p_with_transparency(), "RGBA"),
    ("cmyk_jpeg", to_bytes(Image.new("CMYK", (10, 10), (0, 255, 255, 0)), "JPEG"), "RGB"),
]


@pytest.mark.parametrize("data, expected_mode", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_open_normalizes_mode(codec, data, expected_mode):
    img = codec.open(data)

    assert img.mode == expected_mode
    assert img.mode in PROCESSABLE_MODES
    assert img.size == (10, 10)


@pytest.mark.parametrize("data", [c[1] for c in CASES], ids=[c[0] for c in CASES])
def test_open_result_can_be_processed(codec, data):
    img = codec.open(data)

    # If the mode were not processable, these operations would fail.
    for operation in (Brightness(factor=1.5), Grayscale(), Mirror()):
        result = operation.apply(img)
        assert result.size == img.size


def test_open_garbage_raises_invalid_file(codec):
    with pytest.raises(InvalidFile):
        codec.open(b"this is not an image")


def test_open_empty_bytes_raises_invalid_file(codec):
    with pytest.raises(InvalidFile):
        codec.open(b"")


# --- round trip --------------------------------------------------------------

def test_open_then_encode_round_trip(codec):
    original = to_bytes(Image.new("RGBA", (25, 15), (10, 20, 30, 40)))

    img = codec.open(original)
    data = codec.encode(img, "JPEG")

    info = codec.inspect(data)
    assert info.format == "JPEG"
    assert (info.width, info.height) == (25, 15)
