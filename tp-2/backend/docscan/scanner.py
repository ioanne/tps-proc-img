from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

from docscan.detector import Detector
from docscan.filters import (
    BWFilter,
    ColorCorrectionFilter,
    Filter,
    GrayscaleFilter,
    SoftenColorsFilter,
)
from docscan.warper import PerspectiveWarper

ColorMode = Literal["color", "grayscale", "bw"]


@dataclass(frozen=True)
class ScanResult:
    image: np.ndarray
    corners: list[tuple[float, float]]


class Scanner:

    def __init__(
        self,
        detector: Detector | None = None,
        warper: PerspectiveWarper | None = None,
    ) -> None:
        self.detector = detector or Detector()
        self.warper = warper or PerspectiveWarper()

    def build_filters(
        self,
        color_mode: ColorMode = "color",
        color_correction: bool = True,
        soften_colors: float = 0.0,
    ) -> list[Filter]:
        filters: list[Filter] = []

        if color_correction:
            filters.append(ColorCorrectionFilter())

        if soften_colors > 0.0:
            filters.append(SoftenColorsFilter(soften_colors))

        if color_mode == "grayscale":
            filters.append(GrayscaleFilter())
        elif color_mode == "bw":
            filters.append(BWFilter())

        return filters

    def scan(
        self,
        image: np.ndarray,
        corners: Sequence[tuple[float, float]] | None = None,
        color_mode: ColorMode = "color",
        color_correction: bool = True,
        soften_colors: float = 0.0,
    ) -> ScanResult:
        if corners is None:
            corners = self.detector.detect(image)

        warped = self.warper.warp(image, corners)
        filter_chain = self.build_filters(color_mode, color_correction, soften_colors)

        processed = warped
        for flt in filter_chain:
            processed = flt.apply(processed)

        return ScanResult(image=processed, corners=list(corners))