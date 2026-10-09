from typing import Sequence

import cv2
import numpy as np

Corner = tuple[float, float]


class PerspectiveWarper:

    def warp(self, image: np.ndarray, corners: Sequence[Corner]) -> np.ndarray:
        tl, tr, br, bl = corners

        width_a = np.hypot(br[0] - bl[0], br[1] - bl[1])
        width_b = np.hypot(tr[0] - tl[0], tr[1] - tl[1])
        max_width = int(max(width_a, width_b))

        height_a = np.hypot(tr[0] - br[0], tr[1] - br[1])
        height_b = np.hypot(tl[0] - bl[0], tl[1] - bl[1])
        max_height = int(max(height_a, height_b))

        dst = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_width if max_height <= 0 else max_height - 1],
            ],
            dtype=np.float32,
        )

        src = np.array(corners, dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(image, matrix, (max_width, max_height))