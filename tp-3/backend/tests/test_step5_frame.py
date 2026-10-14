"""
Step 5 · Frame. DO NOT MODIFY.

    pytest tests/test_step5_frame.py -v
"""

import numpy as np
import pytest

from helpers import assert_image, assert_input_untouched, random_image
from retro.steps import Frame

COLOR = np.array([15, 56, 15], dtype=np.uint8)


def frame(thickness: int) -> Frame:
    return Frame(COLOR, thickness)


@pytest.mark.parametrize("thickness", [1, 2, 4])
def test_paints_the_border(thickness):
    image = random_image(16, 16)
    result = frame(thickness).apply(image)
    assert_image(result, 16, 16)
    t = thickness
    ring = np.ones((16, 16), dtype=bool)
    ring[t:-t, t:-t] = False
    assert (result[ring] == COLOR).all(), f"The outer {t} pixel(s) on every side must be {COLOR.tolist()}"
    assert np.array_equal(result[t:-t, t:-t], image[t:-t, t:-t]), "Inside the frame the image must not change"


def test_non_square_image():
    image = random_image(10, 14)
    result = frame(1).apply(image)
    assert_image(result, 10, 14)
    for name, side in [("top", result[0]), ("bottom", result[-1]), ("left", result[:, 0]), ("right", result[:, -1])]:
        assert (side == COLOR).all(), f"The {name} side must be painted"
    assert np.array_equal(result[1:-1, 1:-1], image[1:-1, 1:-1])


def test_thickness_zero_changes_nothing():
    image = random_image(8, 8)
    result = frame(0).apply(image)
    assert_image(result, 8, 8)
    assert np.array_equal(result, image), "With thickness 0 nothing is painted. Hint: what is a[-0:]?"


def test_does_not_modify_the_input():
    assert_input_untouched(frame(2), random_image(8, 8))
