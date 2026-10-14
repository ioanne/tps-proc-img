"""
The steps of the pipeline that turns a photo into a retro avatar.

Every step is a class with the same interface (`Step`): `apply(image)` receives
an image and returns a NEW one. The pipeline (`pipeline.py`, given) builds the
list of steps from the options and applies them one after the other:

    photo → SquareCrop → Shrink → [GradientMap] → PaletteMap | FloydSteinberg → [Frame] → Enlarge

Conventions (the tests check them):
  - An image is a numpy array of shape (height, width, 3), dtype uint8, in RGB
    order. It is indexed [y, x]: image[0, 0] is the top-left pixel.
  - `apply` must NOT modify the image it receives.
  - `apply` returns a uint8 array.

GIVEN: Step and GradientMap (a solved example: read it before starting).
TODO (team): steps 1 to 6, in the order of the assignment. While a step is not
implemented it raises StepNotImplemented and the pipeline skips it, so the
frontend works from minute one.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

import numpy as np

from retro.exceptions import StepNotImplemented
from retro.palettes import LUMA, Palette
import cv2 as cv


class Step(ABC):
    """A step of the pipeline. Given."""

    number: ClassVar[int | None] = None  # step number in the assignment (None: given)
    name: ClassVar[str]                  # id used by the API: "square_crop"
    label: ClassVar[str]                 # name shown in the frontend: "Square crop"
    essential: ClassVar[bool] = False    # if it is pending, the following steps cannot run

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Returns a NEW image with the step applied. `image` must not be modified."""

    def output_shape(self, height: int, width: int) -> tuple[int, int]:
        """(height, width) of the image `apply` returns. The pipeline checks it."""
        return height, width

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


# ===========================================================================
# GIVEN: a solved example
# ===========================================================================

class GradientMap(Step):
    """
    Turns the image into shades of a monochrome palette ("gradient map").

    Black goes to the darkest color of the palette, white to the lightest, and
    the grays in between are spread over the ramp. For the Game Boy palette a
    mid gray becomes a color between its second and third greens. The result
    still has many colors: rounding them to the palette is PaletteMap's job.

    Used only with monochrome palettes, right after Shrink.

    Convierte la imagen en tonos de una paleta monocromática ("mapa de gradiente"). 
    El negro pasa al color más oscuro de la paleta, el blanco al más claro y los grises 
    intermedios se extienden por la rampa. Para la paleta de Game Boy a El gris medio se 
    convierte en un color entre su segundo y tercer verde. El resultado Todavía tiene muchos 
    colores: redondearlos a la paleta es tarea de PaletteMap. Se utiliza únicamente con
      paletas monocromáticas, justo después de Shrink.
    """

    name = "gradient_map"
    label = "Tone ramp"

    def __init__(self, palette: Palette, cutoff: float = 1.0) -> None:
        self.colors = palette.colors.astype(float)  # (n, 3), from darkest to lightest
        self.cutoff = cutoff                        # % of the darkest and lightest pixels to saturate

    def apply(self, image: np.ndarray) -> np.ndarray:
        # 1. Brightness of each pixel: (h, w, 3) @ (3,) → (h, w), float from 0 to 255.
        #    Working in float avoids the overflows of uint8 (250 + 10 = 4 in uint8!).
        gray = image.astype(float) @ LUMA

        # 2. Stretch the contrast: the darkest 1 % goes to 0 and the lightest 1 % to 255.
        low, high = np.percentile(gray, [self.cutoff, 100 - self.cutoff])
        if high - low >= 1:  # a flat image is left as it is (and no division by zero)
            gray = np.clip((gray - low) / (high - low) * 255, 0, 255)

        # 3. Map each gray to the ramp: n colors evenly spread from 0 to 255,
        #    interpolating linearly between them, one channel at a time.
        stops = np.linspace(0, 255, len(self.colors))
        channels = [np.interp(gray, stops, self.colors[:, c]) for c in range(3)]

        # 4. Back to an image: (h, w, 3), rounded and converted to uint8.
        return np.rint(np.stack(channels, axis=-1)).astype(np.uint8)

    def __repr__(self) -> str:
        return f"GradientMap({len(self.colors)} colors)"


# ===========================================================================
# TODO (team): steps 1 to 6
# ===========================================================================

class SquareCrop(Step):
    """
    Step 1. Keeps the largest centered square of the image.

    The side of the square is the shorter side of the image. When the pixels
    left over cannot be split evenly, the extra one is cut on the right (or
    at the bottom).

Paso 1. Mantiene el cuadrado centrado más grande de la imagen.
El lado del cuadrado es el lado más corto de la imagen. Cuando los
 píxeles lo que sobra no se puede dividir uniformemente, el extra se 
 corta a la derecha (o en la parte inferior).


    """

    number = 1
    name = "square_crop"
    label = "Square crop"
    image = cv.imread("tps-proc-img/tp-3/backend/retro/retrato.png")
    window = np.array((512,512))

    def output_shape(self, height: int, width: int) -> tuple[int, int]:
        
        #height, width= image.shape[:2]      
        side = min(height, width)
        return side, side

    def apply(self, image: np.ndarray) -> np.ndarray:
        height, width= image.shape[:2] 

        out_height, out_width = self.output_shape(height, width)

        top = (height - out_height) // 2
        left = (width - out_width) // 2

        return image[
            top:top + out_height,
            left:left + out_width
        ]

        #raise StepNotImplemented(1, "SquareCrop")


class Shrink(Step):
    """
    Step 2. Shrinks the (square) image to `size` × `size` pixels.

    Each pixel of the result is the AVERAGE color of the block of the image it
    covers. If the side is not a multiple of `size`, the blocks may differ in
    one pixel.

    Paso 2. Reduce la imagen (cuadrada) a píxeles `size` × `size`.

    Cada píxel del resultado es el color PROMEDIO del bloque de la imagen
    cubre. Si el lado no es múltiplo de `tamaño`, los bloques pueden diferir
    un píxel.

    """

    number = 2
    name = "shrink"
    label = "Shrink"
    essential = True

    def __init__(self, size: int) -> None:
        self.size = size

    def output_shape(self, height: int, width: int) -> tuple[int, int]:
        return self.size, self.size

    def apply(self, image: np.ndarray) -> np.ndarray:
       
        height, width = image.shape[:2]

        result = np.zeros(
            (self.size, self.size, image.shape[2]),
            dtype=np.uint8
        )

        for y in range(self.size):
            for x in range(self.size):
                # limites
                y_start = y * height // self.size
                y_end = (y + 1) * height // self.size
                x_start = x * width // self.size
                x_end = (x + 1) * width // self.size

                # promedio
                block = image[y_start:y_end, x_start:x_end]
                result[y, x] = np.mean(block, axis=(0, 1))

        return result
        #raise StepNotImplemented(2, "Shrink")

    def __repr__(self) -> str:
        return f"Shrink({self.size})"


class Enlarge(Step):
    """
    Step 3. Enlarges the image `factor` times.

    Each pixel becomes a block of `factor` × `factor` pixels of exactly its
    color (nearest neighbor): no new colors appear.
    """

    number = 3
    name = "enlarge"
    label = "Enlarge"

    def __init__(self, factor: int) -> None:
        self.factor = factor

    def output_shape(self, height: int, width: int) -> tuple[int, int]:
        return height * self.factor, width * self.factor

    def apply(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]

        out_height, out_width = self.output_shape(height, width)

        result = np.zeros(
            (out_height, out_width, image.shape[2]),
            dtype=np.uint8
        )

        for y in range(height):
            for x in range(width):
                y_start = y * self.factor
                y_end = (y + 1) * self.factor

                x_start = x * self.factor
                x_end = (x + 1) * self.factor

                result[y_start:y_end, x_start:x_end] = image[y, x]

        return result
        #raise StepNotImplemented(3, "Enlarge")

    def __repr__(self) -> str:
        return f"Enlarge({self.factor})"


def nearest_color(color: np.ndarray, colors: np.ndarray) -> np.ndarray:
    """
    Step 4 (a). Returns the row of `colors` closest to `color`.

    - `color`: an (r, g, b) array. It may be uint8 or float, and in step 6 its
      values can even be below 0 or above 255.
    - `colors`: the palette, an (n, 3) uint8 array.

    The distance is the euclidean distance in RGB (the squared distance gives
    the same order). On a tie, the first one of the palette wins.
    """
    raise StepNotImplemented(4, "nearest_color")


class PaletteMap(Step):
    """
    Step 4 (b). Replaces each pixel by the nearest color of the palette.

    Use nearest_color. The result has only colors of the palette.
    """

    number = 4
    name = "palette_map"
    label = "Palette"

    def __init__(self, palette: Palette) -> None:
        self.palette = palette
        self.colors = palette.colors  # (n, 3) uint8

    def apply(self, image: np.ndarray) -> np.ndarray:
        raise StepNotImplemented(4, "PaletteMap")

    def __repr__(self) -> str:
        return f"PaletteMap({self.palette.name})"


class Frame(Step):
    """
    Step 5. Paints a frame of `thickness` pixels of `color` around the image.

    The frame is drawn over the border of the image (the size does not change).
    With thickness 0 the image is left as it is.
    """

    number = 5
    name = "frame"
    label = "Frame"

    def __init__(self, color: np.ndarray, thickness: int = 1) -> None:
        self.color = color          # (3,) uint8, e.g. palette.darkest
        self.thickness = thickness

    def apply(self, image: np.ndarray) -> np.ndarray:
        raise StepNotImplemented(5, "Frame")

    def __repr__(self) -> str:
        return f"Frame({self.thickness})"


class FloydSteinberg(Step):
    """
    Step 6. Like PaletteMap, but spreading the error with Floyd–Steinberg dithering.

    Pixels are visited from left to right and from top to bottom. The error of
    each pixel (its value minus the palette color it got) is added to the
    neighbors not yet visited: 7/16 to the right, 3/16 below-left, 5/16 below
    and 1/16 below-right. The error that falls outside the image is lost.
    """

    number = 6
    name = "floyd_steinberg"
    label = "Floyd–Steinberg"

    def __init__(self, palette: Palette) -> None:
        self.palette = palette
        self.colors = palette.colors  # (n, 3) uint8

    def apply(self, image: np.ndarray) -> np.ndarray:
        raise StepNotImplemented(6, "FloydSteinberg")

    def __repr__(self) -> str:
        return f"FloydSteinberg({self.palette.name})"
