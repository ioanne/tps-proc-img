# docscan/detector.py
"""
Document detection core.
Implements a simple classical OpenCV pipeline to locate a document in a photo.
The algorithm follows the steps described in the TP:
- Resize image for speed while keeping aspect ratio (max dimension 600).
- Convert to grayscale, blur, edge detection (Canny).
- Morphological closing to join edges.
- Find contours, sort by area descending.
- Approximate each contour with polygonal curve (approxPolyDP) using 2% of perimeter.
- Choose the first convex quadrilateral whose area is at least MIN_AREA_RATIO of the original image.
- Return the four corners ordered clockwise starting from top‑left.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import List, Tuple

from docscan.exceptions import DocumentNotFound, ScanError

class DocumentDetector:
    """Detect a document (quadrilateral) in an image.

    Parameters
    ----------
    min_area_ratio: float, optional
        Minimum fraction of the original image area that the document must occupy.
        Default 0.15 (15%).
    resize_max_dim: int, optional
        Maximum dimension (width or height) of the resized image used for detection.
        Default 600.
    """

    def __init__(self, min_area_ratio: float = 0.15, resize_max_dim: int = 600):
        if not (0 < min_area_ratio <= 1):
            raise ValueError("min_area_ratio must be in (0, 1]")
        self.min_area_ratio = min_area_ratio
        self.resize_max_dim = resize_max_dim

    # ---------------------------------------------------------------------
    def _resize_for_detection(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Resize image keeping aspect ratio.

        Returns the resized image and the scaling factor (original / resized).
        """
        h, w = image.shape[:2]
        scale = 1.0
        if max(h, w) > self.resize_max_dim:
            scale = self.resize_max_dim / float(max(h, w))
            new_w = int(w * scale)
            new_h = int(h * scale)
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return resized, 1.0 / scale
        return image, 1.0

    # ---------------------------------------------------------------------
    def _order_corners(self, pts: np.ndarray) -> List[Tuple[float, float]]:
        """Order four points clockwise starting from top‑left.

        The input is a (4,2) array of (x,y) coordinates.
        """
        # Convert to list of (x, y)
        pts = pts.reshape(4, 2)
        # Sum and diff for ordering
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1).ravel()
        top_left = pts[np.argmin(s)]
        bottom_right = pts[np.argmax(s)]
        top_right = pts[np.argmin(diff)]
        bottom_left = pts[np.argmax(diff)]
        ordered = [top_left, top_right, bottom_right, bottom_left]
        # Convert to list of floats for JSON serialisation
        return [(float(x), float(y)) for x, y in ordered]

    # ---------------------------------------------------------------------
    def detect(self, image: np.ndarray) -> List[Tuple[float, float]]:
        """Detect document corners.

        Parameters
        ----------
        image: np.ndarray
            BGR image as provided by ``docscan.imageio.Photo``.

        Returns
        -------
        List[Tuple[float, float]]
            Four corners ordered clockwise (tl, tr, br, bl).

        Raises
        ------
        DocumentNotFound
            If no suitable quadrilateral is detected.
        ScanError
            For unexpected OpenCV errors.
        """
        try:
            resized, scale = self._resize_for_detection(image)
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 50, 150)
            # Close gaps
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Sort by area descending
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            img_area = resized.shape[0] * resized.shape[1]
            for cnt in contours:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    # Ensure enough area
                    if cv2.contourArea(approx) >= self.min_area_ratio * img_area:
                        # Scale points back to original size
                        pts = approx.reshape(4, 2).astype(np.float32) * scale
                        ordered = self._order_corners(pts)
                        return ordered
            # No quadrilateral found
            raise DocumentNotFound(
                "No se encontró un documento en la foto. Asegúrate de que se vean las cuatro esquinas y que el documento ocupe al menos el 15 % de la imagen."
            )
        except cv2.error as exc:
            # Wrap any OpenCV error in a generic ScanError for consistency
            raise ScanError(str(exc)) from exc

# Export for convenient import
__all__ = ["DocumentDetector"]
