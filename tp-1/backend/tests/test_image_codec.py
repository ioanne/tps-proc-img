from io import BytesIO

import pytest
from PIL import Image

from app.core.exceptions import InvalidFile
from app.core.imaging import ImageCodec

# we are going to test ImageCodec class since it is already coded

# helper for image creation 

def image_bytes(mode: str, size=(10, 10), color=None, fmt="PNG") -> bytes:
    img = Image.new(mode, size, color)
    buffer = BytesIO()
    img.save(buffer, format=fmt)
    return buffer.getvalue()     

@pytest.fixture # give us fresh ImageCode at any use of codec as a parameter
def codec() -> ImageCodec:
    return ImageCodec()

# test inspect

def test_return_format_and_size(codec):
    data = image_bytes("RGB", size=(30, 20), color="red", fmt="PNG")
    info = codec.inspect(data)
    assert info.format == "PNG"
    assert info.width == 30
    assert info.height == 20

def test_detect_jpeg(codec):
    data = image_bytes("RGB", color="blue", fmt="JPEG")
    assert codec.inspect(data).format == "JPEG"

def test_garbage_invalid_file(codec):
    with pytest.raises(InvalidFile):
        codec.inspect(b"esto no es una imagen")

def test_empty_bytes_invalid_file(codec):
    with pytest.raises(InvalidFile):
        codec.inspect(b"")