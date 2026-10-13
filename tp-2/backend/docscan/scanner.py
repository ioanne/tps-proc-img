from typing import Literal

import numpy as np

from docscan.detector import DocumentDetector
from docscan.filters import (
    BlackAndWhiteFilter,
    ColorCorrectionFilter,
    Filter,
    GrayscaleFilter,
    SoftenColorsFilter,
)
from docscan.perspective import correct_perspective


class Scanner:
    def __init__(self) -> None:
        self.detector = DocumentDetector()

    def scan(
        self,
        image: np.ndarray,
        color_mode: Literal["color", "grayscale", "bw"] = "color",
        color_correction: bool = True,
        soften_colors: float = 0.0,
    ) -> tuple[np.ndarray, list[tuple[float, float]]]:
        corners = self.detector.detect(image)
        scanned = correct_perspective(image, corners)

        filters: list[Filter] = []

        if color_correction:
            filters.append(ColorCorrectionFilter())

        if soften_colors > 0:
            filters.append(SoftenColorsFilter(soften_colors))

        if color_mode == "grayscale":
            filters.append(GrayscaleFilter())
        elif color_mode == "bw":
            filters.append(BlackAndWhiteFilter())
        elif color_mode != "color":
            raise ValueError(f"Modo de color no válido: {color_mode}")

        for image_filter in filters:
            scanned = image_filter.apply(scanned)

        return scanned, corners