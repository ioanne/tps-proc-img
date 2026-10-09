from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.schemas import ColorMode, ErrorOut, ScanOptions, ScanOut
from app.uploads import read_upload
from docscan.scanner import Scanner
from app.repository import ScanRepository

router = APIRouter(prefix="/api/scans", tags=["scans"])
scanner = Scanner()
repository = ScanRepository()


def empty_scan(scan_id: str = "", original_name: str = "", options: ScanOptions | None = None) -> ScanOut:
    """Placeholder answer with the right shape. Delete it once the endpoints are implemented."""
    return ScanOut(
        id=scan_id, original_name=original_name, url="", original_url="",
        width=0, height=0, size_bytes=0, corners=[],
        options=options or ScanOptions(), created_at=datetime.now(),
    )


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
    options = ScanOptions(color_mode=color_mode, color_correction=color_correction, soften_colors=soften_colors)
    upload = await read_upload(file)  # given: 413 FILE_TOO_LARGE / 400 INVALID_FILE / 400 UNSUPPORTED_FORMAT
    result = scanner.scan(
        image=upload.photo.image,
        color_mode=options.color_mode,
        color_correction=options.color_correction,
        soften_colors=options.soften_colors,
    )
    return repository.save(upload, result, options)


@router.get("", response_model=list[ScanOut], summary="List the scans, newest first")
def list_scans():
   return repository.list()


@router.get("/{scan_id}", response_model=ScanOut, summary="Get a scan", responses={404: {"model": ErrorOut}})
def get_scan(scan_id: str):
    return repository.get(scan_id)


@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scan and its files",
    responses={404: {"model": ErrorOut}},
)
def delete_scan(scan_id: str):
    repository.delete(scan_id)
    return None
