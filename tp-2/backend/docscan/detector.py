from typing import Sequence

from docscan.exceptions import InvalidImage, DocumentNotFound
from docscan.imageio import Photo

class Detector:

    def detect(self, photo: Photo) -> Sequence[tuple[float, float]]:
        if photo is None:
            raise InvalidImage("No se proporcionó ninguna foto para la detección.")

        raise DocumentNotFound("No se pudo detectar un documento en la foto proporcionada.")