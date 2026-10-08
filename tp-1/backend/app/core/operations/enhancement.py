from collections.abc import Callable
from typing import ClassVar, Protocol

from PIL import Image, ImageEnhance

from app.core.operations.base import Operation


class Enhancer(Protocol):
    def enhance(self, factor: float) -> Image.Image: ...


class EnhanceOperation(Operation):
    enhancer: ClassVar[Callable[[Image.Image], Enhancer]]

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self._factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        return self.enhancer(image).enhance(self._factor)


class Brightness(EnhanceOperation):
    name = "brightness"
    enhancer = ImageEnhance.Brightness


class Contrast(EnhanceOperation):
    name = "contrast"
    enhancer = ImageEnhance.Contrast


class Saturation(EnhanceOperation):
    name = "saturation"
    enhancer = ImageEnhance.Color


class Sharpness(EnhanceOperation):
    name = "sharpness"
    enhancer = ImageEnhance.Sharpness
