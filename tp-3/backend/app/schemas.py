"""
Input/output schemas of the API: the contract with the frontend and the tests. Given.
"""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

from retro import DEFAULT_PALETTE, PALETTES, AvatarOptions
from retro.pipeline import MAX_FRAME, PIXEL_SIZES


def _check_pixels(value: int) -> int:
    if value not in PIXEL_SIZES:
        options = ", ".join(map(str, PIXEL_SIZES[:-1]))
        raise ValueError(f"tiene que ser {options} o {PIXEL_SIZES[-1]}")
    return value


PixelSize = Annotated[int, AfterValidator(_check_pixels)]
PaletteName = Literal[tuple(PALETTES)]  # type: ignore[valid-type]  # every key of PALETTES
StepStatus = Literal["input", "done", "pending", "blocked", "failed"]


class OptionsIn(BaseModel):
    pixels: PixelSize = 32
    palette: PaletteName = DEFAULT_PALETTE
    dithering: bool = False
    frame: int = Field(0, ge=0, le=MAX_FRAME)

    def to_core(self) -> AvatarOptions:
        return AvatarOptions(**self.model_dump())


class PaletteOut(BaseModel):
    name: str
    label: str
    colors: list[str] = Field(description="#rrggbb; in monochrome palettes, from darkest to lightest")
    monochrome: bool

    model_config = {"json_schema_extra": {"example": {
        "name": "gameboy", "label": "Game Boy",
        "colors": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"], "monochrome": True,
    }}}


class StepOut(BaseModel):
    name: str = Field(description='"photo" for the input, then the name of each step')
    label: str
    number: int | None = Field(description="Step number in the assignment; null for the given ones")
    class_name: str | None = Field(description="Class of the step in retro/steps.py")
    status: StepStatus
    message: str | None = Field(description="Why the step is pending, blocked or failed")
    width: int | None
    height: int | None
    colors: int | None = Field(description="Number of different colors in the image")
    image: str | None = Field(description="PNG as a data: URL, shrunk if it is bigger than 512 px")


class AvatarStepsOut(BaseModel):
    options: OptionsIn
    palette: PaletteOut
    complete: bool = Field(description="Every step is done: the last image is the final avatar")
    steps: list[StepOut]

    model_config = {"json_schema_extra": {"example": {
        "options": {"pixels": 32, "palette": "gameboy", "dithering": True, "frame": 0},
        "palette": PaletteOut.model_config["json_schema_extra"]["example"],
        "complete": False,
        "steps": [
            {"name": "photo", "label": "Photo", "number": None, "class_name": None, "status": "input",
             "message": None, "width": 1024, "height": 768, "colors": 61234, "image": "data:image/png;base64,…"},
            {"name": "square_crop", "label": "Square crop", "number": 1, "class_name": "SquareCrop",
             "status": "done", "message": None, "width": 768, "height": 768, "colors": 50211,
             "image": "data:image/png;base64,…"},
            {"name": "shrink", "label": "Shrink", "number": 2, "class_name": "Shrink", "status": "pending",
             "message": "Paso 2: Shrink todavía no está implementado (retro/steps.py).",
             "width": None, "height": None, "colors": None, "image": None},
        ],
    }}}


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    detail: ErrorDetail

    model_config = {"json_schema_extra": {"example": {
        "detail": {"code": "PHOTO_TOO_SMALL", "message": "La foto mide 20×20: para un avatar de 32×32…"},
    }}}
