import base64
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image

from app.config import PREVIEW_SIDE
from app.routers.palettes import palette_out
from app.schemas import AvatarStepsOut, ErrorOut, OptionsIn, PaletteName, PixelSize, StepOut
from app.uploads import read_upload
from retro import DEFAULT_PALETTE, PALETTES, AvatarMaker, StepFailed, StepResult, count_colors, encode_png, to_pil
from retro.pipeline import MAX_FRAME

router = APIRouter(prefix="/api", tags=["avatar"])
maker = AvatarMaker()

ERRORS = {400: {"model": ErrorOut}, 413: {"model": ErrorOut}, 422: {"model": ErrorOut}, 500: {"model": ErrorOut}}


def options_form(
    pixels: Annotated[PixelSize, Form(description="Side of the avatar in big pixels: 16, 32, 64 or 128")] = 32,
    palette: Annotated[PaletteName, Form(description="Name of a palette (GET /api/palettes)")] = DEFAULT_PALETTE,
    dithering: Annotated[bool, Form(description="Floyd–Steinberg dithering")] = False,
    frame: Annotated[int, Form(ge=0, le=MAX_FRAME, description="Thickness of the frame (0 = none)")] = 0,
) -> OptionsIn:
    return OptionsIn(pixels=pixels, palette=palette, dithering=dithering, frame=frame)


@router.post(
    "/avatar",
    response_class=Response,
    summary="Turn a photo into a retro avatar (PNG)",
    responses={200: {"content": {"image/png": {}}, "description": "The avatar, 512×512"}, **ERRORS},
)
async def make_avatar(
    file: Annotated[UploadFile, File(description="A photo")],
    options: Annotated[OptionsIn, Depends(options_form)],
):
    upload = await read_upload(file)
    trace = maker.run(upload.photo.image, options.to_core())
    if trace.failure:
        raise StepFailed(trace.failure.message)
    headers = {"X-Avatar-Complete": str(trace.complete).lower()}
    return Response(encode_png(trace.image), media_type="image/png", headers=headers)


@router.post(
    "/avatar/steps",
    response_model=AvatarStepsOut,
    summary="Same as /api/avatar, but returns the image of every step",
    responses=ERRORS,
)
async def avatar_steps(
    file: Annotated[UploadFile, File(description="A photo")],
    options: Annotated[OptionsIn, Depends(options_form)],
):
    upload = await read_upload(file)
    trace = maker.run(upload.photo.image, options.to_core())
    photo = StepOut(name="photo", label="Photo", number=None, class_name=None, status="input", message=None,
                    **image_fields(trace.photo))
    return AvatarStepsOut(
        options=options,
        palette=palette_out(PALETTES[options.palette]),
        complete=trace.complete,
        steps=[photo, *(step_out(r) for r in trace.results)],
    )


def step_out(result: StepResult) -> StepOut:
    step = result.step
    fields = image_fields(result.image) if result.image is not None else \
        {"width": None, "height": None, "colors": None, "image": None}
    return StepOut(name=step.name, label=step.label, number=step.number, class_name=type(step).__name__,
                   status=result.status, message=result.message or None, **fields)


def image_fields(image: np.ndarray) -> dict:
    height, width = image.shape[:2]
    preview = to_pil(image)
    if max(width, height) > PREVIEW_SIDE:
        preview.thumbnail((PREVIEW_SIDE, PREVIEW_SIDE), Image.Resampling.LANCZOS)
    png = encode_png(np.asarray(preview))
    return {"width": width, "height": height, "colors": count_colors(image),
            "image": "data:image/png;base64," + base64.b64encode(png).decode()}

