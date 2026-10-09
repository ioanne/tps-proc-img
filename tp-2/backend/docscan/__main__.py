import argparse
import sys
from pathlib import Path

from docscan.exceptions import ScanError
from docscan.imageio import encode_png, read_photo
from docscan.scanner import Scanner


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan document photo to clean PNG.")
    parser.add_argument("input", help="Path to input photo")
    parser.add_argument("output", help="Path to output PNG image")
    parser.add_argument(
        "--color-mode",
        choices=["color", "grayscale", "bw"],
        default="color",
        help="Color mode of output",
    )
    parser.add_argument(
        "--no-color-correction",
        action="store_false",
        dest="color_correction",
        help="Disable color correction",
    )
    parser.set_defaults(color_correction=True)
    parser.add_argument(
        "--soften-colors",
        type=float,
        default=0.0,
        help="Soften strong colors (0.0 to 1.0)",
    )

    args = parser.parse_args()

    try:
        in_path = Path(args.input)
        if not in_path.is_file():
            sys.stderr.write(f"Error: El archivo de entrada '{args.input}' no existe.\n")
            sys.exit(1)

        content = in_path.read_bytes()
        photo = read_photo(content)

        scanner = Scanner()
        result = scanner.scan(
            photo.image,
            color_mode=args.color_mode,
            color_correction=args.color_correction,
            soften_colors=args.soften_colors,
        )

        png_bytes = encode_png(result.image)
        Path(args.output).write_bytes(png_bytes)
        sys.exit(0)

    except ScanError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)
    except Exception as exc:
        sys.stderr.write(f"Error inesperado: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()