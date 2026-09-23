"""
Translation of the domain exceptions to HTTP responses, in a single place.

Every error keeps the contract format: {"detail": {"code": ..., "message": ...}}.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError

HTTP_STATUS: dict[str, int] = {
    "NOT_IMPLEMENTED": 501,
    "IMAGE_NOT_FOUND": 404,
    "UNSUPPORTED_FORMAT": 400,
    "INVALID_FILE": 400,
    "INVALID_PARAMETERS": 400,
    "FILE_TOO_LARGE": 413,
}


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_STATUS.get(exc.code, 400),
        content={"detail": exc.to_detail()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
