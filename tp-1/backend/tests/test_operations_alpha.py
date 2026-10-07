"""
Team tests: on an RGBA image, the color operations (brightness, contrast,
saturation, sharpness) do not modify the alpha channel.

Tested on images created in memory, without touching the disk or the database.
"""

import pytest
from PIL import Image

from app.core.operations import Brightness, Contrast, Saturation, Sharpness

COLOR_OPERATIONS = [
    Brightness(factor=1.5),
    Contrast(factor=0.0),
    Saturation(factor=0.0),
    Sharpness(factor=2.0),
]


@pytest.mark.parametrize("operation", COLOR_OPERATIONS, ids=lambda op: op.name)
def test_color_operations_keep_alpha(operation):
    # Two different alpha values (128 and 0) so the test does not pass
    # by chance with a uniform alpha.
    img = Image.new("RGBA", (40, 20), (200, 50, 50, 128))
    img.putpixel((0, 0), (200, 50, 50, 0))

    result = operation.apply(img)

    assert result.mode == "RGBA"
    assert result.getchannel("A").tobytes() == img.getchannel("A").tobytes()
