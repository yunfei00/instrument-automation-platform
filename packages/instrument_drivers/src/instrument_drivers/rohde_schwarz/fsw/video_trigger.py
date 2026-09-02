"""Reusable R&S FSW video-trigger primitives.

The baseline deliberately exposes instrument semantics only. Product policy such
as choosing ``trigger_offset = -sweep_time / 2`` belongs to the application
workflow and is not hard-coded here.
"""

from __future__ import annotations

from typing import Any


def get_video_trigger_level_pct(driver: Any) -> float:
    """Return the VIDEO trigger level as percent of diagram height."""

    return float(driver.query("TRIGger:SEQuence:LEVel:VIDeo?"))


def set_video_trigger_level_pct(driver: Any, level_pct: float) -> None:
    """Set the VIDEO trigger level in percent (0..100)."""

    value = float(level_pct)
    if not 0.0 <= value <= 100.0:
        raise ValueError("FSW video trigger level must be between 0 and 100 percent")

    driver.write(f"TRIGger:SEQuence:LEVel:VIDeo {value:g} PCT")


def get_trigger_offset_s(driver: Any) -> float:
    """Return Trigger Offset in seconds.

    R&S exposes Trigger Offset through ``TRIGger:SEQuence:HOLDoff:TIME``. A
    negative value is a pre-trigger offset and is therefore intentionally valid.
    """

    return float(driver.query("TRIGger:SEQuence:HOLDoff:TIME?"))


def set_trigger_offset_s(driver: Any, offset_s: float) -> None:
    """Set Trigger Offset in seconds; negative pre-trigger values are allowed."""

    driver.write(f"TRIGger:SEQuence:HOLDoff:TIME {float(offset_s):g} S")


def get_trigger_slope(driver: Any) -> str:
    """Return the configured trigger slope."""

    return str(driver.query("TRIGger:SEQuence:SLOPe?")).strip()


def set_trigger_slope(driver: Any, slope: str) -> None:
    """Set POSitive or NEGative trigger slope."""

    normalized = str(slope).strip().upper()
    aliases = {
        "POS": "POSitive",
        "POSITIVE": "POSitive",
        "NEG": "NEGative",
        "NEGATIVE": "NEGative",
    }
    try:
        value = aliases[normalized]
    except KeyError as exc:
        raise ValueError("FSW trigger slope must be POSitive or NEGative") from exc

    driver.write(f"TRIGger:SEQuence:SLOPe {value}")


def configure_video_trigger(
    driver: Any,
    *,
    level_pct: float,
    offset_s: float,
    slope: str | None = None,
) -> dict[str, object]:
    """Configure VIDEO trigger and return readback values.

    This helper does not start a measurement. Call the driver's existing
    one-shot/trace-arm primitive afterwards so trigger setup and acquisition
    lifecycle remain independently reusable.
    """

    driver.set_trigger_source("VID")
    set_video_trigger_level_pct(driver, level_pct)
    set_trigger_offset_s(driver, offset_s)
    if slope is not None:
        set_trigger_slope(driver, slope)

    return {
        "source": str(driver.get_trigger_source()).strip(),
        "video_level_pct": get_video_trigger_level_pct(driver),
        "trigger_offset_s": get_trigger_offset_s(driver),
        "slope": get_trigger_slope(driver),
    }
