from PIL import Image, ImageOps

from app.core.operations.base import Operation


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        return ImageOps.grayscale(image)
