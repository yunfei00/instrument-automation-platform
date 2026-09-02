"""Reusable DSO-X 3000 front-panel control helpers.

These helpers live in the driver package so desktop, CLI, tests and future
product applications can reuse the same validated SCPI mapping. Qt widgets must
not duplicate these command strings.
"""

from __future__ import annotations

import math


def _validate_channel(channel: int) -> None:
    if channel not in {1, 2, 3, 4}:
        raise ValueError("DSO-X 3034A analog channel must be 1, 2, 3 or 4")


def normalize_edge_trigger_source(source: str | int) -> str:
    """Normalize a supported analog edge-trigger source to SCPI CHANnel<n>."""

    text = str(source).strip().upper().replace(" ", "")
    aliases = {
        "1": 1,
        "CH1": 1,
        "CHAN1": 1,
        "CHANNEL1": 1,
        "2": 2,
        "CH2": 2,
        "CHAN2": 2,
        "CHANNEL2": 2,
        "3": 3,
        "CH3": 3,
        "CHAN3": 3,
        "CHANNEL3": 3,
        "4": 4,
        "CH4": 4,
        "CHAN4": 4,
        "CHANNEL4": 4,
    }
    channel = aliases.get(text)
    if channel is None:
        raise ValueError("DSO-X edge trigger source must be CH1, CH2, CH3 or CH4")
    return f"CHANnel{channel}"


def set_channel_display(driver: object, channel: int, enabled: bool) -> None:
    """Enable or disable one analog channel display."""

    _validate_channel(channel)
    write = getattr(driver, "write", None)
    if not callable(write):
        raise TypeError("DSO-X channel display control requires driver.write()")
    write(f":CHANnel{channel}:DISPlay {'ON' if enabled else 'OFF'}")


def set_edge_trigger(
    driver: object,
    *,
    sweep: str,
    source: str | int,
    level_v: float | None = None,
) -> dict[str, object]:
    """Apply the common edge-trigger controls exposed by the virtual panel.

    The trigger type itself is not changed here. The panel reads the current
    trigger mode and exposes these settings as Edge Trigger controls. This avoids
    silently replacing another trigger type just because the user edits the
    stored Edge Trigger parameters.
    """

    normalized_sweep = str(sweep).strip().upper()
    if normalized_sweep not in {"AUTO", "NORM"}:
        raise ValueError("DSO-X trigger sweep must be AUTO or NORM")

    normalized_source = normalize_edge_trigger_source(source)
    set_sweep = getattr(driver, "set_trigger_sweep", None)
    write = getattr(driver, "write", None)
    if not callable(set_sweep) or not callable(write):
        raise TypeError("DSO-X edge trigger control requires driver trigger/write APIs")

    set_sweep(normalized_sweep)
    write(f":TRIGger:EDGE:SOURce {normalized_source}")

    applied: dict[str, object] = {
        "sweep": normalized_sweep,
        "source": normalized_source,
    }
    if level_v is not None:
        level = float(level_v)
        if not math.isfinite(level):
            raise ValueError("DSO-X trigger level must be a finite voltage")
        write(f":TRIGger:EDGE:LEVel {level},{normalized_source}")
        applied["level_v"] = level

    return applied
