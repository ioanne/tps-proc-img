from io import BytesIO

import pytest
from PIL import Image

from app.core.exceptions import InvalidParameters
from app.core.imaging import ImageCodec
from app.core.operations import (
    Blur,
    Brightness,
    Contrast,
    Edges,
    Grayscale,
    Mirror,
    Operation,
    Resize,
    Rotation,
    Saturation,
    Sharpness,
)

RED, BLUE, GREEN, WHITE = (255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 255)
GRAY = (128, 128, 128)


def quadrants(width: int = 40, height: int = 20, mode: str = "RGB") -> Image.Image:
    image = Image.new("RGB", (width, height))
    mx, my = width // 2, height // 2
    image.paste(RED, (0, 0, mx, my))
    image.paste(BLUE, (mx, 0, width, my))
    image.paste(GREEN, (0, my, mx, height))
    image.paste(WHITE, (mx, my, width, height))
    if mode == "RGBA":
        image.putalpha(128)
        return image
    return image.convert(mode)


def checkerboard(side: int = 32) -> Image.Image:
    image = Image.new("L", (side, side))
    image.putdata([255 if (x + y) % 2 else 0 for y in range(side) for x in range(side)])
    return image.convert("RGB")


def to_bytes(image: Image.Image, fmt: str = "PNG") -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


ALL_OPERATIONS = [
    Brightness(factor=1.5),
    Contrast(factor=2),
    Saturation(factor=0),
    Sharpness(factor=2),
    Grayscale(),
    Blur(method="median", kernel_size=3),
    Edges(),
    Rotation(angle=30),
    Mirror(direction="vertical"),
    Resize(width=10),
]


@pytest.mark.parametrize("mode", ["L", "RGB", "RGBA"])
@pytest.mark.parametrize("operation", ALL_OPERATIONS, ids=lambda operation: operation.name)
def test_apply_returns_a_new_image_and_keeps_the_source(operation: Operation, mode: str) -> None:
    source = quadrants(mode=mode)
    before = source.tobytes()
    result = operation.apply(source)
    assert result is not source
    assert source.tobytes() == before


def test_parameters_include_the_defaults() -> None:
    assert Resize(width=50).parameters == {"width": 50, "height": None, "keep_aspect_ratio": True}
    assert Blur(kernel_size=3).parameters == {"method": "gaussian", "kernel_size": 3}
    assert Grayscale().parameters == {}


def test_brightness_zero_gives_black() -> None:
    assert Brightness(factor=0).apply(quadrants()).getextrema() == ((0, 0), (0, 0), (0, 0))


def test_brightness_scales_the_gray() -> None:
    result = Brightness(factor=1.5).apply(Image.new("RGB", (4, 4), GRAY))
    assert result.getpixel((1, 1)) == (192, 192, 192)


def test_brightness_keeps_the_alpha_channel() -> None:
    result = Brightness(factor=0.5).apply(quadrants(mode="RGBA"))
    assert result.mode == "RGBA"
    assert result.getchannel("A").getextrema() == (128, 128)


def test_contrast_zero_gives_a_uniform_image() -> None:
    assert all(hi - lo <= 2 for lo, hi in Contrast(factor=0).apply(quadrants()).getextrema())


def test_contrast_increases_the_difference() -> None:
    image = Image.new("RGB", (20, 10), (100, 100, 100))
    image.paste((150, 150, 150), (10, 0, 20, 10))
    result = Contrast(factor=2).apply(image)
    assert result.getpixel((15, 5))[0] - result.getpixel((5, 5))[0] > 50


def test_saturation_zero_removes_the_color() -> None:
    result = Saturation(factor=0).apply(quadrants())
    assert result.mode == "RGB"
    r, g, b = result.getpixel((5, 5))
    assert r == g == b


def test_saturation_keeps_the_alpha_channel() -> None:
    result = Saturation(factor=2).apply(quadrants(mode="RGBA"))
    assert result.mode == "RGBA"
    assert result.getchannel("A").getextrema() == (128, 128)


def test_sharpness_one_does_not_change() -> None:
    board = checkerboard()
    assert Sharpness(factor=1).apply(board).tobytes() == board.tobytes()


def test_sharpness_zero_smooths() -> None:
    lo, hi = (
        Sharpness(factor=0).apply(checkerboard()).convert("L").crop((4, 4, 28, 28)).getextrema()
    )
    assert hi - lo < 255


def test_grayscale_uses_the_luminance() -> None:
    result = Grayscale().apply(quadrants())
    assert result.mode == "L"
    assert result.getpixel((5, 5)) == 76
    assert result.getpixel((35, 15)) == 255


@pytest.mark.parametrize("method", ["gaussian", "average"])
def test_blur_smooths(method: str) -> None:
    result = Blur(method=method, kernel_size=5).apply(checkerboard())
    lo, hi = result.convert("L").crop((4, 4, 28, 28)).getextrema()
    assert hi - lo < 100


def test_blur_median_removes_salt_noise() -> None:
    image = Image.new("RGB", (20, 20), GRAY)
    for y in range(2, 20, 5):
        for x in range(2, 20, 5):
            image.putpixel((x, y), WHITE)
    result = Blur(method="median", kernel_size=3).apply(image)
    assert result.getextrema() == ((128, 128), (128, 128), (128, 128))


def test_blur_kernel_one_does_not_change() -> None:
    board = checkerboard()
    assert Blur(kernel_size=1).apply(board).tobytes() == board.tobytes()


def test_edges_are_binary_and_single_channel() -> None:
    result = Edges().apply(quadrants())
    assert result.mode == "L"
    assert {value for value, count in enumerate(result.histogram()) if count} == {0, 255}
    assert result.getpixel((5, 5)) == 0


def test_rotation_90_expands_counterclockwise() -> None:
    result = Rotation(angle=90, expand=True).apply(quadrants())
    assert result.size == (20, 40)
    assert result.getpixel((5, 5)) == BLUE
    assert result.getpixel((5, 35)) == RED


def test_rotation_without_expand_keeps_the_size() -> None:
    assert Rotation(angle=45, expand=False).apply(quadrants()).size == (40, 20)


def test_rotation_fills_with_black_or_transparent() -> None:
    assert Rotation(angle=45).apply(quadrants()).getpixel((0, 0)) == (0, 0, 0)
    assert Rotation(angle=45).apply(quadrants(mode="RGBA")).getpixel((0, 0))[3] == 0


def test_mirror_horizontal() -> None:
    result = Mirror(direction="horizontal").apply(quadrants())
    assert result.getpixel((5, 5)) == BLUE
    assert result.getpixel((5, 15)) == WHITE


def test_mirror_vertical() -> None:
    result = Mirror(direction="vertical").apply(quadrants())
    assert result.getpixel((5, 5)) == GREEN
    assert result.getpixel((35, 5)) == WHITE


def test_resize_keeps_the_aspect_ratio() -> None:
    assert Resize(width=10).apply(quadrants()).size == (10, 5)
    assert Resize(width=100).apply(quadrants(300, 200)).size == (100, 67)
    assert Resize(width=10, height=17).apply(quadrants()).size == (10, 5)


def test_resize_without_aspect_ratio() -> None:
    assert Resize(width=10, height=17, keep_aspect_ratio=False).apply(quadrants()).size == (10, 17)


@pytest.mark.parametrize("kernel_size", [2, 4, 50])
def test_blur_rejects_even_kernels(kernel_size: int) -> None:
    with pytest.raises(InvalidParameters):
        Blur(kernel_size=kernel_size)


def test_blur_rejects_unknown_methods() -> None:
    with pytest.raises(InvalidParameters):
        Blur(method="other")


@pytest.mark.parametrize("lower,upper", [(100, 100), (200, 100)])
def test_edges_reject_inverted_thresholds(lower: int, upper: int) -> None:
    with pytest.raises(InvalidParameters):
        Edges(lower_threshold=lower, upper_threshold=upper)


def test_resize_requires_the_height_without_aspect_ratio() -> None:
    with pytest.raises(InvalidParameters):
        Resize(width=10, keep_aspect_ratio=False)


def test_mirror_rejects_unknown_directions() -> None:
    with pytest.raises(InvalidParameters):
        Mirror(direction="diagonal")


@pytest.mark.parametrize(
    "mode,fmt,expected",
    [("P", "PNG", "RGB"), ("LA", "PNG", "RGBA"), ("1", "PNG", "L"), ("CMYK", "JPEG", "RGB")],
)
def test_codec_open_normalizes_the_mode(mode: str, fmt: str, expected: str) -> None:
    assert ImageCodec().open(to_bytes(quadrants(mode=mode), fmt)).mode == expected


def test_codec_encode_saves_rgba_as_jpeg() -> None:
    with Image.open(BytesIO(ImageCodec().encode(quadrants(mode="RGBA"), "JPEG"))) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"


def test_codec_encode_keeps_the_alpha_in_png() -> None:
    with Image.open(BytesIO(ImageCodec().encode(quadrants(mode="RGBA"), "PNG"))) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"
