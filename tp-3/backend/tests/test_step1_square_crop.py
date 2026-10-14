"""
Step 1 · SquareCrop. DO NOT MODIFY.

    pytest tests/test_step1_square_crop.py -v

`numbered` images store in each pixel where it was (R = column, G = row), so
after cropping we can see which columns and rows were kept.
"""

import numpy as np
import pytest

from helpers import assert_image, assert_input_untouched, numbered, random_image
from retro.steps import SquareCrop


def kept_columns(result: np.ndarray) -> list[int]:
    return result[0, :, 0].tolist()


def kept_rows(result: np.ndarray) -> list[int]:
    return result[:, 0, 1].tolist()


def test_landscape_keeps_the_centered_square():
    result = SquareCrop().apply(numbered(4, 8))
    assert_image(result, 4, 4)
    assert kept_columns(result) == [2, 3, 4, 5], "2 columns are cut on each side"
    assert kept_rows(result) == [0, 1, 2, 3]


def test_portrait_keeps_the_centered_square():
    result = SquareCrop().apply(numbered(10, 6))
    assert_image(result, 6, 6)
    assert kept_rows(result) == [2, 3, 4, 5, 6, 7], "2 rows are cut at the top and 2 at the bottom"
    assert kept_columns(result) == [0, 1, 2, 3, 4, 5]


def test_odd_leftover_is_cut_on_the_right():
    result = SquareCrop().apply(numbered(4, 7))
    assert_image(result, 4, 4)
    assert kept_columns(result) == [1, 2, 3, 4], "3 columns left over: 1 is cut on the left and 2 on the right"


def test_odd_leftover_is_cut_at_the_bottom():
    result = SquareCrop().apply(numbered(7, 4))
    assert_image(result, 4, 4)
    assert kept_rows(result) == [1, 2, 3, 4], "3 rows left over: 1 is cut at the top and 2 at the bottom"


def test_square_image_stays_the_same():
    image = random_image(5, 5)
    result = SquareCrop().apply(image)
    assert_image(result, 5, 5)
    assert np.array_equal(result, image)


@pytest.mark.parametrize("height, width", [(768, 1024), (1024, 576), (300, 301)])
def test_photo_sizes(height, width):
    image = random_image(height, width)
    result = SquareCrop().apply(image)
    side = min(height, width)
    assert_image(result, side, side)
    top, left = (height - side) // 2, (width - side) // 2
    assert np.array_equal(result, image[top:top + side, left:left + side]), "The pixels must be those of the center"


def test_does_not_modify_the_input():
    assert_input_untouched(SquareCrop(), random_image(6, 9))
