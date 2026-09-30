from PIL import Image

from app.core.operations import (
    Blur,
    Brightness,
    Contrast,
    Edges,
    Grayscale,
    Mirror,
    Resize,
    Rotation,
    Saturation,
    Sharpness,
)


def make_rgb(color=(255, 0, 0), size=(40, 20)):
    return Image.new("RGB", size, color)


def make_rgba(color=(255, 0, 0, 128), size=(40, 20)):
    return Image.new("RGBA", size, color)


def test_brightness_zero_returns_black():
    result = Brightness(factor=0.0).apply(make_rgb())

    assert result.getpixel((0, 0)) == (0, 0, 0)


def test_brightness_one_unchanged():
    img = make_rgb((100, 150, 200))

    result = Brightness(factor=1.0).apply(img)

    assert result.getpixel((0, 0)) == img.getpixel((0, 0))


def test_brightness_rgba_preserves_alpha():
    img = make_rgba((255, 0, 0, 128))

    result = Brightness(factor=0.0).apply(img)

    assert result.getpixel((0, 0))[3] == 128


def test_grayscale_mode_is_L():
    result = Grayscale().apply(make_rgb())

    assert result.mode == "L"


def test_grayscale_pure_red_gives_76():
    result = Grayscale().apply(make_rgb((255, 0, 0)))

    assert result.getpixel((0, 0)) == 76


def test_mirror_horizontal_inverts_left_right():
    img = Image.new("RGB", (4, 4), (0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0))

    result = Mirror(direction="horizontal").apply(img)

    assert result.getpixel((3, 0)) == (255, 0, 0)


def test_rotation_90_swaps_dimensions():
    img = Image.new("RGB", (200, 100))

    result = Rotation(angle=90, expand=True).apply(img)

    assert result.size == (100, 200)


def test_resize_aspect_ratio_computes_height():
    img = Image.new("RGB", (300, 200))

    result = Resize(
        width=100,
        keep_aspect_ratio=True,
    ).apply(img)

    assert result.size == (100, 67)


def test_blur_kernel_1_is_noop():
    img = make_rgb((100, 150, 200))

    result = Blur(kernel_size=1).apply(img)

    assert result.getpixel((0, 0)) == img.getpixel((0, 0))


def test_edges_uniform_area_all_zeros():
    img = Image.new("RGB", (50, 50), (128, 128, 128))

    result = Edges().apply(img)

    assert result.mode == "L"
    assert result.getpixel((25, 25)) == 0