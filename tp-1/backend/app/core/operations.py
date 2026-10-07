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

from PIL import Image, ImageEnhance, ImageOps
import cv2
import numpy as np

from app.core.exceptions import NotImplementedFeature, InvalidParameters


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
    name = "brightness"


    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Brightness(image).enhance(self._parameters["factor"])   


class Contrast(Operation):
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Contrast(image).enhance(self._parameters["factor"])


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Color(image).enhance(self._parameters["factor"])


class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageEnhance.Sharpness(image).enhance(self._parameters["factor"])


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageOps.grayscale(image)


class Blur(Operation):
    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        if kernel_size % 2 == 0 or kernel_size < 1:
            raise InvalidParameters(
                "Kernel size must be a positive odd integer."
            )

        super().__init__(method=method, kernel_size=kernel_size)

        self._method = method.lower()
        self._kernel_size = kernel_size

    def apply(self, image: Image.Image) -> Image.Image:
        pixels = np.array(image)
        kernel = self._kernel_size

        if self._method == "gaussian":
            result = cv2.GaussianBlur(pixels, (kernel, kernel), 0)
        elif self._method == "average":
            result = cv2.blur(pixels, (kernel, kernel))
        else:
            result = cv2.medianBlur(pixels, kernel)

        return Image.fromarray(result)


class Edges(Operation):
    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        # TODO: domain rule, lower_threshold < upper_threshold.
        super().__init__(lower_threshold=lower_threshold, upper_threshold=upper_threshold)

    def apply(self, image: Image.Image) -> Image.Image:
       return Image.fromarray(cv2.Canny(np.array(image), self._parameters["lower_threshold"], self._parameters["upper_threshold"]))


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

    def __init__(
        self,
        width: int,
        height: int | None = None,
        keep_aspect_ratio: bool = False,
    ) -> None:

        if width <= 0:
            raise InvalidParameters("Width must be positive.")

        if not keep_aspect_ratio:
            if height is None or height <= 0:
                raise InvalidParameters(
                    "Height must be a positive integer."
                )

        super().__init__(
            width=width,
            height=height,
            keep_aspect_ratio=keep_aspect_ratio,
        )
    def apply(self, image: Image.Image) -> Image.Image:
        width = self._parameters["width"]
        height = self._parameters["height"]

        if self._parameters["keep_aspect_ratio"]:
            height = max(1, round(width * image.height / image.width))
        elif height is None:
            raise InvalidParameters(
                "Height is required when keep_aspect_ratio is false."
            )

        interpolation = (
            cv2.INTER_AREA
            if width <= image.width and height <= image.height
            else cv2.INTER_CUBIC
        )

        pixels = np.asarray(image)
        resized = cv2.resize(
            pixels,
            (width, height),
            interpolation=interpolation,
        )
        return Image.fromarray(resized)