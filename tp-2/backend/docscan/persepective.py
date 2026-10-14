from typing import Sequence

import numpy as np

from docscan.imageio import Photo


class PerspectiveCorrector:
    def correct(self,
                photo: Photo,
                points: Sequence[tuple[float, float]]
    ):
        pts = np.array(points, dtype="float32")

        
        pass