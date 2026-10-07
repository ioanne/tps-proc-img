from PIL import Image

from app.core.operations import Brightness, Contrast, Saturation, Sharpness, Grayscale, Mirror


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