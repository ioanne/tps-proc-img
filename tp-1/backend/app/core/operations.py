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

from PIL import Image

from app.core.exceptions import NotImplementedFeature


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
        raise NotImplementedFeature("Brightness")


class Contrast(Operation):
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Contrast")


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Saturation")


class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Sharpness")


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Grayscale")


class Blur(Operation):
    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        # TODO: domain rule, kernel_size must be odd.
        super().__init__(method=method, kernel_size=kernel_size)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Blur")


class Edges(Operation):
    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        # TODO: domain rule, lower_threshold < upper_threshold.
        super().__init__(lower_threshold=lower_threshold, upper_threshold=upper_threshold)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Edge detection")


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
