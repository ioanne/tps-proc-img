from abc import ABC, abstractmethod
from typing import Any, ClassVar

import numpy as np
from PIL import Image

from app.core.operations.conversion import ArrayConverter, OpenCVConverter


class Operation(ABC):
    name: ClassVar[str]

    def __init__(self, **parameters: Any) -> None:
        self._parameters = parameters

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    @abstractmethod
    def apply(self, image: Image.Image) -> Image.Image: ...


class ArrayOperation(Operation):
    def __init__(self, converter: ArrayConverter | None = None, **parameters: Any) -> None:
        super().__init__(**parameters)
        self._converter = converter if converter is not None else OpenCVConverter()

    def apply(self, image: Image.Image) -> Image.Image:
        return self._converter.to_image(self.process(self._converter.to_array(image)))

    @abstractmethod
    def process(self, array: np.ndarray) -> np.ndarray: ...
