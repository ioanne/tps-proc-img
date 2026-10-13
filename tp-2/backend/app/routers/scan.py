from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile, status

from app.schemas import ColorMode, ErrorOut, ScanOptions as ApiScanOptions, ScanOut
from app.storage import (
    delete_scan_files,
    get_scan as load_scan,
    list_scans as load_scans,
    save_scan,
)
from app.uploads import read_upload
from docscan import ScanOptions as CoreScanOptions
from docscan import Scanner, encode_png

router = APIRouter(prefix="/api/scans", tags=["scans"])

@router.post(
    "",
    response_model=ScanOut,
    status_code=status.HTTP_201_CREATED,
    summary="Scan a photo and save the result",
    responses={400: {"model": ErrorOut}, 413: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)
async def create_scan(
    file: Annotated[UploadFile, File(description="Photo of a document")],
    color_mode: Annotated[ColorMode, Form()] = "color",
    color_correction: Annotated[bool, Form()] = True,
    soften_colors: Annotated[float, Form(ge=0, le=1)] = 0.0,
):
    options = ApiScanOptions(
        color_mode=color_mode,
        color_correction=color_correction,
        soften_colors=soften_colors,
    )
    upload = await read_upload(file)  # given: 413 FILE_TOO_LARGE / 400 INVALID_FILE / 400 UNSUPPORTED_FORMAT
    result = Scanner().scan(
        upload.photo.image,
        CoreScanOptions(
            color_mode=options.color_mode,
            color_correction=options.color_correction,
            soften_colors=options.soften_colors,
        ),
    )
    png = encode_png(result.image)
    scan_id = uuid4().hex
    extension = {
        "PNG": "png",
        "JPEG": "jpg",
        "WEBP": "webp",
        "BMP": "bmp",
    }[upload.photo.format]
    scan = ScanOut(
        id=scan_id,
        original_name=upload.name,
        url=f"/media/{scan_id}.png",
        original_url=f"/media/{scan_id}-original.{extension}",
        width=result.image.shape[1],
        height=result.image.shape[0],
        size_bytes=len(png),
        corners=result.corners.tolist(),
        options=options,
        created_at=datetime.now(),
    )
    return save_scan(scan, png, upload.content)


@router.get("", response_model=list[ScanOut], summary="List the scans, newest first")
def list_scans():
    return load_scans()


@router.get("/{scan_id}", response_model=ScanOut, summary="Get a scan", responses={404: {"model": ErrorOut}})
def get_scan(scan_id: str):
    return load_scan(scan_id)


@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scan and its files",
    responses={404: {"model": ErrorOut}},
)
def delete_scan(scan_id: str):
    delete_scan_files(scan_id)
    return None
