import pytest

from app.core.exceptions import InvalidParameters
from app.core.operations import Blur, Edges, Resize


def test_blur_even_kernel_raises():
    with pytest.raises(InvalidParameters):
        Blur(kernel_size=4)


def test_blur_odd_kernel_ok():
    Blur(kernel_size=3)


def test_edges_inverted_thresholds_raises():
    with pytest.raises(InvalidParameters):
        Edges(lower_threshold=200, upper_threshold=100)


def test_edges_equal_thresholds_raises():
    with pytest.raises(InvalidParameters):
        Edges(lower_threshold=100, upper_threshold=100)


def test_resize_no_height_no_ratio_raises():
    with pytest.raises(InvalidParameters):
        Resize(width=100, keep_aspect_ratio=False)


def test_resize_with_height_no_ratio_ok():
    Resize(width=100, height=50, keep_aspect_ratio=False)