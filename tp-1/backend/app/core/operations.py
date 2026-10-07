"""
Image editing operations.

`Operation` is the contract the service relies on: a `name` (the one of the
route and of `ImageOut.operation`), the `parameters` that are stored in the
database and an `apply` method that works on an image in memory.

TODO (teams): implement the ten operations. Each one validates its domain rules
in the constructor (raising `InvalidParameters`) and implements `apply`.
The constructor arguments match the fields of the schemas in `app/schemas.py`.
"""
from app.core.exceptions import InvalidParameters
import numpy as np
import cv2
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from PIL import Image, ImageEnhance
from PIL import ImageFilter
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
    name = "brightness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        image = ImageEnhance.Brightness(image).enhance(self.factor)
        return image
    
        #raise NotImplementedFeature("Brightness")


class Contrast(Operation):
    name = "contrast"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        image = ImageEnhance.Contrast(image).enhance(self.factor)
        return image
        #raise NotImplementedFeature("Contrast")


class Saturation(Operation):
    name = "saturation"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor

    def apply(self, image: Image.Image) -> Image.Image:
        image = ImageEnhance.Color(image).enhance(self.factor)
        return image
        #raise NotImplementedFeature("Saturation")

class Sharpness(Operation):
    name = "sharpness"

    def __init__(self, factor: float = 1.0) -> None:
        super().__init__(factor=factor)
        self.factor = factor    

    def apply(self, image: Image.Image) -> Image.Image:
        image = ImageEnhance.Sharpness(image).enhance(self.factor)
        return image
        ##raise NotImplementedFeature("Sharpness")


class Grayscale(Operation):
    name = "grayscale"

    def __init__(self) -> None:
        super().__init__()
        

    def apply(self, image: Image.Image) -> Image.Image:
        image = image.convert("L")
        return image
        #raise NotImplementedFeature("Grayscale")


class Blur(Operation):
    name = "blur"

    def __init__(self, method: str = "gaussian", kernel_size: int = 5) -> None:
        # TODO: domain rule, kernel_size must be odd.
        super().__init__(method=method, kernel_size=kernel_size)
        self.method = method
        self.kernel_size = kernel_size

    def apply(self, image: Image.Image) -> Image.Image:
        if self.kernel_size % 2 == 0:
            raise InvalidParameters("El kernel Size debe ser impar")
    
        if self.method == "gaussian":
            image = image.filter(ImageFilter.GaussianBlur(radius=self.kernel_size))
        elif self.method == "median":
            image = image.filter(ImageFilter.MedianFilter(size=self.kernel_size))
        elif self.method == "average":
            image = image.filter(ImageFilter.BoxBlur(radius=self.kernel_size))

        return image   
        #raise NotImplementedFeature("Blur")


class Edges(Operation):
    name = "edges"

    def __init__(self, lower_threshold: int = 100, upper_threshold: int = 200) -> None:
        # TODO: domain rule, lower_threshold < upper_threshold.
        super().__init__(lower_threshold=lower_threshold, upper_threshold=upper_threshold)
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold

    def apply(self, image: Image.Image) -> Image.Image:
        img_gray = image.convert("L")
        np_img_gray = np.array(img_gray)
        
        edges = cv2.Canny(np_img_gray, self.lower_threshold, self.upper_threshold)
        
        return Image.fromarray(edges, mode="L")        
        #raise NotImplementedFeature("Edge detection")


class Rotation(Operation):
    name = "rotation"

    def __init__(self, angle: float = 90.0, expand: bool = True) -> None:
        super().__init__(angle=angle, expand=expand)
        self.angle = angle
        self.expand = expand    

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "RGBA":
            fillcolor = (0, 0, 0, 0)
        elif image.mode == "RGB":
            fillcolor = (0, 0, 0)
        else:
            fillcolor = 0
        
        image = image.rotate(self.angle, expand=self.expand, fillcolor=fillcolor)
        return image
        
        #raise NotImplementedFeature("Rotation")


class Mirror(Operation):
    name = "mirror"

    def __init__(self, direction: str = "horizontal") -> None:
        super().__init__(direction=direction)
        self.direction = direction

    def apply(self, image: Image.Image) -> Image.Image:
        mode = image.mode   
        np_img = np.array(image)

        if self.direction == "horizontal":
            flip_code = 1
        else:
            flip_code = 0

        flipped_img = cv2.flip(np_img, flip_code)
        return Image.fromarray(flipped_img, mode=mode)    
        #raise NotImplementedFeature("Mirror")


class Resize(Operation):
    name = "resize"

    def __init__(self, width: int, height: int | None = None, keep_aspect_ratio: bool = True) -> None:
        # TODO: domain rule, height is required if keep_aspect_ratio is false.
        if not keep_aspect_ratio and height is None:
            raise InvalidParameters("La altura es obligatoria cuando se desactiva 'Mantener Relación de Aspecto'")
        super().__init__(width=width, height=height, keep_aspect_ratio=keep_aspect_ratio)
        self.width = width
        self.height = height
        self.keep_aspect_ratio = keep_aspect_ratio    

    def apply(self, image: Image.Image) -> Image.Image:
        original_width, original_height = image.size

        if self.keep_aspect_ratio:
            new_height = self.height
            new_width = int(original_width * self.height / original_height)
        else:
            new_width = self.width
            new_height = self.height

        resized_image = image.resize((new_width, new_height))
        return resized_image    

        #raise NotImplementedFeature("Resize")
