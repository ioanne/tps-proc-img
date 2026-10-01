"""
Team tests: unit tests of the ten operations.

Each test checks a concrete property from the assignment table (section 5),
on images created in memory, without touching the disk or the database.
"""

import pytest
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

BLUE = (0, 0, 255)
RED = (255, 0, 0)


def gray_image(value: int = 128, size=(40, 20)) -> Image.Image:
    return Image.new("RGB", size, (value, value, value))


def corner_image(size=(40, 20)) -> Image.Image:
    """Red image with a blue pixel in the top-left corner."""
    img = Image.new("RGB", size, RED)
    img.putpixel((0, 0), BLUE)
    return img


def salt_image() -> Image.Image:
    """Black image with a single white pixel ("salt") in the middle."""
    img = Image.new("L", (21, 21), 0)
    img.putpixel((10, 10), 255)
    return img


def two_halves_image() -> Image.Image:
    """Left half dark gray (100), right half light gray (150)."""
    img = Image.new("RGB", (40, 20), (100, 100, 100))
    img.paste((150, 150, 150), (20, 0, 40, 20))
    return img


def distinct_colors(img: Image.Image) -> set:
    return {color for _, color in img.getcolors(maxcolors=img.width * img.height)}


# --- 1. Brightness -----------------------------------------------------------

def test_brightness_zero_is_black():
    result = Brightness(factor=0.0).apply(gray_image(128))
    assert distinct_colors(result) == {(0, 0, 0)}


def test_brightness_one_is_unchanged():
    img = corner_image()
    assert Brightness(factor=1.0).apply(img).tobytes() == img.tobytes()


def test_brightness_1_5_on_gray_128_is_about_192():
    r, g, b = Brightness(factor=1.5).apply(gray_image(128)).getpixel((0, 0))
    for channel in (r, g, b):
        assert abs(channel - 192) <= 1


# --- 2. Contrast -------------------------------------------------------------

def test_contrast_zero_is_a_single_uniform_color():
    result = Contrast(factor=0.0).apply(two_halves_image())
    assert len(distinct_colors(result)) == 1


def test_contrast_one_is_unchanged():
    img = two_halves_image()
    assert Contrast(factor=1.0).apply(img).tobytes() == img.tobytes()


def test_contrast_greater_than_one_separates_dark_and_light():
    result = Contrast(factor=2.0).apply(two_halves_image())
    dark = result.getpixel((0, 0))[0]
    light = result.getpixel((39, 0))[0]
    assert dark < 100
    assert light > 150


# --- 3. Saturation -----------------------------------------------------------

def test_saturation_zero_removes_color_and_keeps_three_channels():
    result = Saturation(factor=0.0).apply(corner_image())
    assert result.mode == "RGB"
    for r, g, b in result.getdata():
        assert r == g == b


def test_saturation_one_is_unchanged():
    img = corner_image()
    assert Saturation(factor=1.0).apply(img).tobytes() == img.tobytes()


# --- 4. Sharpness ------------------------------------------------------------

def test_sharpness_one_is_unchanged():
    img = salt_image()
    assert Sharpness(factor=1.0).apply(img).tobytes() == img.tobytes()


def test_sharpness_zero_smooths():
    result = Sharpness(factor=0.0).apply(salt_image())
    assert result.getpixel((10, 10)) < 255  # the isolated pixel gets softened


# --- 5. Grayscale ------------------------------------------------------------

def test_grayscale_returns_single_channel():
    result = Grayscale().apply(corner_image())
    assert result.mode == "L"
    assert len(result.getbands()) == 1


def test_grayscale_pure_red_is_76():
    result = Grayscale().apply(Image.new("RGB", (10, 10), RED))
    assert result.getpixel((0, 0)) == 76


def test_grayscale_rgba_has_no_alpha():
    result = Grayscale().apply(Image.new("RGBA", (10, 10), (255, 0, 0, 128)))
    assert result.mode == "L"


# --- 6. Blur -----------------------------------------------------------------

@pytest.mark.parametrize("method", ["gaussian", "median", "average"])
def test_blur_kernel_one_is_unchanged(method):
    img = salt_image()
    assert Blur(method=method, kernel_size=1).apply(img).tobytes() == img.tobytes()


def test_blur_median_removes_salt():
    result = Blur(method="median", kernel_size=3).apply(salt_image())
    assert result.getpixel((10, 10)) == 0


@pytest.mark.parametrize("method", ["gaussian", "average"])
def test_blur_spreads_the_salt_pixel(method):
    result = Blur(method=method, kernel_size=5).apply(salt_image())
    assert result.getpixel((10, 10)) < 255  # the center loses intensity
    assert result.getpixel((11, 10)) > 0    # and the neighbors gain some


# --- 7. Edges ----------------------------------------------------------------

def test_edges_returns_l_with_only_0_and_255():
    img = Image.new("RGB", (40, 20), "black")
    img.paste((255, 255, 255), (20, 0, 40, 20))  # vertical border in the middle

    result = Edges().apply(img)

    assert result.mode == "L"
    assert set(result.getdata()) == {0, 255}


def test_edges_uniform_image_has_no_edges():
    result = Edges().apply(gray_image(128))
    assert set(result.getdata()) == {0}


# --- 8. Rotation -------------------------------------------------------------

def test_rotation_90_with_expand_swaps_size():
    result = Rotation(angle=90, expand=True).apply(Image.new("RGB", (200, 100)))
    assert result.size == (100, 200)


def test_rotation_without_expand_keeps_size():
    result = Rotation(angle=90, expand=False).apply(Image.new("RGB", (200, 100)))
    assert result.size == (200, 100)


def test_rotation_positive_angle_is_counterclockwise():
    img = Image.new("RGB", (200, 100), RED)
    img.putpixel((199, 0), BLUE)  # top-right corner

    result = Rotation(angle=90, expand=True).apply(img)

    # Counterclockwise: the top-right corner ends up at the top-left.
    assert result.getpixel((0, 0)) == BLUE


def test_rotation_fills_new_areas_with_black_on_rgb():
    result = Rotation(angle=45, expand=True).apply(Image.new("RGB", (40, 20), RED))
    assert result.getpixel((0, 0)) == (0, 0, 0)


def test_rotation_fills_new_areas_with_transparent_on_rgba():
    result = Rotation(angle=45, expand=True).apply(Image.new("RGBA", (40, 20), (255, 0, 0, 255)))
    assert result.getpixel((0, 0))[3] == 0


# --- 9. Mirror ---------------------------------------------------------------

def test_mirror_horizontal_moves_corner_to_the_right():
    result = Mirror(direction="horizontal").apply(corner_image())
    assert result.getpixel((39, 0)) == BLUE
    assert result.getpixel((0, 0)) == RED


def test_mirror_vertical_moves_corner_to_the_bottom():
    result = Mirror(direction="vertical").apply(corner_image())
    assert result.getpixel((0, 19)) == BLUE
    assert result.getpixel((0, 0)) == RED


# --- 10. Resize --------------------------------------------------------------

def test_resize_keeping_aspect_ratio_gives_expected_height():
    result = Resize(width=100).apply(Image.new("RGB", (300, 200)))
    assert result.size == (100, 67)  # round(100 * 200 / 300)


def test_resize_keeping_aspect_ratio_ignores_height():
    # Assignment: with keep_aspect_ratio, the received height is ignored.
    result = Resize(width=100, height=10, keep_aspect_ratio=True).apply(Image.new("RGB", (300, 200)))
    assert result.size == (100, 67)


def test_resize_without_aspect_ratio_uses_exact_size():
    result = Resize(width=120, height=30, keep_aspect_ratio=False).apply(Image.new("RGB", (300, 200)))
    assert result.size == (120, 30)
