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
from PIL import Image, ImageEnhance
from PIL import ImageOps

from app.core.exceptions import InvalidParameters


def _to_opencv(image: Image.Image) -> np.ndarray:
    """Convert a normalized Pillow image to OpenCV's channel order."""
    pixels = np.asarray(image)
    if image.mode == "RGB":
        return cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)
    if image.mode == "RGBA":
        return cv2.cvtColor(pixels, cv2.COLOR_RGBA2BGRA)
    return pixels


def _from_opencv(pixels: np.ndarray, mode: str) -> Image.Image:
    """Convert OpenCV pixels back to a Pillow image in the original mode."""
    if mode == "RGB":
        pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)
    elif mode == "RGBA":
        pixels = cv2.cvtColor(pixels, cv2.COLOR_BGRA2RGBA)
    return Image.fromarray(pixels)


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
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            rgb = image.convert("RGB")
            result = ImageEnhance.Brightness(rgb).enhance(self.factor).convert("RGBA")
            result.putalpha(alpha)
            return result

        return ImageEnhance.Brightness(image).enhance(self.factor)


class Contrast(Operation):
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            rgb = image.convert("RGB")
            result = ImageEnhance.Contrast(rgb).enhance(self.factor).convert("RGBA")
            result.putalpha(alpha)
            return result

        return ImageEnhance.Contrast(image).enhance(self.factor)


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            rgb = image.convert("RGB")
            result = ImageEnhance.Color(rgb).enhance(self.factor).convert("RGBA")
            result.putalpha(alpha)
            return result

        return ImageEnhance.Color(image).enhance(self.factor)


class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            rgb = image.convert("RGB")
            result = ImageEnhance.Sharpness(rgb).enhance(self.factor).convert("RGBA")
            result.putalpha(alpha)
            return result

        return ImageEnhance.Sharpness(image).enhance(self.factor)


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageOps.grayscale(image)


class Blur(Operation):
    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        if kernel_size % 2 == 0:
            raise InvalidParameters("kernel_size must be odd.")
        super().__init__(method=method, kernel_size=kernel_size)
        self.method = method
        self.kernel_size = kernel_size

    def apply(self, image: Image.Image) -> Image.Image:
        filters = {
            "gaussian": lambda pixels, size: cv2.GaussianBlur(pixels, (size, size), 0),
            "median": lambda pixels, size: cv2.medianBlur(pixels, size),
            "average": lambda pixels, size: cv2.blur(pixels, (size, size)),
        }
        pixels = _to_opencv(image)
        result = filters[self.method](pixels, self.kernel_size)
        return _from_opencv(result, image.mode)


class Edges(Operation):
    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        if lower_threshold >= upper_threshold:
            raise InvalidParameters("lower_threshold must be less than upper_threshold.")
        super().__init__(lower_threshold=lower_threshold, upper_threshold=upper_threshold)
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold

    def apply(self, image: Image.Image) -> Image.Image:
        pixels = _to_opencv(image)
        grayscale_codes = {
            "L": None,
            "RGB": cv2.COLOR_BGR2GRAY,
            "RGBA": cv2.COLOR_BGRA2GRAY,
        }
        grayscale = (
            pixels
            if image.mode == "L"
            else cv2.cvtColor(pixels, grayscale_codes[image.mode])
        )
        edges = cv2.Canny(grayscale, self.lower_threshold, self.upper_threshold)
        return Image.fromarray(edges, mode="L")


class Rotation(Operation):
    name = "rotation"

    def __init__(self, angle: float = 90.0, expand: bool = True) -> None:
        super().__init__(angle=angle, expand=expand)
        self.angle = angle
        self.expand = expand

    def apply(self, image: Image.Image) -> Image.Image:
        fill = (0, 0, 0, 0) if image.mode == "RGBA" else 0
        return image.rotate(
            self.angle,
            resample=Image.Resampling.BICUBIC,
            expand=self.expand,
            fillcolor=fill,
        )


class Mirror(Operation):
    name = "mirror"

    def __init__(self, direction: str = "horizontal") -> None:
        super().__init__(direction=direction)
        self.direction = direction

    def apply(self, image: Image.Image) -> Image.Image:
        transforms = {
            "horizontal": Image.Transpose.FLIP_LEFT_RIGHT,
            "vertical": Image.Transpose.FLIP_TOP_BOTTOM,
        }
        return image.transpose(transforms[self.direction])


class Resize(Operation):
    name = "resize"

    def __init__(self, width: int, height: int | None = None, keep_aspect_ratio: bool = True) -> None:
        if not keep_aspect_ratio and height is None:
            raise InvalidParameters("height is required when keep_aspect_ratio is false.")
        super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)
        self.width = width
        self.height = height
        self.keep_aspect_ratio = keep_aspect_ratio

    def apply(self, image: Image.Image) -> Image.Image:
        if self.keep_aspect_ratio:
            height = round(self.width * image.height / image.width)
        else:
            assert self.height is not None
            height = self.height
        return image.resize(
            (self.width, height),
            resample=Image.Resampling.LANCZOS,
        )
