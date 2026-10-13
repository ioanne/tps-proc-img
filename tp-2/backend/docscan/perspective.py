from typing import Sequence

import cv2
import numpy as np


def correct_perspective(
    image: np.ndarray,
    corners: Sequence[tuple[float, float]],
) -> np.ndarray:
    points = np.asarray(corners, dtype=np.float32)
    tl, tr, br, bl = points

    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    height_right = np.linalg.norm(br - tr)
    height_left = np.linalg.norm(bl - tl)

    width = round(max(width_top, width_bottom))
    height = round(max(height_right, height_left))

    destination = np.array(
        [
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1],
        ],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(points, destination)
    return cv2.warpPerspective(image, matrix, (width, height))