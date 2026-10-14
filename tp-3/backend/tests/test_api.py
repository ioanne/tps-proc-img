"""
The whole app, through the API. DO NOT MODIFY.

    pytest tests/test_api.py -v

The API is given: these tests pass when the six steps are done. Run them at the end.
"""

import base64
import os
import subprocess
import sys
import textwrap

import numpy as np
import pytest
from PIL import Image

from helpers import BACKEND_DIR, as_hex, colors_of, decode, encode, palette_colors, rgb, uniform
from retro import PALETTES

MB = 1024 * 1024
STEP_NAMES = ["photo", "square_crop", "shrink", "gradient_map", "floyd_steinberg", "frame", "enlarge"]


def portrait(width: int = 400, height: int = 300) -> np.ndarray:
    """A "photo": a vertical gradient as background and a face in the middle."""
    y, x = np.mgrid[0:height, 0:width]
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[..., 0] = 60 + 120 * y // height
    img[..., 1] = 120 + 80 * y // height
    img[..., 2] = 220 - 60 * y // height
    cx, cy, r = width / 2, height / 2, min(width, height) * 0.35
    img[(x - cx) ** 2 + (y - cy) ** 2 < r ** 2] = (235, 190, 160)
    for ex in (cx - r * 0.35, cx + r * 0.35):
        img[(x - ex) ** 2 + (y - cy + r * 0.2) ** 2 < (r * 0.12) ** 2] = (30, 30, 40)
    return img


def post(client, path: str, content: bytes, name: str = "photo.png", mime: str = "image/png", **options):
    data = {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in options.items()}
    return client.post(path, files={"file": (name, content, mime)}, data=data)


def avatar(client, image: np.ndarray | None = None, **options) -> np.ndarray:
    r = post(client, "/api/avatar", encode(portrait() if image is None else image), **options)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    image = decode(r.content)
    assert image.shape == (512, 512, 3), f"The avatar must be 512×512, got {image.shape[1]}×{image.shape[0]}"
    return image


def steps(client, image: np.ndarray | None = None, **options) -> dict:
    r = post(client, "/api/avatar/steps", encode(portrait() if image is None else image), **options)
    assert r.status_code == 200, r.text
    return r.json()


def assert_error(r, status: int, code: str):
    assert r.status_code == status, f"Expected {status}, got {r.status_code}: {r.text}"
    detail = r.json()["detail"]
    assert detail["code"] == code, detail
    assert detail["message"].strip(), "Missing 'message'"


def assert_complete(body: dict):
    pending = [f"{s['class_name']}: {s['status']}" for s in body["steps"] if s["status"] not in ("input", "done")]
    assert body["complete"] and not pending, f"Steps not done yet: {pending}"


# ===========================================================================
# Given: system, palettes and validation (these pass from the start)
# ===========================================================================

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_palettes(client):
    r = client.get("/api/palettes")
    assert r.status_code == 200, r.text
    body = {p["name"]: p for p in r.json()}
    assert set(body) == set(PALETTES)
    assert body["gameboy"] == {"name": "gameboy", "label": "Game Boy", "monochrome": True,
                               "colors": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]}


@pytest.mark.parametrize("path", ["/api/avatar", "/api/avatar/steps"])
def test_file_too_large(client, path):
    assert_error(post(client, path, encode(portrait()) + b"\0" * (10 * MB)), 413, "FILE_TOO_LARGE")


@pytest.mark.parametrize("content", [b"", b"this is not an image", b"\x89PNG\r\n\x1a\n broken"],
                         ids=["empty", "text", "corrupt-png"])
def test_invalid_file(client, content):
    assert_error(post(client, "/api/avatar", content), 400, "INVALID_FILE")


def test_unsupported_format(client):
    r = post(client, "/api/avatar", encode(portrait(), "GIF"), "photo.gif", "image/gif")
    assert_error(r, 400, "UNSUPPORTED_FORMAT")


def test_missing_file(client):
    assert client.post("/api/avatar").status_code == 422


@pytest.mark.parametrize("options", [
    {"pixels": 20}, {"pixels": "a lot"}, {"palette": "nes"}, {"palette": "GameBoy"},
    {"frame": 5}, {"frame": -1}, {"dithering": "maybe"},
])
def test_invalid_options(client, options):
    assert post(client, "/api/avatar", encode(portrait()), **options).status_code == 422


def test_photo_too_small(client):
    r = post(client, "/api/avatar", encode(portrait(40, 20)), pixels=32)
    assert_error(r, 422, "PHOTO_TOO_SMALL")


def test_steps_are_listed_in_order(client):
    body = steps(client, dithering=True, frame=1)
    assert [s["name"] for s in body["steps"]] == STEP_NAMES
    assert body["steps"][0]["status"] == "input"
    assert (body["steps"][0]["width"], body["steps"][0]["height"]) == (400, 300)


def test_color_palettes_have_no_tone_ramp(client):
    names = [s["name"] for s in steps(client, palette="pico8")["steps"]]
    assert names == ["photo", "square_crop", "shrink", "palette_map", "enlarge"]


def test_core_does_not_depend_on_the_api():
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent("""
            import sys
            import retro, retro.__main__  # noqa: F401
            print([m for m in sys.modules if m.split(".")[0] in {"fastapi", "starlette", "app"}])
        """)], cwd=BACKEND_DIR, capture_output=True, text=True, timeout=120, env=os.environ.copy())
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", f"retro must not import the API: {result.stdout}"


# ===========================================================================
# The avatar (these pass when the six steps are done)
# ===========================================================================

def test_avatar_is_a_512_png(client):
    r = post(client, "/api/avatar", encode(portrait()))
    assert r.status_code == 200, r.text
    image = decode(r.content)
    assert image.shape == (512, 512, 3), f"The avatar must be 512×512, got {image.shape[1]}×{image.shape[0]}"
    assert r.headers["x-avatar-complete"] == "true"


@pytest.mark.parametrize("dithering", [False, True], ids=["no-dithering", "dithering"])
@pytest.mark.parametrize("palette", sorted(PALETTES))
def test_avatar_uses_only_palette_colors(client, palette, dithering):
    image = avatar(client, palette=palette, dithering=dithering)
    extra = colors_of(image) - palette_colors(palette)
    assert not extra, f"Colors that are not in {palette}: {sorted(as_hex(c) for c in extra)[:5]}"


@pytest.mark.parametrize("pixels", [16, 32, 64, 128])
def test_avatar_is_made_of_big_pixels(client, pixels):
    image = avatar(client, pixels=pixels, dithering=True)
    size = 512 // pixels
    blocks = image.reshape(pixels, size, pixels, size, 3)
    uniform_blocks = (blocks == blocks[:, :1, :, :1]).all(axis=(1, 3, 4))
    assert uniform_blocks.all(), f"Each big pixel must be a uniform {size}×{size} block"


def test_avatar_frame(client):
    image = avatar(client, pixels=32, frame=2)
    darkest = tuple(PALETTES["gameboy"].darkest.tolist())
    ring = np.ones((512, 512), dtype=bool)
    ring[32:-32, 32:-32] = False  # 2 big pixels of 16 screen pixels
    assert colors_of(image[ring]) == {darkest}, "A frame of 2 big pixels of the darkest color"
    assert colors_of(image[32:-32, 32:-32]) != {darkest}, "Inside the frame there is the photo"


def test_avatar_is_the_center_of_the_photo(client):
    photo = uniform(200, 300, (0, 228, 54))  # PICO-8 green…
    photo[:, :40] = photo[:, -40:] = (255, 0, 77)  # …with red bands on the sides, outside the square
    image = avatar(client, photo, palette="pico8")
    assert colors_of(image) == {rgb("#00e436")}, "Only the centered square of the photo is used"


def test_dithering_mixes_two_colors(client):
    gray = uniform(256, 256, 128)  # in the Game Boy ramp, between the 2nd and 3rd greens
    plain = avatar(client, gray, dithering=False)
    assert len(colors_of(plain)) == 1
    mixed = avatar(client, gray, dithering=True)
    colors, counts = np.unique(mixed.reshape(-1, 3), axis=0, return_counts=True)
    shares = {as_hex(c): round(float(n / counts.sum()), 2) for c, n in zip(colors, counts)}
    assert shares.get("#306230", 0) >= 0.3 and shares.get("#8bac0f", 0) >= 0.3, (
        f"Expected about half #306230 and half #8bac0f, got {shares}")


def test_avatar_respects_exif_orientation(client):
    photo = np.zeros((300, 300, 3), dtype=np.uint8)
    photo[150:] = 255  # dark at the top, light at the bottom (as it is seen)
    stored = Image.fromarray(photo).transpose(Image.Transpose.ROTATE_90)  # how the phone stores it
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90° clockwise to display
    r = post(client, "/api/avatar", encode(stored, "JPEG", quality=95, exif=exif), "phone.jpg", "image/jpeg")
    image = decode(r.content).astype(float)
    assert image[:100].mean() < image[-100:].mean(), "The top of the photo must stay at the top"


# ===========================================================================
# /api/avatar/steps (these pass when the six steps are done)
# ===========================================================================

def test_every_step_is_done(client):
    assert_complete(steps(client, dithering=True, frame=1))
    assert_complete(steps(client, palette="pico8"))


def test_steps_sizes(client):
    body = steps(client, pixels=64, dithering=True, frame=1)
    assert_complete(body)
    sizes = {s["name"]: (s["width"], s["height"]) for s in body["steps"]}
    assert sizes == {"photo": (400, 300), "square_crop": (300, 300), "shrink": (64, 64), "gradient_map": (64, 64),
                     "floyd_steinberg": (64, 64), "frame": (64, 64), "enlarge": (512, 512)}


def test_steps_respect_the_palette_after_mapping(client):
    body = steps(client, palette="cga", dithering=True, frame=1)
    assert_complete(body)
    for step in body["steps"][3:]:
        assert step["colors"] <= 4, f"{step['class_name']} has {step['colors']} colors: CGA has 4"


def test_last_step_is_the_avatar(client):
    body = steps(client, dithering=True)
    assert_complete(body)
    last = body["steps"][-1]["image"]
    prefix = "data:image/png;base64,"
    assert last.startswith(prefix)
    assert np.array_equal(decode(base64.b64decode(last[len(prefix):])), avatar(client, dithering=True))


def test_cli(tmp_path):
    source, target = tmp_path / "photo.png", tmp_path / "avatar.png"
    source.write_bytes(encode(portrait()))
    result = subprocess.run(
        [sys.executable, "-m", "retro", source, target, "--palette", "cga", "--dithering", "--pixels", "16"],
        cwd=BACKEND_DIR, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    image = decode(target.read_bytes())
    assert image.shape == (512, 512, 3)
    assert colors_of(image) <= palette_colors("cga")
