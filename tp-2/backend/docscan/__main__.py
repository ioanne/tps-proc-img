import argparse
import sys
from pathlib import Path

from docscan import encode_png, read_photo
from docscan.exceptions import ScanError
from docscan.scanner import Scanner


def parse_soften_colors(value: str) -> float:
    try:
        amount = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un número entre 0 y 1") from exc

    if not 0 <= amount <= 1:
        raise argparse.ArgumentTypeError("debe ser un número entre 0 y 1")

    return amount


def main() -> int:
    parser = argparse.ArgumentParser(description="Escanea una foto de un documento.")
    parser.add_argument("entrada", type=Path, help="foto de entrada")
    parser.add_argument("salida", type=Path, help="archivo PNG de salida")
    parser.add_argument(
        "--color-mode",
        choices=("color", "grayscale", "bw"),
        default="color",
    )
    parser.add_argument("--no-color-correction", action="store_false", dest="color_correction")
    parser.add_argument("--soften-colors", type=parse_soften_colors, default=0.0)
    args = parser.parse_args()

    try:
        photo = read_photo(args.entrada.read_bytes())
        scanned, _ = Scanner().scan(
            photo.image,
            color_mode=args.color_mode,
            color_correction=args.color_correction,
            soften_colors=args.soften_colors,
        )
        args.salida.write_bytes(encode_png(scanned))
    except (OSError, ScanError) as exc:
        print(f"No se pudo escanear la imagen: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())