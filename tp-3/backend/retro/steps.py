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
from retro import PALETTES


import cv2
import numpy as np


from retro.exceptions import StepNotImplemented
from retro.palettes import LUMA, Palette


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
    """

    number = 1
    name = "square_crop"
    label = "Square crop"

    def output_shape(self, height: int, width: int) -> tuple[int, int]:
        side = min(height, width)
        return side, side

    def apply(self, image: np.ndarray) -> np.ndarray:
        #raise StepNotImplemented(1, "SquareCrop")
        height, width = image.shape[:2] #image.shape devuelve (alto, ancho, 3). Con el corte [:2] se obtienen únicamente las dimensiones espaciales para hacer las cuentas del recorte
        side = min(height, width)  # Encuentra el lado mas pequeño
        top = (height - side) // 2 # Calcula cuántas filas se descartan en la parte superior
        left = (width - side) // 2 # Calcula cuántas columnas se descartan del lado izquierdo, si la cantidad sobrante es impar (por ejemplo 3), asigna 1 a la izquierda y deja 2 a la derecha, cumpliendo la regla de recortar el sobrante impar a la derecha
        return image[top : top + side, left : left + side] # Recorta y devuelve la porción central de la imagen con tamaño side × side



class Shrink(Step):
    """
    Step 2. Shrinks the (square) image to `size` × `size` pixels.

    Each pixel of the result is the AVERAGE color of the block of the image it
    covers. If the side is not a multiple of `size`, the blocks may differ in
    one pixel.
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
        #raise StepNotImplemented(2, "Shrink")
        return cv2.resize(
            image, (self.size, self.size), interpolation=cv2.INTER_AREA #INTER_AREA superpone la cuadrícula de la imagen de destino sobre la imagen original
        )
    
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
        #raise StepNotImplemented(3, "Enlarge")
        expandir = np.repeat(image, self.factor, axis=1) # 1 representa columnas
        return np.repeat(expandir, self.factor, axis=0) # 2 representa filas

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
    #raise StepNotImplemented(4, "nearest_color")

    differences = colors.astype(float) - color.astype(float) # 1. Convertir a float antes de restar para evitar que uint8 desborde
    distances = np.sum(differences**2, axis=1) # 2. Calcular la distancia al cuadrado d^2 sumando sobre los canales RGB (axis=1)
    return colors[np.argmin(distances)] # 3. Devolver la fila de la paleta con la distancia mínima (en empate gana el primero)
             


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
        height, width = image.shape[:2]
        result = np.empty_like(image)  # mismo tamaño y dtype, sin inicializar
        for y in range(height):
            for x in range(width):
                result[y, x] = nearest_color(image[y, x], self.colors)
        return result

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
        #raise StepNotImplemented(5, "Frame")
        if self.thickness <= 0:
            return image.copy()

        result = image.copy()
        t = self.thickness

        result[:t, :] = self.color    # Arriba
        result[-t:, :] = self.color   # Abajo
        result[:, :t] = self.color    # Izquierda
        result[:, -t:] = self.color   # Derecha

        return result

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
