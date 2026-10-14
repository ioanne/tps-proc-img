"""
Helpers shared by the tests. DO NOT MODIFY.

You can use them in your own experiments too:  from helpers import random_image
"""

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from retro import PALETTES

BACKEND_DIR = Path(__file__).resolve().parent.parent


# ===========================================================================
# Images
# ===========================================================================

def random_image(height: int, width: int, seed: int = 0) -> np.ndarray:
    """An RGB image of random colors."""
    return np.random.default_rng(seed).integers(0, 256, (height, width, 3), dtype=np.uint8)


def uniform(height: int, width: int, color) -> np.ndarray:
    """An RGB image of a single color."""
    return np.full((height, width, 3), color, dtype=np.uint8)


def gray_image(values) -> np.ndarray:
    """A 2D list of gray levels → RGB image with R = G = B."""
    g = np.array(values, dtype=np.uint8)
    return np.repeat(g[:, :, None], 3, axis=2)


def numbered(height: int, width: int) -> np.ndarray:
    """Each pixel stores where it was: R = its column (x), G = its row (y), B = 0."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :, 0] = np.arange(width)[None, :]
    img[:, :, 1] = np.arange(height)[:, None]
    return img


def checkerboard(height: int, width: int) -> np.ndarray:
    """Black and white squares of 1 pixel."""
    return gray_image((np.indices((height, width)).sum(axis=0) % 2) * 255)


# ===========================================================================
# Colors
# ===========================================================================

def colors_of(image: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(c) for c in np.unique(image.reshape(-1, 3), axis=0).tolist()}


def palette_colors(name: str) -> set[tuple[int, int, int]]:
    return {tuple(c) for c in PALETTES[name].colors.tolist()}


def rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def as_hex(color) -> str:
    return "#%02x%02x%02x" % tuple(int(v) for v in color)


# ===========================================================================
# Assertions
# ===========================================================================

def assert_image(result, height: int, width: int) -> None:
    assert isinstance(result, np.ndarray), f"apply must return a numpy array, got {type(result).__name__}"
    assert result.dtype == np.uint8, f"apply must return uint8, got {result.dtype}"
    assert result.shape == (height, width, 3), f"Expected shape {(height, width, 3)}, got {result.shape}"


def assert_input_untouched(step, image: np.ndarray) -> None:
    before = image.copy()
    step.apply(image)
    assert np.array_equal(image, before), "apply must not modify the image it receives (work on a copy)"


# ===========================================================================
# Files
# ===========================================================================

def encode(rgb_image: np.ndarray | Image.Image, fmt: str = "PNG", **save_args) -> bytes:
    img = rgb_image if isinstance(rgb_image, Image.Image) else Image.fromarray(rgb_image)
    buf = BytesIO()
    img.save(buf, format=fmt, **save_args)
    return buf.getvalue()


def decode(content: bytes) -> np.ndarray:
    with Image.open(BytesIO(content)) as img:
        assert img.format == "PNG", f"Expected a PNG, got {img.format}"
        return np.array(img.convert("RGB"))
