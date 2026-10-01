"""
Team tests: building an operation with invalid parameters raises the domain
exception `InvalidParameters` (which the API translates to a 400).

Only the domain rules are tested here, the ones the schemas cannot express.
Ranges (e.g. 0 <= factor <= 3) are validated by FastAPI and answered with 422.
Each rule also has a "valid" counterpart, to make sure the validation is not
rejecting values it should accept.
"""

import pytest

from app.core.exceptions import InvalidParameters
from app.core.operations import Blur, Edges, Mirror, Resize


# --- Blur: kernel_size must be odd -------------------------------------------

@pytest.mark.parametrize("kernel_size", [2, 4, 50])
def test_blur_even_kernel_raises(kernel_size):
    with pytest.raises(InvalidParameters):
        Blur(kernel_size=kernel_size)


@pytest.mark.parametrize("kernel_size", [1, 3, 51])
def test_blur_odd_kernel_is_valid(kernel_size):
    blur = Blur(kernel_size=kernel_size)
    assert blur.parameters["kernel_size"] == kernel_size


# --- Edges: lower_threshold must be strictly less than upper_threshold -------

@pytest.mark.parametrize(
    "lower, upper",
    [(200, 100), (150, 150), (255, 0)],
    ids=["lower_greater", "equal", "extremes_inverted"],
)
def test_edges_invalid_thresholds_raise(lower, upper):
    with pytest.raises(InvalidParameters):
        Edges(lower_threshold=lower, upper_threshold=upper)


def test_edges_valid_thresholds():
    edges = Edges(lower_threshold=100, upper_threshold=101)
    assert edges.parameters == {"lower_threshold": 100, "upper_threshold": 101}


# --- Resize: height is required when keep_aspect_ratio is False --------------

def test_resize_without_height_and_without_aspect_ratio_raises():
    with pytest.raises(InvalidParameters):
        Resize(width=100, keep_aspect_ratio=False)


def test_resize_with_height_and_without_aspect_ratio_is_valid():
    resize = Resize(width=100, height=50, keep_aspect_ratio=False)
    assert resize.parameters["height"] == 50


def test_resize_without_height_keeping_aspect_ratio_is_valid():
    resize = Resize(width=100)
    assert resize.parameters["height"] is None


# --- Mirror: direction must be "horizontal" or "vertical" --------------------

@pytest.mark.parametrize("direction", ["diagonal", "", "left"])
def test_mirror_invalid_direction_raises(direction):
    with pytest.raises(InvalidParameters):
        Mirror(direction=direction)


@pytest.mark.parametrize("direction", ["horizontal", "vertical"])
def test_mirror_valid_direction(direction):
    assert Mirror(direction=direction).parameters["direction"] == direction


# --- The exception carries the contract error code ---------------------------

def test_invalid_parameters_has_contract_code():
    with pytest.raises(InvalidParameters) as exc_info:
        Blur(kernel_size=4)
    assert exc_info.value.code == "INVALID_PARAMETERS"
