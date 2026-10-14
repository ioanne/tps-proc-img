import cv2

from typing import Sequence

from docscan.exceptions import InvalidImage, DocumentNotFound
from docscan.imageio import Photo

class Detector:

    def detect(self, photo: Photo) -> Sequence[tuple[float, float]]:
        if photo is None:
            raise InvalidImage("No se proporcionó ninguna foto para la detección.")

        image = photo.image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 75, 200)

        contours, hierachy = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

    def _order_points(self, points):
        pts = points.reshape(4, 2)
        pass

        raise DocumentNotFound("No se pudo detectar un documento en la foto proporcionada.")
    