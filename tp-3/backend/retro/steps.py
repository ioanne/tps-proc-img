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
import cv2
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

#Define una nueva clase llamada SquareCrop que hereda de la clase base Step. 
# Esto indica que este bloque de código es un "paso" estandarizado dentro del pipeline de procesamiento.

class SquareCrop(Step):
    """
    Step 1. Keeps the largest centered square of the image.

    The side of the square is the shorter side of the image. When the pixels
    left over cannot be split evenly, the extra one is cut on the right (or
    at the bottom).
    """
    ## Son atributos de clase fijos
    number = 1 #Define que este es el primer paso del pipeline.
    name = "square_crop" #El identificador técnico que usa el backend.
    label = "Square crop" #El texto ue se muestra en el frontend

# Es el método principal del paso. Recibe la imagen original en formato de matriz NumPy (np.ndarray) 
# y se compromete a devolver otra matriz NumPy ya procesada (-> np.ndarray
    def apply(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2] #Extrae las dos primeras dimensiones de la forma (shape) de la matriz de la imagen, 
        #guardándolas en las variables height (alto) y width (ancho). Se usa [:2] porque las imágenes a color tienen 3 dimensiones (alto, ancho, canales), pero para calcular el recorte solo nos interesan los ejes espaciales
        side = min(height, width) # calcula la lonigutd
        top = (height - side) // 2
        left = (width - side) // 2 #Calcula el punto de inicio (el "desplazamiento" u offset) para centrar el recorte
#Aplica el recorte sobre la matriz de NumPy
        return image[top:top + side, left:left + side]
#Define un método permite predecir qué dimensiones tendrá la imagen antes de ejecutar el procesamiento real, recibiendo el alto y ancho originales y devolviendo una tupla con las nuevas dimensiones.
    def output_shape(self, height: int, width: int) -> tuple[int, int]:
        side = min(height, width) #Vuelve a calcular el lado mínimo basándose en las dimensiones que entran y devuelve una tupla con dos valores iguales (side, side), confirmando que la salida siempre será un cuadrado
        return side, side


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
        return cv2.resize(image, (self.size, self.size), interpolation=cv2.INTER_AREA)
# Recibe la imagen ya recortada como matriz NumPy y un parámetro opcional. Esta opción realiza una interpolación por área
    def __repr__(self) -> str:
        return f"Shrink({self.size})"


class Enlarge(Step):
    #agramos la imagen multiplicando sus dimensiones por un factor. Usamos al vecino más cercano para que cada píxel se expanda en un bloque cuadrado idéntico
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
        return cv2.resize(image, (width * self.factor, height * self.factor), interpolation=cv2.INTER_NEAREST)

    def __repr__(self) -> str:
        return f"Enlarge({self.factor})"


def nearest_color(color: np.ndarray, colors: np.ndarray) -> np.ndarray:
#Buscamos el color de la paleta mas parecido del píxel, despues seleccionamos el color de la paleta que dio menor distancia
    """
    Step 4 (a). Returns the row of `colors` closest to `color`.

    - `color`: an (r, g, b) array. It may be uint8 or float, and in step 6 its
      values can even be below 0 or above 255.
    - `colors`: the palette, an (n, 3) uint8 array.

    The distance is the euclidean distance in RGB (the squared distance gives
    the same order). On a tie, the first one of the palette wins.
    """
    diff = colors.astype(float) - color.astype(float)
    dist_sq = np.sum(diff ** 2, axis=1)
    return colors[np.argmin(dist_sq)]


class PaletteMap(Step):
    #Transformamos la imagen para que solo use los colores de la paleta que se elija. Tambien se usa para hallar el color que mas se parezca y se reconstruya la img final
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
        # Convertir a float para evitar desbordamientos de uint8 en la resta
        img_float = image.astype(float)
        colors_float = self.colors.astype(float)
        
        diff = img_float[:, :, None, :] - colors_float[None, None, :, :]
        dist_sq = np.sum(diff ** 2, axis=-1)
        indices = np.argmin(dist_sq, axis=-1)
        return self.colors[indices]

    def __repr__(self) -> str:
        return f"PaletteMap({self.palette.name})"


class Frame(Step):
    #Hacemos el marco para la imagen con el color mas oscuro de la paleta.
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
        if self.thickness <= 0:
            return image.copy()
        
        result = image.copy()
        h, w, _ = result.shape
        t = self.thickness

        # Pintar los bordes superior, inferior, izquierdo y derecho
        result[:t, :] = self.color
        result[h - t:, :] = self.color
        result[:, :t] = self.color
        result[:, w - t:] = self.color

        return result

    def __repr__(self) -> str:
        return f"Frame({self.thickness})"


class FloydSteinberg(Step):
    #Aca logramos aplicar a la imagen que se utilicen mas colores con una paleta chica. Calculamos el color mas cercano y vemos la diferencia (pixel x pixel). 
    
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
        img = image.astype(float)
        h, w, _ = img.shape
        result = np.empty_like(image)

        for y in range(h):
            for x in range(w):
                old_pixel = img[y, x]
                new_pixel = nearest_color(old_pixel, self.colors)
                result[y, x] = new_pixel

                error = old_pixel - new_pixel.astype(float)

                if x + 1 < w:
                    img[y, x + 1] += error * (7 / 16)
                if y + 1 < h:
                    if x > 0:
                        img[y + 1, x - 1] += error * (3 / 16)
                    img[y + 1, x] += error * (5 / 16)
                    if x + 1 < w:
                        img[y + 1, x + 1] += error * (1 / 16)

        return result

    def __repr__(self) -> str:
        return f"FloydSteinberg({self.palette.name})"
