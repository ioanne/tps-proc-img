import cv2
import numpy as np
from PIL import Image, ImageOps

from app.core.exceptions import InvalidParameters
from app.core.operations.base import ArrayOperation
from app.core.operations.conversion import ArrayConverter


class Edges(ArrayOperation):
    name = "edges"

    def __init__(
        self,
        lower_threshold: int = 100,
        upper_threshold: int = 200,
        converter: ArrayConverter | None = None,
    ) -> None:
        if lower_threshold >= upper_threshold:
            raise InvalidParameters(
                f"The lower threshold ({lower_threshold}) must be lower than "
                f"the upper threshold ({upper_threshold})."
            )
        super().__init__(
            converter, lower_threshold=lower_threshold, upper_threshold=upper_threshold
        )
        self._lower_threshold = lower_threshold
        self._upper_threshold = upper_threshold

    def apply(self, image: Image.Image) -> Image.Image:
        return super().apply(ImageOps.grayscale(image))

    def process(self, array: np.ndarray) -> np.ndarray:
        return cv2.Canny(array, self._lower_threshold, self._upper_threshold)
