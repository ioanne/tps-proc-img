"""
Team tests: no operation modifies the image it receives.

The `Operation.apply` contract says it returns a NEW image and that the input
image is not modified. Tested on images created in memory, without touching
the disk or the database.
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


def sample_image() -> Image.Image:
    # Red with a blue pixel in the corner, so the operations
    # (mirror, rotation, blur...) actually change something.
    img = Image.new("RGB", (40, 20), "red")
    img.putpixel((0, 0), (0, 0, 255))
    return img


ALL_OPERATIONS = [
    Brightness(factor=1.5),
    Contrast(factor=2.0),
    Saturation(factor=0.0),
    Sharpness(factor=2.0),
    Grayscale(),
    Blur(kernel_size=5),
    Edges(),
    Rotation(angle=90),
    Mirror(direction="horizontal"),
    Resize(width=10),
]


@pytest.mark.parametrize("operation", ALL_OPERATIONS, ids=lambda op: op.name)
def test_apply_does_not_modify_original(operation):
    original = sample_image()
    copy = original.copy()

    operation.apply(original)

    assert original.mode == copy.mode
    assert original.size == copy.size
    assert original.tobytes() == copy.tobytes()
