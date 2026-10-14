"""
retro: turns a photo into a retro pixel-art avatar.

It does NOT import FastAPI nor anything from `app`, so it can be used from the
API, from the command line (`python -m retro`) or from any Python program.

Given: everything except the steps. TODO (team): steps 1 to 6 in steps.py.
"""

from retro.exceptions import InvalidImage, PhotoTooSmall, RetroError, StepFailed, StepNotImplemented
from retro.imageio import Photo, count_colors, encode_png, read_photo, to_pil
from retro.palettes import DEFAULT_PALETTE, PALETTES, Palette
from retro.pipeline import AvatarMaker, AvatarOptions, StepResult, Trace

__all__ = [
    "DEFAULT_PALETTE", "PALETTES", "AvatarMaker", "AvatarOptions", "InvalidImage", "Palette",
    "Photo", "PhotoTooSmall", "RetroError", "StepFailed", "StepNotImplemented", "StepResult",
    "Trace", "count_colors", "encode_png", "read_photo", "to_pil",
]
