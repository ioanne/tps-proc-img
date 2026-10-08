from abc import ABC, abstractmethod
from typing import ClassVar

import cv2
import numpy as np
from PIL import Image


class ArrayConverter(ABC):
    @abstractmethod
    def to_array(self, image: Image.Image) -> np.ndarray: ...

    @abstractmethod
    def to_image(self, array: np.ndarray) -> Image.Image: ...


class OpenCVConverter(ArrayConverter):
    _to_bgr: ClassVar[dict[str, int]] = {"RGB": cv2.COLOR_RGB2BGR, "RGBA": cv2.COLOR_RGBA2BGRA}
    _to_rgb: ClassVar[dict[int, int]] = {3: cv2.COLOR_BGR2RGB, 4: cv2.COLOR_BGRA2RGBA}

    def to_array(self, image: Image.Image) -> np.ndarray:
        array = np.array(image)
        code = self._to_bgr.get(image.mode)
        return array if code is None else cv2.cvtColor(array, code)

    def to_image(self, array: np.ndarray) -> Image.Image:
        code = self._to_rgb.get(self._channels(array))
        return Image.fromarray(array if code is None else cv2.cvtColor(array, code))

    @staticmethod
    def _channels(array: np.ndarray) -> int:
        return 1 if array.ndim == 2 else int(array.shape[2])
