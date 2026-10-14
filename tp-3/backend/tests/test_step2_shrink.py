"""
Step 2 · Shrink. DO NOT MODIFY.

    pytest tests/test_step2_shrink.py -v
"""

import numpy as np
import pytest

from helpers import assert_image, assert_input_untouched, checkerboard, random_image, uniform
from retro.steps import Shrink


def blocks_with_known_average(size: int, block: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """
    An image of size·block pixels per side whose blocks of block × block pixels
    have a known average color (`target`). Inside each block the pixels are
    different: the target plus random offsets that add up to zero.
    """
    rng = np.random.default_rng(seed)
    target = rng.integers(50, 206, (size, size, 3))
    half = block * block // 2
    offsets = rng.integers(-40, 41, (size, size, 3, half))
    offsets = np.concatenate([offsets, -offsets], axis=-1)            # each block adds up to 0
    offsets = rng.permuted(offsets, axis=-1)                          # in random positions
    offsets = offsets.reshape(size, size, 3, block, block).transpose(0, 3, 1, 4, 2)
    image = target[:, None, :, None, :] + offsets
    return image.reshape(size * block, size * block, 3).astype(np.uint8), target


@pytest.mark.parametrize("side, size", [(64, 16), (64, 32), (128, 128), (100, 32), (768, 64)])
def test_output_size(side, size):
    assert_image(Shrink(size).apply(random_image(side, side)), size, size)


def test_each_pixel_is_the_average_of_its_block():
    image, target = blocks_with_known_average(size=16, block=4)
    result = Shrink(16).apply(image)
    assert_image(result, 16, 16)
    diff = np.abs(result.astype(int) - target)
    y, x, _ = np.unravel_index(diff.argmax(), diff.shape)
    assert diff.max() <= 1, (
        f"Pixel [{y}, {x}] should be the average of its 4×4 block, ≈{target[y, x].tolist()}, "
        f"got {result[y, x].tolist()}")


def test_fine_checkerboard_becomes_gray():
    result = Shrink(16).apply(checkerboard(64, 64))
    assert_image(result, 16, 16)
    assert result.min() >= 126 and result.max() <= 129, (
        "Half black and half white pixels average to gray (≈128), "
        f"got values from {result.min()} to {result.max()}. Did you use nearest neighbor?")


def test_uniform_image_keeps_its_color():
    result = Shrink(32).apply(uniform(100, 100, (200, 40, 90)))
    assert_image(result, 32, 32)
    assert np.array_equal(result, uniform(32, 32, (200, 40, 90)))


def test_does_not_modify_the_input():
    assert_input_untouched(Shrink(8), random_image(64, 64))
