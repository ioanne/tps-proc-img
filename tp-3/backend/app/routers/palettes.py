from fastapi import APIRouter

from app.schemas import PaletteOut
from retro import PALETTES, Palette

router = APIRouter(prefix="/api", tags=["palettes"])


def palette_out(palette: Palette) -> PaletteOut:
    return PaletteOut(name=palette.name, label=palette.label, colors=list(palette.hex_colors),
                      monochrome=palette.monochrome)


@router.get("/palettes", response_model=list[PaletteOut], summary="List the palettes")
def list_palettes():
    return [palette_out(p) for p in PALETTES.values()]
