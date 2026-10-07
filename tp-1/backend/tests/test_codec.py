from io import BytesIO

from PIL import Image

from app.core.imaging import ImageCodec


def test_encode_rgba_as_jpeg():
    codec =ImageCodec()
    image =Image.new("RGBA", (10, 10), (255, 0, 0, 128))

    content= codec.encode(image, "JPEG")

    result= Image.open(BytesIO(content))

    assert result.format== "JPEG"
    assert result.mode== "RGB"


def test_open_normalizes_palette_image():
    codec =ImageCodec()

    image =Image.new("P", (10, 10))
    buffer =BytesIO()
    image.save(buffer, format="PNG")

    result =codec.open(buffer.getvalue())

    assert result.mode== "RGB"