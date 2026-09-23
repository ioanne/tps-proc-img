"""
Acceptance tests: the API contract in executable form. DO NOT MODIFY.

If a test in this file fails, the implementation does not meet the assignment.
Run with:   cd backend && pytest tests/test_contract.py -v

The team's own tests (core unit tests, etc.) go in other files.
"""

import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from conftest import DB_PATH, STORAGE_DIR

MB = 1024 * 1024

RED, BLUE, GREEN, WHITE, BLACK = (255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 255), (0, 0, 0)
GRAY = (128, 128, 128)

IMAGE_OUT_FIELDS = {
    "id", "original_name", "url", "width", "height", "format", "size_bytes",
    "operation", "parameters", "source_id", "created_at",
}


# ===========================================================================
# Image generators
# ===========================================================================

def quadrants(width: int = 200, height: int = 100, mode: str = "RGB") -> Image.Image:
    """Four quadrants: top-left RED, top-right BLUE, bottom-left GREEN, bottom-right WHITE."""
    img = Image.new("RGB", (width, height))
    mx, my = width // 2, height // 2
    img.paste(RED, (0, 0, mx, my))
    img.paste(BLUE, (mx, 0, width, my))
    img.paste(GREEN, (0, my, mx, height))
    img.paste(WHITE, (mx, my, width, height))
    if mode == "RGBA":
        img.putalpha(128)
    elif mode == "P":
        img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=8)
    elif mode != "RGB":
        img = img.convert(mode)
    return img


def checkerboard(side: int = 64) -> Image.Image:
    """1 px checkerboard: maximum variation between neighboring pixels."""
    img = Image.new("L", (side, side))
    img.putdata([255 if (x + y) % 2 else 0 for y in range(side) for x in range(side)])
    return img.convert("RGB")


def salt_noise(side: int = 40) -> Image.Image:
    """Gray background with isolated white pixels (what a median filter removes)."""
    img = Image.new("RGB", (side, side), GRAY)
    for y in range(2, side, 5):
        for x in range(2, side, 5):
            img.putpixel((x, y), WHITE)
    return img


def to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ===========================================================================
# HTTP helpers
# ===========================================================================

def upload(client, content: bytes, name: str = "photo.png", mime: str = "image/png"):
    return client.post("/api/images", files={"file": (name, content, mime)})


def upload_ok(client, img: Image.Image | None = None, fmt: str = "PNG", name: str = "photo.png") -> dict:
    img = img if img is not None else quadrants()
    mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "BMP": "image/bmp"}[fmt]
    r = upload(client, to_bytes(img, fmt), name, mime)
    assert r.status_code == 201, r.text
    return r.json()


def operate(client, image_id: int, operation: str, body: dict | None = None):
    if body is None:
        return client.post(f"/api/images/{image_id}/{operation}")
    return client.post(f"/api/images/{image_id}/{operation}", json=body)


def operate_ok(client, image_id: int, operation: str, body: dict | None = None) -> dict:
    r = operate(client, image_id, operation, body)
    assert r.status_code == 201, r.text
    return r.json()


def download(client, image: dict) -> Image.Image:
    r = client.get(image["url"])
    assert r.status_code == 200, f"Could not download {image['url']}: {r.status_code}"
    img = Image.open(BytesIO(r.content))
    img.load()
    return img


def assert_error(r, status: int, code: str):
    assert r.status_code == status, f"Expected {status}, got {r.status_code}: {r.text}"
    body = r.json()
    assert "detail" in body, f"The error must come in 'detail': {body}"
    detail = body["detail"]
    assert isinstance(detail, dict), f"'detail' must be a {{code, message}} object: {detail}"
    assert detail.get("code") == code, f"Expected code={code}: {detail}"
    assert isinstance(detail.get("message"), str) and detail["message"].strip(), "Missing 'message'"


def close(a, b, tolerance: int = 3) -> bool:
    a = a if isinstance(a, tuple) else (a,)
    b = b if isinstance(b, tuple) else (b,)
    return len(a) == len(b) and all(abs(x - y) <= tolerance for x, y in zip(a, b))


def rgb(img: Image.Image, xy: tuple[int, int]) -> tuple:
    return img.convert("RGB").getpixel(xy)


# ===========================================================================
# System
# ===========================================================================

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ===========================================================================
# RF1 · Upload image
# ===========================================================================

class TestUpload:
    def test_returns_full_image_out(self, client):
        r = upload(client, to_bytes(quadrants()), "cat.png")
        assert r.status_code == 201, r.text
        img = r.json()
        assert set(img) == IMAGE_OUT_FIELDS
        assert isinstance(img["id"], int)
        assert img["original_name"] == "cat.png"
        assert img["url"].startswith("/media/")
        assert (img["width"], img["height"]) == (200, 100)
        assert img["format"] == "PNG"
        assert img["operation"] is None
        assert img["parameters"] is None
        assert img["source_id"] is None
        datetime.fromisoformat(img["created_at"])

    def test_the_file_is_served_at_the_url(self, client):
        img = upload_ok(client)
        r = client.get(img["url"])
        assert r.status_code == 200
        assert len(r.content) == img["size_bytes"]
        assert Image.open(BytesIO(r.content)).size == (img["width"], img["height"])

    def test_the_file_is_stored_in_storage_dir(self, client):
        img = upload_ok(client)
        file_name = img["url"].removeprefix("/media/")
        assert (STORAGE_DIR / file_name).is_file()

    def test_the_url_is_stored_in_the_images_table(self, client):
        img = upload_ok(client)
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT url FROM images WHERE id = ?", (img["id"],)).fetchone()
        assert row is not None, "There is no row in the 'images' table with that id"
        assert row[0] == img["url"]

    def test_unique_file_name_generated_by_the_backend(self, client):
        content = to_bytes(quadrants())
        a = upload(client, content, "photo.png").json()
        b = upload(client, content, "photo.png").json()
        assert a["id"] != b["id"]
        assert a["url"] != b["url"]
        assert not a["url"].endswith("/photo.png"), "The user's name must not be used as the file name"

    @pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP", "BMP"])
    def test_accepted_formats(self, client, fmt):
        img = upload_ok(client, fmt=fmt, name=f"photo.{fmt.lower()}")
        assert img["format"] == fmt
        assert download(client, img).format == fmt

    def test_the_format_is_detected_by_content(self, client):
        r = upload(client, to_bytes(quadrants(), "PNG"), "misleading.jpg", "application/octet-stream")
        assert r.status_code == 201, r.text
        assert r.json()["format"] == "PNG"

    def test_unsupported_format(self, client):
        r = upload(client, to_bytes(quadrants(), "GIF"), "animated.gif", "image/gif")
        assert_error(r, 400, "UNSUPPORTED_FORMAT")

    def test_file_that_is_not_an_image(self, client):
        r = upload(client, b"this is not an image" * 10, "fake.png", "image/png")
        assert_error(r, 400, "INVALID_FILE")

    def test_empty_file(self, client):
        assert_error(upload(client, b"", "empty.png", "image/png"), 400, "INVALID_FILE")

    def test_file_too_large(self, client):
        r = upload(client, b"\0" * (10 * MB + 1), "huge.png", "image/png")
        assert_error(r, 413, "FILE_TOO_LARGE")

    def test_without_file(self, client):
        assert client.post("/api/images").status_code == 422


# ===========================================================================
# RF2 / RF3 · List and get
# ===========================================================================

class TestListAndGet:
    def test_list_by_descending_id(self, client):
        a = upload_ok(client)
        b = upload_ok(client)
        r = client.get("/api/images")
        assert r.status_code == 200
        items = r.json()
        ids = [i["id"] for i in items]
        assert ids == sorted(ids, reverse=True)
        assert ids.index(b["id"]) < ids.index(a["id"])
        assert all(set(i) == IMAGE_OUT_FIELDS for i in items)

    def test_list_includes_derived(self, client):
        original = upload_ok(client)
        derived = operate_ok(client, original["id"], "mirror", {})
        ids = [i["id"] for i in client.get("/api/images").json()]
        assert original["id"] in ids and derived["id"] in ids

    def test_get(self, client):
        img = upload_ok(client)
        r = client.get(f"/api/images/{img['id']}")
        assert r.status_code == 200
        assert r.json() == img

    def test_get_nonexistent(self, client):
        assert_error(client.get("/api/images/999999"), 404, "IMAGE_NOT_FOUND")


# ===========================================================================
# RF4 · Delete
# ===========================================================================

class TestDelete:
    def test_deletes_record_and_file(self, client):
        img = upload_ok(client)
        file_name = img["url"].removeprefix("/media/")
        r = client.delete(f"/api/images/{img['id']}")
        assert r.status_code == 204
        assert r.content == b""
        assert_error(client.get(f"/api/images/{img['id']}"), 404, "IMAGE_NOT_FOUND")
        assert not (STORAGE_DIR / file_name).exists()
        assert client.get(img["url"]).status_code == 404

    def test_delete_nonexistent(self, client):
        assert_error(client.delete("/api/images/999999"), 404, "IMAGE_NOT_FOUND")

    def test_derived_images_are_kept_without_source(self, client):
        original = upload_ok(client)
        derived = operate_ok(client, original["id"], "brightness", {"factor": 1.2})
        assert client.delete(f"/api/images/{original['id']}").status_code == 204
        r = client.get(f"/api/images/{derived['id']}")
        assert r.status_code == 200
        assert r.json()["source_id"] is None
        assert client.get(derived["url"]).status_code == 200


# ===========================================================================
# RF5 · Rules common to the 10 operations
# ===========================================================================

# (route, body sent, expected `parameters` in the response = body with defaults)
CASES = [
    ("brightness", {"factor": 1.5}, {"factor": 1.5}),
    ("contrast", {"factor": 0.5}, {"factor": 0.5}),
    ("saturation", {}, {"factor": 1.0}),
    ("sharpness", {"factor": 2}, {"factor": 2.0}),
    ("grayscale", None, {}),
    ("blur", {"kernel_size": 3}, {"method": "gaussian", "kernel_size": 3}),
    ("edges", {}, {"lower_threshold": 100, "upper_threshold": 200}),
    ("rotation", {"angle": 45}, {"angle": 45.0, "expand": True}),
    ("mirror", {"direction": "vertical"}, {"direction": "vertical"}),
    ("resize", {"width": 50}, {"width": 50, "height": None, "keep_aspect_ratio": True}),
]
IDS = [c[0] for c in CASES]


class TestCommonRules:
    @pytest.mark.parametrize("route,body,expected", CASES, ids=IDS)
    def test_creates_a_new_image(self, client, route, body, expected):
        source = upload_ok(client, name="source.png")
        r = operate(client, source["id"], route, body)
        assert r.status_code == 201, r.text
        res = r.json()
        assert set(res) == IMAGE_OUT_FIELDS
        assert res["id"] != source["id"]
        assert res["source_id"] == source["id"]
        assert res["operation"] == route
        assert res["parameters"] == expected
        assert res["original_name"] == "source.png"
        assert res["url"] != source["url"]
        assert res["format"] == "PNG"
        file = download(client, res)
        assert file.size == (res["width"], res["height"])
        assert client.get(f"/api/images/{res['id']}").json() == res

    @pytest.mark.parametrize("route,body,expected", CASES, ids=IDS)
    def test_does_not_modify_the_source_image(self, client, route, body, expected):
        source = upload_ok(client)
        bytes_before = client.get(source["url"]).content
        operate_ok(client, source["id"], route, body)
        assert client.get(source["url"]).content == bytes_before
        assert client.get(f"/api/images/{source['id']}").json() == source

    @pytest.mark.parametrize("route,body,expected", CASES, ids=IDS)
    def test_nonexistent_image(self, client, route, body, expected):
        assert_error(operate(client, 999999, route, body), 404, "IMAGE_NOT_FOUND")

    @pytest.mark.parametrize("fmt", ["JPEG", "WEBP", "BMP"])
    @pytest.mark.parametrize("route,body,expected", CASES, ids=IDS)
    def test_keeps_the_format(self, client, fmt, route, body, expected):
        source = upload_ok(client, fmt=fmt)
        res = operate_ok(client, source["id"], route, body)
        assert res["format"] == fmt
        assert download(client, res).format == fmt

    @pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
    @pytest.mark.parametrize("route,body,expected", CASES, ids=IDS)
    def test_accepts_any_color_mode(self, client, mode, route, body, expected):
        source = upload_ok(client, quadrants(mode=mode))
        operate_ok(client, source["id"], route, body)

    def test_a_result_can_be_edited(self, client):
        source = upload_ok(client)
        first = operate_ok(client, source["id"], "mirror", {})
        second = operate_ok(client, first["id"], "grayscale")
        assert second["source_id"] == first["id"]

    def test_out_of_range_parameters_give_422(self, client):
        source = upload_ok(client)
        assert operate(client, source["id"], "brightness", {"factor": 3.5}).status_code == 422
        assert operate(client, source["id"], "blur", {"method": "other"}).status_code == 422
        assert operate(client, source["id"], "resize", {}).status_code == 422

    def test_400_takes_priority_over_404(self, client):
        r = operate(client, 999999, "blur", {"kernel_size": 4})
        assert_error(r, 400, "INVALID_PARAMETERS")


# ===========================================================================
# RF5 · Behavior of each operation
# ===========================================================================

class TestBrightness:
    def test_factor_zero_gives_black(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "brightness", {"factor": 0})
        assert download(client, res).convert("RGB").getextrema() == ((0, 0), (0, 0), (0, 0))

    def test_factor_one_does_not_change(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "brightness", {"factor": 1})
        img = download(client, res)
        for xy in [(20, 20), (150, 20), (20, 80), (150, 80)]:
            assert close(rgb(img, xy), rgb(quadrants(), xy))

    def test_greater_factor_brightens(self, client):
        source = upload_ok(client, Image.new("RGB", (20, 20), GRAY))
        res = operate_ok(client, source["id"], "brightness", {"factor": 1.5})
        assert close(rgb(download(client, res), (5, 5)), (192, 192, 192))

    def test_keeps_the_alpha_channel(self, client):
        source = upload_ok(client, quadrants(mode="RGBA"))
        img = download(client, operate_ok(client, source["id"], "brightness", {"factor": 0.5}))
        assert img.mode == "RGBA"
        assert img.getchannel("A").getextrema() == (128, 128)


class TestContrast:
    def test_factor_zero_gives_a_single_color(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "contrast", {"factor": 0})
        extrema = download(client, res).convert("RGB").getextrema()
        assert all(hi - lo <= 2 for lo, hi in extrema)

    def test_greater_factor_increases_the_difference(self, client):
        img = Image.new("RGB", (20, 10), (100, 100, 100))
        img.paste((150, 150, 150), (10, 0, 20, 10))
        res = operate_ok(client, upload_ok(client, img)["id"], "contrast", {"factor": 2})
        out = download(client, res)
        assert rgb(out, (15, 5))[0] - rgb(out, (5, 5))[0] > 50


class TestSaturation:
    def test_factor_zero_removes_the_color(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "saturation", {"factor": 0})
        img = download(client, res).convert("RGB")
        for xy in [(20, 20), (150, 20), (20, 80)]:
            r, g, b = img.getpixel(xy)
            assert max(r, g, b) - min(r, g, b) <= 2

    def test_keeps_the_alpha_channel(self, client):
        source = upload_ok(client, quadrants(mode="RGBA"))
        img = download(client, operate_ok(client, source["id"], "saturation", {"factor": 2}))
        assert img.mode == "RGBA"
        assert img.getchannel("A").getextrema() == (128, 128)


class TestSharpness:
    def test_factor_one_does_not_change(self, client):
        res = operate_ok(client, upload_ok(client, checkerboard())["id"], "sharpness", {"factor": 1})
        img = download(client, res)
        assert all(close(rgb(img, (x, 10)), rgb(checkerboard(), (x, 10))) for x in range(10, 20))

    def test_factor_zero_smooths(self, client):
        res = operate_ok(client, upload_ok(client, checkerboard())["id"], "sharpness", {"factor": 0})
        lo, hi = download(client, res).convert("L").crop((5, 5, 59, 59)).getextrema()
        assert hi - lo < 255


class TestGrayscale:
    def test_single_channel_result(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "grayscale")
        assert download(client, res).mode == "L"

    def test_uses_luminance(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "grayscale")
        img = download(client, res)
        assert close(img.getpixel((20, 20)), 76)    # red   -> 0.299 * 255
        assert close(img.getpixel((150, 80)), 255)  # white


class TestBlur:
    @pytest.mark.parametrize("method", ["gaussian", "average"])
    def test_smooths(self, client, method):
        res = operate_ok(client, upload_ok(client, checkerboard())["id"], "blur",
                         {"method": method, "kernel_size": 5})
        lo, hi = download(client, res).convert("L").crop((8, 8, 56, 56)).getextrema()
        assert hi - lo < 100

    def test_median_removes_salt_noise(self, client):
        res = operate_ok(client, upload_ok(client, salt_noise())["id"], "blur",
                         {"method": "median", "kernel_size": 3})
        assert download(client, res).convert("L").getextrema() == (128, 128)

    def test_kernel_one_is_valid(self, client):
        operate_ok(client, upload_ok(client)["id"], "blur", {"kernel_size": 1})

    @pytest.mark.parametrize("kernel", [2, 4, 50])
    def test_even_kernel_is_invalid(self, client, kernel):
        r = operate(client, upload_ok(client)["id"], "blur", {"kernel_size": kernel})
        assert_error(r, 400, "INVALID_PARAMETERS")


class TestEdges:
    def test_binary_single_channel_result(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "edges", {})
        img = download(client, res)
        assert img.mode == "L"
        values = {v for v, _ in enumerate(img.histogram()) if img.histogram()[v]}
        assert values <= {0, 255}
        assert 255 in values, "The test image has sharp edges: it should detect them"

    def test_uniform_areas_without_edges(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "edges", {})
        img = download(client, res)
        assert img.getpixel((20, 20)) == 0
        assert img.getpixel((150, 80)) == 0

    @pytest.mark.parametrize("lower,upper", [(100, 100), (200, 100)])
    def test_inverted_thresholds(self, client, lower, upper):
        r = operate(client, upload_ok(client)["id"], "edges",
                    {"lower_threshold": lower, "upper_threshold": upper})
        assert_error(r, 400, "INVALID_PARAMETERS")


class TestRotation:
    def test_90_counterclockwise_with_expand(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "rotation", {"angle": 90, "expand": True})
        assert close((res["width"], res["height"]), (100, 200), 1)
        img = download(client, res)
        assert close(rgb(img, (20, 20)), BLUE, 10)     # top-right moves to top-left
        assert close(rgb(img, (80, 20)), WHITE, 10)    # bottom-right moves to top-right
        assert close(rgb(img, (20, 180)), RED, 10)     # top-left moves to bottom-left

    def test_negative_angle_is_clockwise(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "rotation", {"angle": -90})
        assert close(rgb(download(client, res), (20, 20)), GREEN, 10)

    def test_without_expand_keeps_the_size(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "rotation", {"angle": 45, "expand": False})
        assert (res["width"], res["height"]) == (200, 100)

    def test_expand_enlarges_the_canvas_and_fills_with_black(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "rotation", {"angle": 45, "expand": True})
        assert res["width"] > 200 and res["height"] > 100
        assert close(rgb(download(client, res), (1, 1)), BLACK, 10)

    def test_with_alpha_fills_transparent(self, client):
        source = upload_ok(client, quadrants(mode="RGBA"))
        res = operate_ok(client, source["id"], "rotation", {"angle": 45, "expand": True})
        img = download(client, res)
        assert img.mode == "RGBA"
        assert img.getpixel((1, 1))[3] == 0


class TestMirror:
    def test_horizontal(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "mirror", {"direction": "horizontal"})
        img = download(client, res)
        assert (res["width"], res["height"]) == (200, 100)
        assert rgb(img, (20, 20)) == BLUE
        assert rgb(img, (20, 80)) == WHITE

    def test_vertical(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "mirror", {"direction": "vertical"})
        img = download(client, res)
        assert rgb(img, (20, 20)) == GREEN
        assert rgb(img, (150, 20)) == WHITE

    def test_default_is_horizontal(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "mirror", {})
        assert rgb(download(client, res), (20, 20)) == BLUE


class TestResize:
    def test_keep_aspect_ratio(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "resize", {"width": 50})
        assert (res["width"], res["height"]) == (50, 25)
        assert download(client, res).size == (50, 25)

    def test_rounds_to_the_nearest_integer(self, client):
        source = upload_ok(client, quadrants(300, 200))
        res = operate_ok(client, source["id"], "resize", {"width": 100})
        assert (res["width"], res["height"]) == (100, 67)

    def test_height_is_ignored_if_aspect_ratio_is_kept(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "resize",
                         {"width": 50, "height": 70, "keep_aspect_ratio": True})
        assert (res["width"], res["height"]) == (50, 25)

    def test_without_keeping_aspect_ratio(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "resize",
                         {"width": 50, "height": 70, "keep_aspect_ratio": False})
        assert (res["width"], res["height"]) == (50, 70)

    def test_without_aspect_ratio_height_is_required(self, client):
        r = operate(client, upload_ok(client)["id"], "resize", {"width": 50, "keep_aspect_ratio": False})
        assert_error(r, 400, "INVALID_PARAMETERS")

    def test_enlarge(self, client):
        res = operate_ok(client, upload_ok(client)["id"], "resize", {"width": 400})
        assert (res["width"], res["height"]) == (400, 200)
