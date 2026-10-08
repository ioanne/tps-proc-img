"""
Image editing operations.

`Operation` is the contract the service relies on: a `name` (the one of the
route and of `ImageOut.operation`), the `parameters` that are stored in the
database and an `apply` method that works on an image in memory.

TODO (teams): implement the ten operations. Each one validates its domain rules
in the constructor (raising `InvalidParameters`) and implements `apply`.
The constructor arguments match the fields of the schemas in `app/schemas.py`.
"""

import cv2 #PARA ALGUNOS CAMBIOS LOS NECESITO
import numpy as np

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from PIL import Image, ImageEnhance, ImageOps #voy cambiando a medida que cambio los raise

from app.core.exceptions import InvalidParameters, NotImplementedFeature #agregado por el blur (invalid parameters)

def pil_to_cv(image: Image.Image) -> np.ndarray:
    array = np.array(image)

    if image.mode == "RGB":
        return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)

    if image.mode == "RGBA":
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGRA)

    return array


def cv_to_pil(array: np.ndarray, mode: str) -> Image.Image:
    if mode == "RGB":
        array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)

    elif mode == "RGBA":
        array = cv2.cvtColor(array, cv2.COLOR_BGRA2RGBA)

    return Image.fromarray(array)


class Operation(ABC):
    name: ClassVar[str]

    def __init__(self, **parameters: Any) -> None:
        self._parameters = parameters

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    @abstractmethod
    def apply(self, image: Image.Image) -> Image.Image:
        """Returns a NEW image with the operation applied. `image` must not be modified."""
        


class Brightness(Operation):
    """Adjusts the brightness of the image by `factor`: 0 = black, 1.0 = unchanged.

    How the parameters get here (the other nine operations work the same way):

      1. The client sends `POST /api/images/{id}/brightness` with the JSON body
         `{"factor": 1.5}`. The fields are optional: `{}` means `factor = 1.0`
         (but the body itself is required: no body at all is a 422).
      2. FastAPI parses the body into `schemas.BrightnessIn` and validates the
         ranges declared there (0 <= factor <= 3). If they are not met it answers
         422 on its own: this class never sees an out-of-range `factor`.
      3. The router (`routers/operations.py`) builds the operation with
         `Brightness(**params.model_dump())`, i.e. `Brightness(factor=1.5)`. The
         constructor arguments are the schema fields, same names, already typed
         (`factor` is a `float`) and with the defaults applied.
      4. The constructor validates the domain rules the schema cannot express
         (raising `InvalidParameters` -> 400; brightness has none) and passes
         the values to `super().__init__`. That dict is what `self.parameters`
         returns and what the service stores in the database and returns in
         `ImageOut.parameters` (`{"factor": 1.5}`), so it must keep the same keys
         as the schema.
      5. The router hands the operation to `ImageService.apply`, which opens the
         source image and calls `apply(image)`. Inside `apply` the values are read
         from `self.parameters["factor"]` (or from an attribute the constructor
         saved, e.g. `self.factor`).
    """

    name = "brightness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Brightness(image).enhance(self.factor)


class Contrast(Operation):
    """Ajusta el contraste de la imagen según `factor`.

    El contraste es la diferencia entre las zonas claras y las oscuras.
    0 = imagen gris uniforme, 1.0 = sin cambios, mayor a 1 = más contraste.
    Usa ImageEnhance.Contrast de Pillow.
    """

    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Contrast(image).enhance(self.parameters["factor"])


class Saturation(Operation):
    """Ajusta la saturación (intensidad de los colores) según `factor`.

    0 = blanco y negro, 1.0 = sin cambios, mayor a 1 = colores más vivos.
    Usa ImageEnhance.Color de Pillow.
    """

    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Color(image).enhance(self.parameters["factor"])


class Sharpness(Operation):
    """Ajusta la nitidez de la imagen según `factor`.

    Menor a 1 = más borrosa, 1.0 = sin cambios, mayor a 1 = bordes más marcados.
    Usa ImageEnhance.Sharpness de Pillow.
    """

    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Sharpness(image).enhance(self.parameters["factor"])


class Grayscale(Operation):
    """Convierte la imagen a escala de grises (blanco y negro).

    No recibe parámetros. El resultado tiene un solo canal (modo "L"),
    donde cada píxel es un valor de brillo entre 0 (negro) y 255 (blanco).
    """

    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageOps.grayscale(image)


class Blur(Operation): #con OpenCV
    """Desenfoca la imagen usando OpenCV.

    Parámetros:
      - method: "gaussian" (suave y natural), "median" (bueno para quitar
        ruido tipo puntitos) o "box" (promedio simple de los vecinos).
      - kernel_size: tamaño de la ventana de píxeles vecinos que se usa.
        Tiene que ser impar para que exista un píxel central; si es par se
        lanza InvalidParameters. Con 1 la imagen queda igual.
    Cuanto más grande el kernel, más borrosa queda la imagen.
    """

    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        if kernel_size % 2 == 0:
            raise InvalidParameters("The kernel size must be odd.")

        super().__init__(method=method, kernel_size=kernel_size)

    def apply(self, image: Image.Image) -> Image.Image:
        method = self.parameters["method"]
        kernel_size = self.parameters["kernel_size"]

        if kernel_size == 1:
            return image.copy()

        cv_image = pil_to_cv(image)

        if method == "gaussian":
            result = cv2.GaussianBlur(
                cv_image,
                (kernel_size, kernel_size),
                0
            )
        elif method == "median":
            result = cv2.medianBlur(cv_image, kernel_size)
        else:
            result = cv2.blur(
                cv_image,
                (kernel_size, kernel_size)
            )

        return cv_to_pil(result, image.mode)


class Edges(Operation):
    """Detecta los bordes de la imagen con el algoritmo de Canny (OpenCV).

    Primero pasa la imagen a gris y después marca en blanco los bordes
    y en negro el resto.
      - lower_threshold / upper_threshold: umbrales del algoritmo. Los cambios
        de intensidad mayores al umbral alto son bordes seguros; los que están
        entre ambos solo cuentan si están conectados a un borde seguro.
    El umbral bajo tiene que ser menor que el alto (si no, InvalidParameters).
    """

    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        if lower_threshold >= upper_threshold:
            raise InvalidParameters("The lower threshold must be smaller than the upper threshold.")

        super().__init__(lower_threshold=lower_threshold, upper_threshold=upper_threshold)

    def apply(self, image: Image.Image) -> Image.Image:
        cv_image = pil_to_cv(image)

        if image.mode == "RGBA":
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2GRAY)
        elif image.mode == "RGB":
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv_image

        edges = cv2.Canny(
            gray,
            self.parameters["lower_threshold"],
            self.parameters["upper_threshold"]
        )

        return Image.fromarray(edges)


class Rotation(Operation):
    """Rota la imagen `angle` grados en sentido antihorario.

      - expand: si es True, agranda el lienzo para que no se corte ninguna
        parte de la imagen; si es False, mantiene el tamaño original.
    Las esquinas que quedan vacías se rellenan con negro (o transparente
    si la imagen tiene canal alfa, RGBA).
    """

    name = "rotation"

    def __init__(self, angle: float = 90.0, expand: bool = True) -> None:
        super().__init__(angle=angle, expand=expand)

    def apply(self, image: Image.Image) -> Image.Image:
        angle = self.parameters["angle"]
        expand = self.parameters["expand"]

        if image.mode == "RGBA":
            fill = (0, 0, 0, 0)
        elif image.mode == "RGB":
            fill = (0, 0, 0)
        else:
            fill = 0

        return image.rotate(
            angle,
            expand=expand,
            fillcolor=fill
        )


class Mirror(Operation):
    """Refleja la imagen como un espejo.

      - direction: "horizontal" da vuelta izquierda/derecha;
        cualquier otro valor ("vertical") da vuelta arriba/abajo.
    """

    name = "mirror"

    def __init__(self, direction: str = "horizontal") -> None:
        super().__init__(direction=direction)

    def apply(self, image: Image.Image) -> Image.Image:
        direction = self.parameters["direction"]

        if direction == "horizontal":
            return ImageOps.mirror(image)

        return ImageOps.flip(image)


class Resize(Operation):
    """Cambia el tamaño de la imagen usando OpenCV.

      - width: ancho nuevo en píxeles.
      - height: alto nuevo (opcional si se mantiene la proporción).
      - keep_aspect_ratio: si es True, el alto se calcula solo para que la
        imagen no se deforme; si es False, `height` es obligatorio
        (si falta, InvalidParameters).
    Para achicar usa INTER_AREA (evita que se vea "pixelado") y para
    agrandar usa INTER_CUBIC (da un resultado más suave).
    """

    name = "resize"

    def __init__(
        self,
        width: int,
        height: int | None = None,
        keep_aspect_ratio: bool = True
    ) -> None:

        if not keep_aspect_ratio and height is None:
            raise InvalidParameters(
                "Height is required when keep_aspect_ratio is false."
            )

        super().__init__(
            width=width,
            height=height,
            keep_aspect_ratio=keep_aspect_ratio
        )

    def apply(self, image: Image.Image) -> Image.Image:
        width = self.parameters["width"]
        height = self.parameters["height"]
        keep_aspect_ratio = self.parameters["keep_aspect_ratio"]

        if keep_aspect_ratio:
            height = round(width * image.height / image.width)

        cv_image = pil_to_cv(image)

        if width < image.width or height < image.height:
            interpolation = cv2.INTER_AREA
        else:
            interpolation = cv2.INTER_CUBIC

        result = cv2.resize(
            cv_image,
            (width, height),
            interpolation=interpolation
        )

        return cv_to_pil(result, image.mode)