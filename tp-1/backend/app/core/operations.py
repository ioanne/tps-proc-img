"""
Image editing operations.

`Operation` is the contract the service relies on: a `name` (the one of the
route and of `ImageOut.operation`), the `parameters` that are stored in the
database and an `apply` method that works on an image in memory.

TODO (teams): implement the ten operations. Each one validates its domain rules
in the constructor (raising `InvalidParameters`) and implements `apply`.
The constructor arguments match the fields of the schemas in `app/schemas.py`.
"""

import cv2 #PARA ALGUNSO CAMBIOS LOS NECESITO
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
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Contrast(image).enhance(self.parameters["factor"])


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Color(image).enhance(self.parameters["factor"])


class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Sharpness(image).enhance(self.parameters["factor"])


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageOps.grayscale(image)


class Blur(Operation): #con OpenCV
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
    name = "rotation"

    def __init__(self, angle: float = 90.0, expand: bool = True) -> None:
        super().__init__(angle=angle, expand=expand)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Rotation")


class Mirror(Operation):
    name = "mirror"

    def __init__(self, direction: str = "horizontal") -> None:
        super().__init__(direction=direction)

    def apply(self, image: Image.Image) -> Image.Image:
        direction = self.parameters["direction"]

        if direction == "horizontal":
            return ImageOps.mirror(image)

        return ImageOps.flip(image)


class Resize(Operation):
    name = "resize"

    def __init__(self, width: int, height: int | None = None, keep_aspect_ratio: bool = True) -> None:
        # TODO: domain rule, height is required if keep_aspect_ratio is false.
        super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Resize")
