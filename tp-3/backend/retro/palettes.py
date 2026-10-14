"""
The palettes of the avatar. Given.

A palette is a short, fixed list of colors: the only ones the avatar may use.
There are two kinds:

- Monochrome palettes are a "ramp" from the darkest color to the lightest
  (the four greens of the Game Boy). The photo is first turned into shades of
  that ramp (GradientMap) and then each pixel is rounded to one of its colors.
- Color palettes (CGA, PICO-8) are used as they are: each pixel goes to the
  nearest color of the list.

Add your own palette to PALETTES and it shows up in the API and the frontend.
"""

from dataclasses import dataclass

import numpy as np

LUMA = np.array([0.299, 0.587, 0.114])  # weights of R, G and B in the perceived brightness


@dataclass(frozen=True)
class Palette:
    name: str                    # id used by the API: "gameboy"
    label: str                   # name shown in the frontend: "Game Boy"
    hex_colors: tuple[str, ...]  # "#rrggbb"; in monochrome palettes, from darkest to lightest
    monochrome: bool = False

    @property
    def colors(self) -> np.ndarray:
        """The colors as an (n, 3) uint8 array, in RGB order. A new array on every call."""
        return np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in self.hex_colors], dtype=np.uint8)

    @property
    def darkest(self) -> np.ndarray:
        """The color with the lowest luminance, as a (3,) uint8 array."""
        colors = self.colors
        return colors[np.argmin(colors @ LUMA)]

    def __len__(self) -> int:
        return len(self.hex_colors)


PALETTES: dict[str, Palette] = {p.name: p for p in [
    Palette("gameboy", "Game Boy", ("#0f380f", "#306230", "#8bac0f", "#9bbc0f"), monochrome=True),
    Palette("bw", "1-bit", ("#000000", "#ffffff"), monochrome=True),
    Palette("virtualboy", "Virtual Boy", ("#000000", "#550000", "#aa0000", "#ff0000"), monochrome=True),
    Palette("cga", "CGA", ("#000000", "#55ffff", "#ff55ff", "#ffffff")),
    Palette("pico8", "PICO-8", (
        "#000000", "#1d2b53", "#7e2553", "#008751", "#ab5236", "#5f574f", "#c2c3c7", "#fff1e8",
        "#ff004d", "#ffa300", "#ffec27", "#00e436", "#29adff", "#83769c", "#ff77a8", "#ffccaa",
    )),
]}

DEFAULT_PALETTE = "gameboy"
