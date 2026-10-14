from cv2 import COLOR_HSV2BGR
from abc import ABC, abstractmethod
import numpy as np
import cv2

class Filter(ABC):
    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        pass

# Escala de grises
class GrayscaleFilter(Filter):
    def apply(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
# Blanco y negro
class BWFilter(Filter):
    def apply(self, image: np.ndarray) -> np.ndarray:
        grayscale = GrayscaleFilter().apply(image)
        return cv2.adaptiveThreshold(grayscale, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 8)

# Original
class Color(Filter):
    def apply(self, image: np.ndarray) -> np.ndarray:
        return image


#Correción de color
class ColorCorrectionFilter(Filter):
    def apply(self,image: np.ndarray) -> np.ndarray:
        split_image = cv2.split(image)

        perc_b = np.percentile(split_image[0], 98)
        perc_g = np.percentile(split_image[1], 98)
        perc_r = np.percentile(split_image[2], 98)

        canal_b = split_image[0] * (255 / perc_b)
        canal_g = split_image[1] * (255 / perc_g)
        canal_r = split_image[2] * (255 / perc_r)

        canal_b = np.clip(canal_b, 0, 255).astype(np.uint8)
        canal_g = np.clip(canal_g, 0, 255).astype(np.uint8)
        canal_r = np.clip(canal_r, 0, 255).astype(np.uint8)

        new_image = cv2.merge([canal_b,canal_g, canal_r])

        return new_image


class SoftenColorsFilter(Filter):

    def __init__(self, factor: float):
        self.factor = factor

    def apply(self, image: np.ndarray) -> np.ndarray:
        # Sin suavizado, conservar exactamente los píxeles.
        if self.factor == 0:
            return image.copy()

        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        h, s, v = cv2.split(hsv_image)

        strength = (s / 255.0) * (v / 255.0)
        adjust = strength * self.factor

        s = np.clip(
            s * (1.0 - adjust), 0, 255
        ).astype(np.uint8)

        v = np.clip(
            v * (1.0 + adjust), 0, 255
        ).astype(np.uint8)

        new_image = cv2.merge([h, s, v])

        return cv2.cvtColor(new_image, cv2.COLOR_HSV2BGR)

        




        

        


 
