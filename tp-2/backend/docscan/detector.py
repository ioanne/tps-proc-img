from typing import Sequence

import cv2
import numpy as np

from docscan.exceptions import DocumentNotFound

Corner = tuple[float, float]


class Detector:

    def __init__(
        self,
        max_processing_dim: int = 600,
        min_area_ratio: float = 0.15,
        approx_poly_eps: float = 0.02,
    ) -> None:
        self.max_processing_dim = max_processing_dim
        self.min_area_ratio = min_area_ratio
        self.approx_poly_eps = approx_poly_eps

    def order_corners(self, pts: np.ndarray) -> list[Corner]:
        """Orders 4 points: top-left, top-right, bottom-right, bottom-left."""
        pts = pts.reshape(4, 2)
        rect = np.zeros((4, 2), dtype=np.float32)

        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # top-left (menor x+y)
        rect[2] = pts[np.argmax(s)]  # bottom-right (mayor x+y)

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # top-right (menor y-x)
        rect[3] = pts[np.argmax(diff)]  # bottom-left (mayor y-x)

        return [(float(pt[0]), float(pt[1])) for pt in rect]

    def detect(self, image: np.ndarray) -> list[Corner]:
        """Finds the 4 corners of a document in pixels of the input image."""
        orig_h, orig_w = image.shape[:2]
        if orig_h == 0 or orig_w == 0:
            raise DocumentNotFound("La imagen proporcionada está vacía.")

        scale = 1.0
        max_dim = max(orig_h, orig_w)
        if max_dim > self.max_processing_dim:
            scale = self.max_processing_dim / float(max_dim)
            scaled_w = int(orig_w * scale)
            scaled_h = int(orig_h * scale)
            proc_img = cv2.resize(image, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
        else:
            proc_img = image.copy()

        gray = cv2.cvtColor(proc_img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Probar dos métodos de detección: Edges (Canny) y Threshold (Otsu)
        canny_edges = cv2.Canny(blurred, 50, 200)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed_edges = cv2.morphologyEx(canny_edges, cv2.MORPH_CLOSE, kernel)

        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_edges = cv2.Canny(otsu, 50, 200)
        closed_otsu = cv2.morphologyEx(otsu_edges, cv2.MORPH_CLOSE, kernel)

        total_proc_area = proc_img.shape[0] * proc_img.shape[1]
        min_area = total_proc_area * self.min_area_ratio

        candidates: list[tuple[float, np.ndarray]] = []

        for edge_map in (closed_edges, closed_otsu):
            contours, _ = cv2.findContours(edge_map, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < min_area:
                    continue

                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, self.approx_poly_eps * peri, True)

                if len(approx) == 4 and cv2.isContourConvex(approx):
                    candidates.append((area, approx))

        if not candidates:
            raise DocumentNotFound(
                "No se encontró un documento en la foto. Asegurate de que se vean las cuatro "
                "esquinas sobre un fondo que contraste, con buena iluminación y sin sombras marcadas."
            )

        candidates.sort(key=lambda x: x[0], reverse=True)
        best_cnt = candidates[0][1]

        proc_corners = self.order_corners(best_cnt)
        return [(x / scale, y / scale) for x, y in proc_corners]
    