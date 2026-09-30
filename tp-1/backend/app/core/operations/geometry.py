from typing import ClassVar

from PIL import Image

from app.core.exceptions import InvalidParameters
from app.core.operations.base import Operation


class Rotation(Operation):
    name = "rotation"

    def __init__(self, angle: float = 90.0, expand: bool = True) -> None:
        super().__init__(angle=angle, expand=expand)
        self._angle = angle
        self._expand = expand

    def apply(self, image: Image.Image) -> Image.Image:
        return image.rotate(self._angle, resample=Image.Resampling.BICUBIC, expand=self._expand)


class Mirror(Operation):
    name = "mirror"
    directions: ClassVar[dict[str, Image.Transpose]] = {
        "horizontal": Image.Transpose.FLIP_LEFT_RIGHT,
        "vertical": Image.Transpose.FLIP_TOP_BOTTOM,
    }

    def __init__(self, direction: str = "horizontal") -> None:
        if direction not in self.directions:
            raise InvalidParameters(
                f"Unknown mirror direction '{direction}'. Use horizontal or vertical."
            )
        super().__init__(direction=direction)
        self._transpose = self.directions[direction]

    def apply(self, image: Image.Image) -> Image.Image:
        return image.transpose(self._transpose)


class Resize(Operation):
    name = "resize"

    def __init__(
        self, width: int, height: int | None = None, keep_aspect_ratio: bool = True
    ) -> None:
        if not keep_aspect_ratio and height is None:
            raise InvalidParameters("The height is required when the aspect ratio is not kept.")
        super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)
        self._width = width
        self._height = height
        self._keep_aspect_ratio = keep_aspect_ratio

    def apply(self, image: Image.Image) -> Image.Image:
        return image.resize((self._width, self._target_height(image)), Image.Resampling.LANCZOS)

    def _target_height(self, image: Image.Image) -> int:
        if self._height is None or self._keep_aspect_ratio:
            return max(1, round(self._width * image.height / image.width))
        return self._height
