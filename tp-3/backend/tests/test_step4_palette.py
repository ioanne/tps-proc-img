"""
Step 4 · nearest_color and PaletteMap. DO NOT MODIFY.

    pytest tests/test_step4_palette.py -v
"""

import numpy as np
import pytest

from helpers import (as_hex, assert_image, assert_input_untouched, colors_of, palette_colors, random_image,
                     rgb)
from retro import PALETTES
from retro.steps import PaletteMap, nearest_color

# (palette, color, nearest color of that palette)
EXAMPLES = [
    ("pico8", (250, 20, 60), "#ff004d"),
    ("pico8", (30, 40, 90), "#1d2b53"),
    ("pico8", (200, 200, 200), "#c2c3c7"),
    ("pico8", (255, 160, 20), "#ffa300"),
    ("pico8", (60, 160, 255), "#29adff"),
    ("pico8", (120, 110, 160), "#83769c"),
    ("cga", (255, 0, 0), "#000000"),
    ("cga", (100, 220, 230), "#55ffff"),
    ("cga", (200, 100, 210), "#ff55ff"),
    ("gameboy", (120, 160, 20), "#8bac0f"),
    ("gameboy", (40, 90, 40), "#306230"),
    ("bw", (100, 100, 100), "#000000"),
    ("bw", (140, 140, 140), "#ffffff"),
]


# ===========================================================================
# nearest_color
# ===========================================================================

@pytest.mark.parametrize("palette, color, expected", EXAMPLES)
def test_nearest_color(palette, color, expected):
    got = nearest_color(np.array(color, dtype=np.uint8), PALETTES[palette].colors)
    assert as_hex(got) == expected, (
        f"In {palette}, the nearest color to {color} is {expected}, got {as_hex(got)}. "
        "If you subtract uint8 arrays, 10 - 20 is 246: convert to float first")


@pytest.mark.parametrize("color, expected", [
    ((127.4, 127.4, 127.4), "#000000"),
    ((127.6, 127.6, 127.6), "#ffffff"),
    ((-30.0, -30.0, -30.0), "#000000"),
    ((290.0, 290.0, 290.0), "#ffffff"),
])
def test_nearest_color_accepts_floats_out_of_range(color, expected):
    """In step 6 the colors are floats and can go below 0 or above 255."""
    got = nearest_color(np.array(color), PALETTES["bw"].colors)
    assert as_hex(got) == expected, f"The nearest color to {color} is {expected}, got {as_hex(got)}"


def test_nearest_color_returns_a_color_of_the_palette():
    colors = PALETTES["pico8"].colors
    allowed = palette_colors("pico8")
    for color in random_image(1, 50, seed=4)[0]:
        got = nearest_color(color, colors)
        assert tuple(int(v) for v in got) in allowed, f"{as_hex(got)} is not in the palette"


# ===========================================================================
# PaletteMap
# ===========================================================================

@pytest.mark.parametrize("palette", sorted(PALETTES))
def test_only_palette_colors(palette):
    result = PaletteMap(PALETTES[palette]).apply(random_image(24, 24))
    assert_image(result, 24, 24)
    extra = colors_of(result) - palette_colors(palette)
    assert not extra, f"Colors that are not in {palette}: {sorted(as_hex(c) for c in extra)[:5]}"


def test_each_pixel_gets_its_nearest_color():
    pico8 = [(color, expected) for palette, color, expected in EXAMPLES if palette == "pico8"]
    image = np.array([[color for color, _ in pico8]], dtype=np.uint8)
    result = PaletteMap(PALETTES["pico8"]).apply(image)
    assert_image(result, 1, len(pico8))
    assert [as_hex(c) for c in result[0]] == [expected for _, expected in pico8]


def test_palette_colors_stay_the_same():
    colors = PALETTES["pico8"].colors
    image = np.tile(colors[None, :, :], (3, 1, 1))  # 3 rows with the 16 colors
    assert np.array_equal(PaletteMap(PALETTES["pico8"]).apply(image), image)


def test_uniform_image_gets_a_single_color():
    image = np.full((8, 8, 3), (250, 20, 60), dtype=np.uint8)
    result = PaletteMap(PALETTES["pico8"]).apply(image)
    assert colors_of(result) == {rgb("#ff004d")}


def test_does_not_modify_the_input():
    assert_input_untouched(PaletteMap(PALETTES["cga"]), random_image(8, 8))
