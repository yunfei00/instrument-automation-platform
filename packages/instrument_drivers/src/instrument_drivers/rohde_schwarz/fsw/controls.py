"""Reusable high-level FSW control helpers kept inside the driver package.

These helpers centralize manually verified SCPI so GUI/Operation layers never
need to duplicate command strings. They complement the core driver without
forcing every family-specific convenience action into the base class.
"""

from __future__ import annotations

from .driver import RohdeSchwarzFSWDriver


def set_sweep_time_s(driver: RohdeSchwarzFSWDriver, value_s: float) -> float:
    """Set FSW sweep time in seconds and return the requested value."""
    numeric = float(value_s)
    if numeric <= 0:
        raise ValueError("FSW sweep time must be greater than 0 seconds")
    driver.write(f"SENSe:SWEep:TIME {numeric:.12g}")
    return numeric


def marker_peak_search(
    driver: RohdeSchwarzFSWDriver,
    *,
    window: int = 1,
    marker: int = 1,
) -> float:
    """Move a marker to the trace maximum and return its Y result.

    Only the commands already marked manual_verified in the FSW marker catalog
    are used here: MAXimum:PEAK and MARKer:Y?. Marker state/X remain candidate
    and are deliberately not introduced into the automatic control path yet.
    """
    if window <= 0 or marker <= 0:
        raise ValueError("FSW window and marker indexes must be positive")
    driver.write(f"CALCulate{window}:MARKer{marker}:MAXimum:PEAK")
    return float(driver.query(f"CALCulate{window}:MARKer{marker}:Y?"))
