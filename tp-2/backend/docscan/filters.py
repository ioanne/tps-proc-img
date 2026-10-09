
from abc import ABC, abstractmethod

import cv2
import numpy as np


class Filter(ABC):

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Applies filter to image and returns transformed image."""


class ColorCorrectionFilter(Filter):

    def __init__(self, percentile: float = 98.0) -> None:
        self.percentile = percentile

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image.ndim != 3:
            return image

        result = image.astype(np.float32)
        for i in range(3):
            val = np.percentile(result[:, :, i], self.percentile)
            if val > 0:
                result[:, :, i] = np.clip((result[:, :, i] / val) * 255.0, 0, 255)
        return result.astype(np.uint8)


class SoftenColorsFilter(Filter):

    def __init__(self, factor: float) -> None:
        self.factor = float(np.clip(factor, 0.0, 1.0))

    def apply(self, image: np.ndarray) -> np.ndarray:
        if self.factor <= 0.0 or image.ndim != 3:
            return image

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        sat_factor = s / 255.0
        val_factor = v / 255.0
        weight = sat_factor * val_factor * self.factor

        v_new = v + (255.0 - v) * weight
        s_new = s * (1.0 - weight)

        hsv[:, :, 1] = np.clip(s_new, 0, 255)
        hsv[:, :, 2] = np.clip(v_new, 0, 255)

        res_hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(res_hsv, cv2.COLOR_HSV2BGR)


class GrayscaleFilter(Filter):

    def apply(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class BWFilter(Filter):

    def apply(self, image: np.ndarray) -> np.ndarray:
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )