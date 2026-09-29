"""
Image editing operations.

`Operation` is the contract the service relies on: a `name` (the one of the
route and of `ImageOut.operation`), the `parameters` that are stored in the
database and an `apply` method that works on an image in memory.

TODO (teams): implement the ten operations. Each one validates its domain rules
in the constructor (raising `InvalidParameters`) and implements `apply`.
The constructor arguments match the fields of the schemas in `app/schemas.py`.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from PIL import Image

from app.core.exceptions import NotImplementedFeature


class Operation(ABC):
    name: ClassVar[str]

    def __init__(self, **parameters: Any) -> None:
        self._parameters = parameters

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    @abstractmethod
    def apply(self, image: Image.Image) -> Image.Image:
        """Returns a NEW image with the operation applied. `image` must not be modified."""


class Brightness(Operation):
    """Adjusts the brightness of the image by `factor`: 0 = black, 1.0 = unchanged.

    How the parameters get here (the other nine operations work the same way):

      1. The client sends `POST /api/images/{id}/brightness` with the JSON body
         `{"factor": 1.5}`. The fields are optional: `{}` means `factor = 1.0`
         (but the body itself is required: no body at all is a 422).
      2. FastAPI parses the body into `schemas.BrightnessIn` and validates the
         ranges declared there (0 <= factor <= 3). If they are not met it answers
         422 on its own: this class never sees an out-of-range `factor`.
      3. The router (`routers/operations.py`) builds the operation with
         `Brightness(**params.model_dump())`, i.e. `Brightness(factor=1.5)`. The
         constructor arguments are the schema fields, same names, already typed
         (`factor` is a `float`) and with the defaults applied.
      4. The constructor validates the domain rules the schema cannot express
         (raising `InvalidParameters` -> 400; brightness has none) and passes
         the values to `super().__init__`. That dict is what `self.parameters`
         returns and what the service stores in the database and returns in
         `ImageOut.parameters` (`{"factor": 1.5}`), so it must keep the same keys
         as the schema.
      5. The router hands the operation to `ImageService.apply`, which opens the
         source image and calls `apply(image)`. Inside `apply` the values are read
         from `self.parameters["factor"]` (or from an attribute the constructor
         saved, e.g. `self.factor`).
    """

    name = "brightness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        factor = self.factor  # the value received in the JSON body, e.g. 1.5
        raise NotImplementedFeature("Brightness")


class Contrast(Operation):
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Contrast")


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Saturation")


class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Sharpness")


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Grayscale")


class Blur(Operation):
    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        # TODO: domain rule, kernel_size must be odd.
        super().__init__(method=method, kernel_size=kernel_size)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Blur")


class Edges(Operation):
    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        # TODO: domain rule, lower_threshold < upper_threshold.
        super().__init__(lower_threshold=lower_threshold, upper_threshold=upper_threshold)

    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedFeature("Edge detection")


class Rotation(Operation):
    name = "rotation"

    def __init__(self, angle: float = 90.0, expand: bool = True) -> None:
        super().__init__(angle=angle, expand=expand)
        self.angle = angle
        self.expand = expand

    def apply(self, image: Image.Image) -> Image.Image:
        #raise NotImplementedFeature("Rotation")
        return image.rotate(self.angle, expand=self.expand, resample=Image.Resampling.BICUBIC)

class Mirror(Operation):
    name = "mirror"

    def __init__(self, direction: str = "horizontal") -> None:
        #super().__init__(direction=direction)
        direction_normalized = direction.lower()
        if direction_normalized not in ("horizontal", "vertical"):
            raise InvalidParameters(f"Invalid direction '{direction}'. Must be 'horizontal' or 'vertical'.")

        super().__init__(direction=direction_normalized)
        self.direction = direction_normalized

    def apply(self, image: Image.Image) -> Image.Image:
        #raise NotImplementedFeature("Mirror")
        if self.direction == "horizontal":
            return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


class Resize(Operation):
    name = "resize"

    def __init__(self, width: int, height: int | None = None, keep_aspect_ratio: bool = True) -> None:
        # TODO: domain rule, height is required if keep_aspect_ratio is false.
        #super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)
        # Validación de regla de dominio: height es obligatorio si keep_aspect_ratio es False
        if not keep_aspect_ratio and height is None:
            raise InvalidParameters("Height is required when keep_aspect_ratio is False.")

        super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)
        self.width = width
        self.height = height
        self.keep_aspect_ratio = keep_aspect_ratio

    def apply(self, image: Image.Image) -> Image.Image:
        #raise NotImplementedFeature("Resize")
        orig_w, orig_h = image.size

        if self.keep_aspect_ratio:
            if self.height is None:
                # Calcular altura manteniendo la proporción del nuevo ancho
                new_h = round(orig_h * (self.width / orig_w))
                new_w = self.width
            else:
                # Si ambos vienen dados, redimensionar proporcionalmente para que quepa dentro de la caja (bounding box)
                ratio = min(self.width / orig_w, self.height / orig_h)
                new_w = round(orig_w * ratio)
                new_h = round(orig_h * ratio)
        else:
            new_w = self.width
            new_h = self.height

        # Evitar dimensiones menores a 1 píxel
        new_w = max(1, new_w)
        new_h = max(1, new_h)

        return image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)