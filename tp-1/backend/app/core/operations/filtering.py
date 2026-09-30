from abc import ABC, abstractmethod
from typing import ClassVar

import cv2
import numpy as np

from app.core.exceptions import InvalidParameters
from app.core.operations.base import ArrayOperation
from app.core.operations.conversion import ArrayConverter


class BlurMethod(ABC):
    @abstractmethod
    def blur(self, array: np.ndarray, kernel_size: int) -> np.ndarray: ...


class GaussianBlur(BlurMethod):
    def blur(self, array: np.ndarray, kernel_size: int) -> np.ndarray:
        return cv2.GaussianBlur(array, (kernel_size, kernel_size), 0)


class MedianBlur(BlurMethod):
    def blur(self, array: np.ndarray, kernel_size: int) -> np.ndarray:
        return cv2.medianBlur(array, kernel_size)


class AverageBlur(BlurMethod):
    def blur(self, array: np.ndarray, kernel_size: int) -> np.ndarray:
        return cv2.blur(array, (kernel_size, kernel_size))


class Blur(ArrayOperation):
    name = "blur"
    methods: ClassVar[dict[str, BlurMethod]] = {
        "gaussian": GaussianBlur(),
        "median": MedianBlur(),
        "average": AverageBlur(),
    }

    def __init__(
        self,
        method: str = "gaussian",
        kernel_size: int = 5,
        converter: ArrayConverter | None = None,
    ) -> None:
        if method not in self.methods:
            raise InvalidParameters(
                f"Unknown blur method '{method}'. Use gaussian, median or average."
            )
        if kernel_size % 2 == 0:
            raise InvalidParameters(f"The kernel size must be odd, got {kernel_size}.")
        super().__init__(converter, method=method, kernel_size=kernel_size)
        self._method = self.methods[method]
        self._kernel_size = kernel_size

    def process(self, array: np.ndarray) -> np.ndarray:
        return self._method.blur(array, self._kernel_size)
