"""
Step 3 · Enlarge. DO NOT MODIFY.

    pytest tests/test_step3_enlarge.py -v
"""

import numpy as np
import pytest

from helpers import assert_image, assert_input_untouched, colors_of, random_image
from retro.steps import Enlarge


@pytest.mark.parametrize("factor", [1, 2, 16])
def test_output_size(factor):
    assert_image(Enlarge(factor).apply(random_image(8, 8)), 8 * factor, 8 * factor)


def test_non_square_image():
    assert_image(Enlarge(4).apply(random_image(3, 5)), 12, 20)


def test_every_pixel_becomes_a_block_of_its_color():
    image = random_image(6, 6)
    result = Enlarge(5).apply(image)
    assert_image(result, 30, 30)
    for y in range(6):
        for x in range(6):
            block = result[5 * y:5 * y + 5, 5 * x:5 * x + 5]
            assert (block == image[y, x]).all(), (
                f"The block of pixel [{y}, {x}] must be all {image[y, x].tolist()}. "
                "Did you use bilinear or bicubic interpolation instead of nearest neighbor?")


def test_no_new_colors_appear():
    image = random_image(8, 8, seed=3)
    assert colors_of(Enlarge(16).apply(image)) == colors_of(image), "Enlarging pixel art must not create colors"


def test_factor_one_changes_nothing():
    image = random_image(7, 7)
    assert np.array_equal(Enlarge(1).apply(image), image)


def test_does_not_modify_the_input():
    assert_input_untouched(Enlarge(3), random_image(4, 4))
