"""
Domain exceptions of the core. Given.

The core only raises these exceptions: it does not know about HTTP. Whoever
uses it decides how to report them (the API with a status code, the command
line with a message on stderr).
"""


class RetroError(Exception):
    """Base class of every error of the core."""


class InvalidImage(RetroError):
    """The bytes cannot be opened as an image (empty, corrupt, not an image)."""


class PhotoTooSmall(RetroError):
    """The photo has fewer pixels per side than the avatar it should become."""


class StepNotImplemented(RetroError):
    """Raised by the steps that are still a TODO. The pipeline skips them."""

    def __init__(self, number: int, name: str) -> None:
        super().__init__(f"Paso {number}: {name} todavía no está implementado (retro/steps.py).")
        self.number = number
        self.name = name


class StepFailed(RetroError):
    """A step raised an unexpected error or returned something that is not a valid image."""
