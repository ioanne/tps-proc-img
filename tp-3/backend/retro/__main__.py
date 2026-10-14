"""
Command line. Given.

    python -m retro PHOTO AVATAR [--pixels N] [--palette NAME] [--dithering] [--frame N] [--steps FOLDER]

Writes the avatar as PNG and prints what happened in each step. With --steps it
also saves the image of every step in FOLDER (01-square_crop.png, …), handy to
see where something goes wrong without opening the frontend.
"""

import argparse
import sys
from pathlib import Path

from retro.exceptions import RetroError
from retro.imageio import count_colors, encode_png, read_photo
from retro.palettes import DEFAULT_PALETTE, PALETTES
from retro.pipeline import MAX_FRAME, PIXEL_SIZES, AvatarMaker, AvatarOptions

SYMBOLS = {"done": "✓", "pending": "·", "blocked": "-", "failed": "✗"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m retro", description="Turns a photo into a retro avatar.")
    parser.add_argument("photo", type=Path)
    parser.add_argument("avatar", type=Path)
    parser.add_argument("--pixels", type=int, choices=PIXEL_SIZES, default=32)
    parser.add_argument("--palette", choices=sorted(PALETTES), default=DEFAULT_PALETTE)
    parser.add_argument("--dithering", action="store_true")
    parser.add_argument("--frame", type=int, choices=range(MAX_FRAME + 1), default=0, metavar=f"{{0..{MAX_FRAME}}}")
    parser.add_argument("--steps", type=Path, metavar="FOLDER", help="also save the image of every step here")
    args = parser.parse_args(argv)

    options = AvatarOptions(pixels=args.pixels, palette=args.palette, dithering=args.dithering, frame=args.frame)
    try:
        photo = read_photo(args.photo.read_bytes())
        trace = AvatarMaker().run(photo.image, options)
    except OSError as exc:
        print(f"No se pudo leer {args.photo}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except RetroError as exc:
        print(exc, file=sys.stderr)
        return 1

    for i, result in enumerate(trace.results, start=1):
        line = f"{SYMBOLS[result.status]} {i}. {result.step.label:<16}"
        if result.image is not None:
            h, w = result.image.shape[:2]
            line += f"{w}×{h}, {count_colors(result.image)} colores"
        print(line + (f"  {result.message}" if result.message else ""))
        if args.steps and result.image is not None:
            args.steps.mkdir(parents=True, exist_ok=True)
            (args.steps / f"{i:02d}-{result.step.name}.png").write_bytes(encode_png(result.image))

    if trace.failure:
        print(trace.failure.message, file=sys.stderr)
        return 1
    args.avatar.write_bytes(encode_png(trace.image))
    print(f"Avatar guardado en {args.avatar}" + ("" if trace.complete else " (faltan pasos)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
