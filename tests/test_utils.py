"""Tests for utility functions: curve normalization, monotonic enforcement, and helpers."""

from asus_linux_control_center.utils import (
    clamp,
    make_non_decreasing_curve,
    normalize_curve_values,
    unique_lines,
)

# ─── clamp ────────────────────────────────────────────────────────────────────

def test_clamp_within_range() -> None:
    assert clamp(50, 0, 100) == 50


def test_clamp_below_minimum() -> None:
    assert clamp(-5, 0, 100) == 0


def test_clamp_above_maximum() -> None:
    assert clamp(150, 0, 100) == 100


def test_clamp_at_boundaries() -> None:
    assert clamp(0, 0, 100) == 0
    assert clamp(100, 0, 100) == 100


# ─── normalize_curve_values ───────────────────────────────────────────────────

def test_normalize_empty_values() -> None:
    assert normalize_curve_values([], 8) == [0] * 8


def test_normalize_same_length() -> None:
    values = [10, 20, 30, 40, 50, 60, 70, 80]
    assert normalize_curve_values(values, 8) == values


def test_normalize_clamps_values() -> None:
    result = normalize_curve_values([-10, 50, 200], 3)
    assert result == [0, 50, 100]


def test_normalize_interpolation_upsample() -> None:
    result = normalize_curve_values([0, 100], 3)
    assert result == [0, 50, 100]


def test_normalize_interpolation_downsample() -> None:
    result = normalize_curve_values([0, 50, 100], 2)
    assert result == [0, 100]


def test_normalize_single_target() -> None:
    result = normalize_curve_values([42, 99], 1)
    assert result == [42]


def test_normalize_zero_target() -> None:
    assert normalize_curve_values([10, 20], 0) == []


def test_normalize_all_zeros() -> None:
    assert normalize_curve_values([0, 0, 0, 0], 4) == [0, 0, 0, 0]


def test_normalize_all_hundred() -> None:
    assert normalize_curve_values([100, 100, 100, 100], 4) == [100, 100, 100, 100]


def test_normalize_single_value_to_many() -> None:
    result = normalize_curve_values([50], 5)
    assert all(v == 50 for v in result)


# ─── make_non_decreasing_curve ────────────────────────────────────────────────

def test_non_decreasing_already_monotonic() -> None:
    values = [10, 20, 30, 40, 50]
    assert make_non_decreasing_curve(values) == values


def test_non_decreasing_fixes_dips() -> None:
    assert make_non_decreasing_curve([50, 30, 40, 20, 60]) == [50, 50, 50, 50, 60]


def test_non_decreasing_empty() -> None:
    assert make_non_decreasing_curve([]) == []


def test_non_decreasing_single() -> None:
    assert make_non_decreasing_curve([42]) == [42]


def test_non_decreasing_all_same() -> None:
    assert make_non_decreasing_curve([50, 50, 50]) == [50, 50, 50]


def test_non_decreasing_clamps_over_100() -> None:
    result = make_non_decreasing_curve([50, 200, 30])
    assert result == [50, 100, 100]


def test_non_decreasing_clamps_negative() -> None:
    result = make_non_decreasing_curve([-10, 20, 30])
    assert result == [0, 20, 30]


# ─── unique_lines ─────────────────────────────────────────────────────────────

def test_unique_lines_deduplicates() -> None:
    assert unique_lines(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_unique_lines_strips_whitespace() -> None:
    assert unique_lines(["  hello  ", "hello", "  hello  "]) == ["hello"]


def test_unique_lines_skips_empty() -> None:
    assert unique_lines(["a", "", "  ", "b"]) == ["a", "b"]


def test_unique_lines_empty_input() -> None:
    assert unique_lines([]) == []
