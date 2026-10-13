from abc import ABC, abstractmethod

import cv2
import numpy as np


class Filter(ABC):
    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class GrayscaleFilter(Filter):
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class BlackAndWhiteFilter(Filter):
    def apply(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            10,
        )


class ColorCorrectionFilter(Filter):
    def apply(self, image: np.ndarray) -> np.ndarray:
        image_float = image.astype(np.float32)
        paper_color = np.percentile(image_float, 98, axis=(0, 1))
        paper_color = np.maximum(paper_color, 1.0)

        corrected = image_float * (255.0 / paper_color)
        return np.clip(corrected, 0, 255).astype(np.uint8)

class SoftenColorsFilter(Filter):
    def __init__(self, amount: float) -> None:
        if not 0.0 <= amount <= 1.0:
            raise ValueError("amount debe estar entre 0 y 1")
        self.amount = amount

    def apply(self, image: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        saturation = hsv[:, :, 1] / 255.0
        brightness = hsv[:, :, 2] / 255.0

        bright_colors = np.clip((brightness - 80 / 255) / (175 / 255), 0, 1)
        strength = self.amount * saturation * bright_colors

        result = image.astype(np.float32) * (1 - strength[:, :, None])
        result += 255 * strength[:, :, None]
        return np.clip(result, 0, 255).astype(np.uint8)        