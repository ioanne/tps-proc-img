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
from PIL import Image, ImageEnhance, ImageFilter

from app.core.exceptions import InvalidParameters, NotImplementedFeature


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
        factor = self._parameters["factor"]
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            enhanced = ImageEnhance.Brightness(image.convert("RGB")).enhance(factor)
            enhanced.putalpha(alpha)
            return enhanced
        return ImageEnhance.Brightness(image).enhance(factor)


class Contrast(Operation):
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        factor = self._parameters["factor"]
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            enhanced = ImageEnhance.Contrast(image.convert("RGB")).enhance(factor)
            enhanced.putalpha(alpha)
            return enhanced
        if image.mode == "P":
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            if image.mode == "RGBA":
                alpha = image.getchannel("A")
                enhanced = ImageEnhance.Contrast(image.convert("RGB")).enhance(factor)
                enhanced.putalpha(alpha)
                return enhanced
        return ImageEnhance.Contrast(image).enhance(factor)


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        factor = self._parameters["factor"]
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            enhanced = ImageEnhance.Color(image.convert("RGB")).enhance(factor)
            enhanced.putalpha(alpha)
            return enhanced
        if image.mode == "P":
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            if image.mode == "RGBA":
                alpha = image.getchannel("A")
                enhanced = ImageEnhance.Color(image.convert("RGB")).enhance(factor)
                enhanced.putalpha(alpha)
                return enhanced
        return ImageEnhance.Color(image).enhance(factor)


class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        factor = self._parameters["factor"]
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            enhanced = ImageEnhance.Sharpness(image.convert("RGB")).enhance(factor)
            enhanced.putalpha(alpha)
            return enhanced
        if image.mode == "P":
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            if image.mode == "RGBA":
                alpha = image.getchannel("A")
                enhanced = ImageEnhance.Sharpness(image.convert("RGB")).enhance(factor)
                enhanced.putalpha(alpha)
                return enhanced
        return ImageEnhance.Sharpness(image).enhance(factor)


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        return image.convert("L")


class Blur(Operation):
    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        if kernel_size % 2 == 0:
            raise InvalidParameters("kernel_size must be odd.")

        super().__init__(method=method, kernel_size=kernel_size)
        self.method = method
        self.kernel_size = kernel_size

    def apply(self, image: Image.Image) -> Image.Image:
        radius = (self.kernel_size - 1) / 2

        if self.method == "gaussian":
            image_filter = ImageFilter.GaussianBlur(radius=radius)
        elif self.method == "average":
            image_filter = ImageFilter.BoxBlur(radius=radius)
        elif self.method == "median":
            image_filter = ImageFilter.MedianFilter(size=self.kernel_size)
        else:
            raise InvalidParameters(f"Unsupported blur method: {self.method}")

        return image.filter(image_filter)


class Edges(Operation):
    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        if lower_threshold >= upper_threshold:
            raise InvalidParameters("lower_threshold must be less than upper_threshold.")

        super().__init__(
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
        )
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold

    def apply(self, image: Image.Image) -> Image.Image:
        grayscale = np.asarray(image.convert("L"))
        edges = cv2.Canny(grayscale, self.lower_threshold, self.upper_threshold)
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
        raise NotImplementedFeature("Mirror")


class Resize(Operation):
    name = "resize"

    def __init__(self, width: int, height: int | None = None, keep_aspect_ratio: bool = True) -> None:
        # TODO: domain rule, height is required if keep_aspect_ratio is false.
        super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Resize")
