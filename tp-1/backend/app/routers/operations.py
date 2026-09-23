"""
Image editing endpoints.

Each endpoint applies ONE operation to the image `image_id` and returns the
resulting image, which is a NEW image (stored on disk and in the database with
`source_id = image_id`). The original image is never modified.

Common rules (see section 5 of the assignment):
  - parameters are validated BEFORE looking up the image (400 takes priority over 404);
  - the result keeps the file format of the source;
  - `parameters` in the response = `params.model_dump()` ({} for grayscale).

Each endpoint builds the operation (which validates its domain rules in the
constructor, so a 400 happens before looking up the image) and hands it to
`ImageService.apply`.
"""

from fastapi import APIRouter, Depends, status

from app.core.operations import (
    Blur,
    Brightness,
    Contrast,
    Edges,
    Grayscale,
    Mirror,
    Resize,
    Rotation,
    Saturation,
    Sharpness,
)
from app.core.service import ImageService
from app.dependencies import get_image_service
from app.schemas import (
    BlurIn,
    BrightnessIn,
    ContrastIn,
    EdgesIn,
    ErrorResponse,
    ImageOut,
    MirrorIn,
    ResizeIn,
    RotationIn,
    SaturationIn,
    SharpnessIn,
)

router = APIRouter(prefix="/api/images/{image_id}", tags=["operations"])

OPTIONS = dict(
    response_model=ImageOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "INVALID_PARAMETERS: a domain rule is violated"},
        404: {"model": ErrorResponse, "description": "IMAGE_NOT_FOUND: the source image does not exist"},
        501: {"model": ErrorResponse, "description": "NOT_IMPLEMENTED"},
    },
)


@router.post("/brightness", summary="1. Adjust brightness", **OPTIONS)
def apply_brightness(image_id: int, params: BrightnessIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Brightness(**params.model_dump()))


@router.post("/contrast", summary="2. Adjust contrast", **OPTIONS)
def apply_contrast(image_id: int, params: ContrastIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Contrast(**params.model_dump()))


@router.post("/saturation", summary="3. Adjust saturation", **OPTIONS)
def apply_saturation(image_id: int, params: SaturationIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Saturation(**params.model_dump()))


@router.post("/sharpness", summary="4. Adjust sharpness", **OPTIONS)
def apply_sharpness(image_id: int, params: SharpnessIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Sharpness(**params.model_dump()))


@router.post("/grayscale", summary="5. Convert to grayscale", **OPTIONS)
def apply_grayscale(image_id: int, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Grayscale())


@router.post("/blur", summary="6. Blur", **OPTIONS)
def apply_blur(image_id: int, params: BlurIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Blur(**params.model_dump()))


@router.post("/edges", summary="7. Detect edges (Canny)", **OPTIONS)
def apply_edges(image_id: int, params: EdgesIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Edges(**params.model_dump()))


@router.post("/rotation", summary="8. Rotate", **OPTIONS)
def apply_rotation(image_id: int, params: RotationIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Rotation(**params.model_dump()))


@router.post("/mirror", summary="9. Mirror", **OPTIONS)
def apply_mirror(image_id: int, params: MirrorIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Mirror(**params.model_dump()))


@router.post("/resize", summary="10. Resize", **OPTIONS)
def apply_resize(image_id: int, params: ResizeIn, service: ImageService = Depends(get_image_service)):
    return service.apply(image_id, Resize(**params.model_dump()))
