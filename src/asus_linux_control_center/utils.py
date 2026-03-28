from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def normalize_curve_values(values: Sequence[int], target_len: int) -> list[int]:
    if target_len <= 0:
        return []
    if not values:
        return [0] * target_len
    if len(values) == target_len:
        return [clamp(v, 0, 100) for v in values]
    if target_len == 1:
        return [clamp(values[0], 0, 100)]

    source = [clamp(v, 0, 100) for v in values]
    result: list[int] = []
    for index in range(target_len):
        position = index * (len(source) - 1) / (target_len - 1)
        lower = int(position)
        upper = min(lower + 1, len(source) - 1)
        fraction = position - lower
        value = round(source[lower] * (1 - fraction) + source[upper] * fraction)
        result.append(clamp(value, 0, 100))
    return result


def make_non_decreasing_curve(values: Sequence[int]) -> list[int]:
    fixed: list[int] = []
    current = 0
    for value in values:
        current = max(current, clamp(value, 0, 100))
        fixed.append(current)
    return fixed


def unique_lines(lines: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for line in lines:
        clean = line.strip()
        if clean and clean not in seen:
            seen.add(clean)
            ordered.append(clean)
    return ordered


def read_os_release() -> tuple[str, str]:
    path = Path("/etc/os-release")
    if not path.exists():
        return "Unknown", "unknown"

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values.get("PRETTY_NAME", "Unknown"), values.get("ID", "unknown").lower()
