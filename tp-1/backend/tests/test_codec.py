from io import BytesIO

from PIL import Image

from app.core.imaging import ImageCodec, pil_to_cv2, cv2_to_pil


def test_encode_rgba_as_jpeg_succeeds():
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))

    data = ImageCodec().encode(img, "JPEG")

    assert isinstance(data, bytes)
    assert len(data) > 0


def test_open_returns_processable_mode():
    buf = BytesIO()
    Image.new("RGB", (10, 10)).save(buf, "PNG")

    result = ImageCodec().open(buf.getvalue())

    assert result.mode in ("L", "RGB", "RGBA")


def test_pil_cv2_roundtrip_preserves_pixels():
    img = Image.new("RGB", (4, 4), (100, 150, 200))

    roundtrip = cv2_to_pil(pil_to_cv2(img), "RGB")

    assert roundtrip.getpixel((0, 0)) == (100, 150, 200)


def test_pil_cv2_rgba_roundtrip():
    img = Image.new("RGBA", (4, 4), (100, 150, 200, 128))

    roundtrip = cv2_to_pil(pil_to_cv2(img), "RGBA")

    assert roundtrip.getpixel((0, 0)) == (100, 150, 200, 128)