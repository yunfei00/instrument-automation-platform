"""Engineering-unit conversion helpers shared by instrument control surfaces.

Keep unit math Qt-free so Driver/Operation tests can validate the same conversions
used by desktop widgets. Base values remain SI (Hz, s, V, ...); the UI may present
more readable engineering units such as MHz or ms.
"""

from __future__ import annotations

from collections.abc import Mapping


FREQUENCY_UNITS: dict[str, float] = {
    "Hz": 1.0,
    "kHz": 1e3,
    "MHz": 1e6,
    "GHz": 1e9,
}

TIME_UNITS: dict[str, float] = {
    "s": 1.0,
    "ms": 1e-3,
    "us": 1e-6,
    "ns": 1e-9,
}


def to_base(value: float, unit: str, units: Mapping[str, float]) -> float:
    """Convert one displayed engineering-unit value to the SI/base value."""
    try:
        scale = float(units[unit])
    except KeyError as exc:
        raise ValueError(f"Unknown unit: {unit}") from exc
    return float(value) * scale


def from_base(value: float, unit: str, units: Mapping[str, float]) -> float:
    """Convert one SI/base value to a displayed engineering-unit value."""
    try:
        scale = float(units[unit])
    except KeyError as exc:
        raise ValueError(f"Unknown unit: {unit}") from exc
    if scale == 0:
        raise ValueError(f"Unit scale must not be zero: {unit}")
    return float(value) / scale


def best_unit(
    value: float,
    units: Mapping[str, float],
    *,
    zero_unit: str | None = None,
) -> str:
    """Choose a readable engineering unit for a base/SI value.

    The largest unit whose scale is not greater than the magnitude is preferred.
    For zero, callers may supply a context-friendly ``zero_unit`` (for example
    MHz for FSW Span=0) because magnitude alone cannot select a useful unit.
    """
    numeric = float(value)
    if numeric == 0.0 and zero_unit is not None:
        if zero_unit not in units:
            raise ValueError(f"Unknown zero unit: {zero_unit}")
        return zero_unit

    magnitude = abs(numeric)
    ordered = sorted(units.items(), key=lambda item: item[1])
    selected = ordered[0][0]
    for unit, scale in ordered:
        if magnitude >= float(scale):
            selected = unit
    return selected
