"""
Domain exceptions.

The core raises these; `app/errors.py` translates them to HTTP responses in a
single exception handler. They do not know anything about HTTP.
"""


class DomainError(Exception):
    """Base of every error the core can raise. `code` is the `ErrorCode` of the contract."""

    code: str = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def to_detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class NotImplementedFeature(DomainError):
    code = "NOT_IMPLEMENTED"

    def __init__(self, feature: str) -> None:
        super().__init__(f"The feature '{feature}' has not been implemented yet.")
        self.feature = feature

    def to_detail(self) -> dict[str, str]:
        return {**super().to_detail(), "feature": self.feature}


class ImageNotFound(DomainError):
    code = "IMAGE_NOT_FOUND"

    def __init__(self, image_id: int) -> None:
        super().__init__(f"There is no image with id {image_id}.")
        self.image_id = image_id


class InvalidParameters(DomainError):
    code = "INVALID_PARAMETERS"


class InvalidFile(DomainError):
    code = "INVALID_FILE"

    def __init__(self, message: str = "The file cannot be opened as an image.") -> None:
        super().__init__(message)


class UnsupportedFormat(DomainError):
    code = "UNSUPPORTED_FORMAT"

    def __init__(self, image_format: str | None) -> None:
        super().__init__(f"The format '{image_format}' is not supported. Use PNG, JPEG, WEBP or BMP.")
        self.image_format = image_format


class FileTooLarge(DomainError):
    code = "FILE_TOO_LARGE"

    def __init__(self, max_bytes: int) -> None:
        super().__init__(f"The file exceeds the maximum size of {max_bytes // (1024 * 1024)} MB.")
        self.max_bytes = max_bytes
