"""
Image editing operations.

`Operation` is the contract the service relies on: a `name` (the one of the
route and of `ImageOut.operation`), the `parameters` that are stored in the
database and an `apply` method that works on an image in memory.

TODO (teams): implement the ten operations. Each one validates its domain rules
in the constructor (raising `InvalidParameters`) and implements `apply`.
The constructor arguments match the fields of the schemas in `app/schemas.py`.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from app.core.exceptions import InvalidParameters
from app.core.imaging import cv2_to_pil, pil_to_cv2


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

class EnhanceOperation(Operation):
    """Base para operaciones Pillow ImageEnhance."""

    _enhancer_class: ClassVar

    def apply(self, image: Image.Image) -> Image.Image:
        factor = self._parameters["factor"]

        if image.mode == "RGBA":
            r, g, b, a = image.split()
            rgb = Image.merge("RGB", (r, g, b))
            enhanced = self._enhancer_class(rgb).enhance(factor)
            return Image.merge("RGBA", (*enhanced.split(), a))

        return self._enhancer_class(image).enhance(factor)

class Brightness(EnhanceOperation):
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
    _enhancer_class = ImageEnhance.Brightness

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

class Contrast(EnhanceOperation):
    name = "contrast"
    _enhancer_class = ImageEnhance.Contrast

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

   


class Saturation(EnhanceOperation):
    name = "saturation"
    _enhancer_class = ImageEnhance.Color

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)




class Sharpness(EnhanceOperation):
    name = "sharpness"
    _enhancer_class = ImageEnhance.Sharpness

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)




class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "L":
            return image.copy()

        rgb = image.convert("RGB")
        gray = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2GRAY)

        return Image.fromarray(gray, mode="L")


class Blur(Operation):
    name = "blur"

    def __init__(
        self,
        method: str = "gaussian",
        kernel_size: int = 5,
    ) -> None:
        if kernel_size % 2 == 0:
            raise InvalidParameters("kernel_size must be odd.")

        super().__init__(
            method=method,
            kernel_size=kernel_size,
        )
        self.method = method
        self.kernel_size = kernel_size

    def apply(self, image: Image.Image) -> Image.Image:
        original_mode = image.mode
        cv_array = pil_to_cv2(image)
        ksize = (self.kernel_size, self.kernel_size)

        if self.method == "gaussian":
            result = cv2.GaussianBlur(cv_array, ksize, 0)
        elif self.method == "median":
            result = cv2.medianBlur(cv_array, self.kernel_size)
        else:
            result = cv2.blur(cv_array, ksize)

        return cv2_to_pil(result, original_mode)


class Edges(Operation):
    name = "edges"

    def __init__(
        self,
        lower_threshold: int = 100,
        upper_threshold: int = 200,
    ) -> None:
        if lower_threshold >= upper_threshold:
            raise InvalidParameters(
                "lower_threshold must be less than upper_threshold."
            )

        super().__init__(
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
        )
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "L":
            gray = np.array(image)
        else:
            gray = cv2.cvtColor(
                np.array(image.convert("RGB")),
                cv2.COLOR_RGB2GRAY,
            )

        edges = cv2.Canny(
            gray,
            self.lower_threshold,
            self.upper_threshold,
        )

        return Image.fromarray(edges, mode="L")

class Rotation(Operation):
    name = "rotation"

    def __init__(
        self,
        angle: float = 90.0,
        expand: bool = True,
    ) -> None:
        super().__init__(angle=angle, expand=expand)
        self.angle = angle
        self.expand = expand

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "RGBA":
            fill = (0, 0, 0, 0)
        elif image.mode == "L":
            fill = 0
        else:
            fill = (0, 0, 0)

        return image.rotate(
            self.angle,
            expand=self.expand,
            fillcolor=fill,
        )


class Mirror(Operation):
    name = "mirror"

    def __init__(self, direction: str = "horizontal") -> None:
        super().__init__(direction=direction)
        self.direction = direction

    def apply(self, image: Image.Image) -> Image.Image:
        if self.direction == "horizontal":
            return ImageOps.mirror(image)

        return ImageOps.flip(image)

class Resize(Operation):
    name = "resize"

    def __init__(
        self,
        width: int,
        height: int | None = None,
        keep_aspect_ratio: bool = True,
    ) -> None:
        if not keep_aspect_ratio and height is None:
            raise InvalidParameters(
                "height is required when keep_aspect_ratio is false."
            )

        super().__init__(
            width=width,
            height=height,
            keep_aspect_ratio=keep_aspect_ratio,
        )
        self.width = width
        self.height = height
        self.keep_aspect_ratio = keep_aspect_ratio

    def apply(self, image: Image.Image) -> Image.Image:
        orig_w, orig_h = image.size

        if self.keep_aspect_ratio:
            new_h = round(self.width * orig_h / orig_w)
        else:
            new_h = self.height

        return image.resize(
            (self.width, new_h),
            Image.Resampling.LANCZOS,
        )
