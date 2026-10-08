
import pytest
from PIL import Image

from app.core.exceptions import InvalidParameters
from app.core.operations import Brightness, Contrast, Saturation, Sharpness, Grayscale, Mirror, Resize, Blur, Edges, Rotation


def test_brightness_factor_zero_gives_black():
    image= Image.new("RGB", (10, 10), (100, 150, 200))

    operation = Brightness(factor=0)
    result =operation.apply(image)

    assert result.getpixel((0, 0))==(0, 0, 0)

def test_contrast_factor_one_does_not_change_image():
    image = Image.new("RGB", (10, 10), (100, 150, 200))

    operation = Contrast(factor=1)
    result = operation.apply(image)

    assert result.getpixel((0, 0)) == image.getpixel((0, 0))    

def test_saturation_factor_zero_removes_color():
    image = Image.new("RGB", (10, 10), (100, 150, 200))

    operation = Saturation(factor=0)
    result = operation.apply(image)

    r, g, b = result.getpixel((0, 0))

    assert r == g == b
    assert result.mode == "RGB"


def test_sharpness_factor_one_does_not_change_image():
    image = Image.new("RGB", (10, 10), (100, 150, 200))

    operation = Sharpness(factor=1)
    result = operation.apply(image)

    assert result.getpixel((0, 0)) == image.getpixel((0, 0))


def test_grayscale_returns_single_channel_image():
    image = Image.new("RGB", (10, 10), (255, 0, 0))

    operation = Grayscale()
    result = operation.apply(image)

    assert result.mode == "L"


def test_mirror_horizontal_swaps_left_and_right():
    image = Image.new("RGB", (2, 1))
    image.putpixel((0, 0), (255, 0, 0))
    image.putpixel((1, 0), (0, 0, 255))

    operation = Mirror(direction="horizontal")
    result = operation.apply(image)

    assert result.getpixel((0, 0)) == (0, 0, 255)
    assert result.getpixel((1, 0)) == (255, 0, 0)    

def test_blur_smooths_a_bright_pixel():
    image = Image.new("L", (5, 5), 0)
    image.putpixel((2, 2), 255)

    operation = Blur(method="average", kernel_size=3)
    result = operation.apply(image)

    assert result.getpixel((2, 2)) < 255


def test_edges_returns_binary_grayscale_image():
    image = Image.new("L", (20, 20), 0)

    for x in range(10, 20):
        for y in range(20):
            image.putpixel((x, y), 255)

    operation = Edges(lower_threshold=100, upper_threshold=200)
    result = operation.apply(image)

    values = set(result.get_flattened_data())

    assert result.mode == "L"
    assert values.issubset({0, 255})
    assert 255 in values


def test_rotation_90_degrees_changes_dimensions():
    image = Image.new("RGB", (20, 10), "red")

    operation = Rotation(angle=90, expand=True)
    result = operation.apply(image)

    assert result.size == (10, 20)


def test_resize_keeps_aspect_ratio():
    image = Image.new("RGB", (300, 200), "red")

    operation = Resize(width=100)
    result = operation.apply(image)

    assert result.size == (100, 67)    

def test_blur_rejects_even_kernel():
    with pytest.raises(InvalidParameters):
        Blur(method="gaussian", kernel_size=4)


def test_edges_rejects_invalid_thresholds():
    with pytest.raises(InvalidParameters):
        Edges(lower_threshold=200, upper_threshold=100)


def test_resize_requires_height_without_aspect_ratio():
    with pytest.raises(InvalidParameters):
        Resize(
            width=100,
            height=None,
            keep_aspect_ratio=False
        )    