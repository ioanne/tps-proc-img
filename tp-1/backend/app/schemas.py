"""
API contract (input and output).

These schemas are the interface consumed by the frontend and checked by the
acceptance tests: DO NOT change field names, types or ranges. They validate the
request format (if it fails, FastAPI responds 422); the domain rules (for example,
that the kernel must be odd) are validated in the core classes and answered with 400.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Name of each operation. Matches the last segment of its route
# (POST /api/images/{id}/<name>) and is the value of `ImageOut.operation`.
OperationName = Literal[
    "brightness",
    "contrast",
    "saturation",
    "sharpness",
    "grayscale",
    "blur",
    "edges",
    "rotation",
    "mirror",
    "resize",
]

ImageFormat = Literal["PNG", "JPEG", "WEBP", "BMP"]

ErrorCode = Literal[
    "NOT_IMPLEMENTED",
    "IMAGE_NOT_FOUND",
    "UNSUPPORTED_FORMAT",
    "INVALID_FILE",
    "FILE_TOO_LARGE",
    "INVALID_PARAMETERS",
]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str = Field(
        description="File name as uploaded by the user. Derived images inherit the one from their source."
    )
    url: str = Field(description="Public URL of the file: '/media/<file_name>'")
    width: int = Field(description="In pixels")
    height: int = Field(description="In pixels")
    format: ImageFormat = Field(description="Actual format of the stored file")
    size_bytes: int = Field(description="Size of the file stored on disk")
    operation: OperationName | None = Field(
        None, description="Operation that generated the image. null if it is an original image."
    )
    parameters: dict[str, Any] | None = Field(
        None,
        description=(
            "Operation parameters with the default values already applied "
            "(equivalent to `params.model_dump()`). {} for grayscale; null if it is an original image."
        ),
    )
    source_id: int | None = Field(
        None,
        description="Id of the image the operation was applied to. null if original or if its source was deleted.",
    )
    created_at: datetime


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str = Field(description="Message for the user")
    feature: str | None = Field(None, description="Only present in NOT_IMPLEMENTED")


class ErrorResponse(BaseModel):
    """Body of ALL custom error responses (400, 404, 413, 501)."""
    detail: ErrorDetail


# ---------------------------------------------------------------------------
# Input: parameters of each operation
# ---------------------------------------------------------------------------

class FactorIn(BaseModel):
    """Enhancement factor. 1.0 = unchanged image."""
    factor: float = Field(1.0, ge=0.0, le=3.0)


class BrightnessIn(FactorIn):
    """0 = black, 1.0 = unchanged."""


class ContrastIn(FactorIn):
    """0 = uniform gray, 1.0 = unchanged."""


class SaturationIn(FactorIn):
    """0 = no color (R = G = B), 1.0 = unchanged."""


class SharpnessIn(BaseModel):
    """<1 smooths, 1.0 = unchanged, >1 sharpens."""
    factor: float = Field(1.0, ge=0.0, le=5.0)


class BlurIn(BaseModel):
    method: Literal["gaussian", "median", "average"] = "gaussian"
    kernel_size: int = Field(5, ge=1, le=51, description="Kernel side in pixels. Domain rule: odd.")


class EdgesIn(BaseModel):
    lower_threshold: int = Field(100, ge=0, le=255, description="Domain rule: lower than upper_threshold.")
    upper_threshold: int = Field(200, ge=0, le=255)


class RotationIn(BaseModel):
    angle: float = Field(90.0, ge=-360.0, le=360.0, description="Degrees. Positive = counterclockwise.")
    expand: bool = Field(True, description="Enlarge the canvas so the image does not get cropped")


class MirrorIn(BaseModel):
    direction: Literal["horizontal", "vertical"] = Field(
        "horizontal", description="horizontal = left↔right, vertical = top↔bottom"
    )


class ResizeIn(BaseModel):
    width: int = Field(..., ge=1, le=8000)
    height: int | None = Field(
        None, ge=1, le=8000,
        description=(
            "Ignored if keep_aspect_ratio is true (computed as round(width * orig_height / orig_width)). "
            "Domain rule: required if keep_aspect_ratio is false."
        ),
    )
    keep_aspect_ratio: bool = True
