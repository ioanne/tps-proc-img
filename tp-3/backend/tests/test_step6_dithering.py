"""
Step 6 · FloydSteinberg. DO NOT MODIFY.

    pytest tests/test_step6_dithering.py -v

The exact tests use small images worked out by hand with the algorithm of the
assignment: left to right, top to bottom, 7/16 · 3/16 · 5/16 · 1/16.
"""

import numpy as np
import pytest

from helpers import (as_hex, assert_image, assert_input_untouched, colors_of, gray_image, palette_colors,
                     random_image, uniform)
from retro import PALETTES
from retro.steps import FloydSteinberg, PaletteMap


def dither(palette: str, image: np.ndarray) -> np.ndarray:
    return FloydSteinberg(PALETTES[palette]).apply(image)


def as_indices(palette: str, image: np.ndarray) -> list[list[int]]:
    """Each pixel → the position of its color in the palette."""
    colors = [tuple(c) for c in PALETTES[palette].colors.tolist()]
    return [[colors.index(tuple(p)) for p in row] for row in image.tolist()]


def block_error(result: np.ndarray, image: np.ndarray, block: int = 8) -> float:
    """Mean difference between the average brightness of each block before and after."""
    h, w = image.shape[:2]
    a = result[:, :, 0].astype(float).reshape(h // block, block, w // block, block).mean(axis=(1, 3))
    b = image[:, :, 0].astype(float).reshape(h // block, block, w // block, block).mean(axis=(1, 3))
    return float(np.abs(a - b).mean())


# ===========================================================================
# What any dithering must do
# ===========================================================================

@pytest.mark.parametrize("palette", sorted(PALETTES))
def test_only_palette_colors(palette):
    result = dither(palette, random_image(32, 32))
    assert_image(result, 32, 32)
    extra = colors_of(result) - palette_colors(palette)
    assert not extra, f"Colors that are not in {palette}: {sorted(as_hex(c) for c in extra)[:5]}"


def test_palette_colors_stay_the_same():
    """A pixel that already is a palette color has no error: nothing to spread."""
    colors = PALETTES["pico8"].colors
    image = np.tile(colors[None, :, :], (4, 1, 1))
    assert np.array_equal(dither("pico8", image), image)


def test_mid_gray_becomes_half_black_half_white():
    result = dither("bw", uniform(32, 32, 128))
    white = float((result[:, :, 0] == 255).mean())
    assert 0.45 <= white <= 0.55, (
        f"A 50 % gray must become ≈50 % white pixels, got {white:.0%}. "
        "(Without dithering it would be 100 % white.)")


def test_keeps_the_average_brightness():
    gradient = gray_image(np.repeat(np.arange(64)[None, :] * 4, 32, axis=0))  # 32×64, from black to white
    dithered = block_error(dither("bw", gradient), gradient)
    rounded = block_error(PaletteMap(PALETTES["bw"]).apply(gradient), gradient)
    assert dithered < 10, (
        f"Each 8×8 block must keep (about) its average brightness: it moved {dithered:.1f} on average "
        f"(without dithering it moves {rounded:.1f})")


# ===========================================================================
# Exactly Floyd–Steinberg
# ===========================================================================

def test_one_row():
    """A single row: only the right neighbor exists, so it receives 7/16 of each error (the rest is lost)."""
    result = dither("bw", uniform(1, 8, 100))
    assert_image(result, 1, 8)
    assert result[0, :, 0].tolist() == [0, 255, 0, 0, 255, 0, 0, 255]


def test_gray_pattern():
    image = gray_image([[52, 160, 173, 178, 193],
                        [73, 137, 181, 103, 73],
                        [124, 54, 78, 190, 157],
                        [191, 187, 194, 94, 123]])
    result = dither("bw", image)
    assert_image(result, 4, 5)
    expected = [[0, 1, 1, 1, 1],
                [0, 1, 0, 0, 0],
                [0, 0, 1, 1, 1],
                [1, 1, 0, 0, 0]]
    got = as_indices("bw", result)
    assert got == expected, (
        f"Expected (0 = black, 1 = white)\n{np.array(expected)}\ngot\n{np.array(got)}\n"
        "Check the weights, the order (left to right, top to bottom) and the borders: "
        "at x = 0 there is no neighbor below-left (x - 1 = -1 is the LAST column in numpy)")


def test_color_pattern():
    image = np.array([[[39, 201, 135], [171, 59, 141], [159, 174, 201], [174, 206, 39]],
                      [[136, 188, 217], [51, 86, 135], [132, 125, 125], [179, 38, 72]],
                      [[141, 166, 130], [184, 108, 97], [86, 143, 207], [111, 96, 178]]], dtype=np.uint8)
    result = dither("cga", image)
    assert_image(result, 3, 4)
    expected = [[1, 0, 3, 0],
                [1, 0, 2, 2],
                [2, 2, 1, 0]]
    got = as_indices("cga", result)
    assert got == expected, (
        f"Expected (0 black, 1 cyan, 2 magenta, 3 white)\n{np.array(expected)}\ngot\n{np.array(got)}\n"
        "The error is a vector: each channel (R, G, B) is spread separately")


def test_does_not_modify_the_input():
    assert_input_untouched(FloydSteinberg(PALETTES["bw"]), random_image(8, 8))
