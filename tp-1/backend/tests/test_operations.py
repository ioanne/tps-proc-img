from PIL import Image

from app.core.operations import Brightness, Contrast


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