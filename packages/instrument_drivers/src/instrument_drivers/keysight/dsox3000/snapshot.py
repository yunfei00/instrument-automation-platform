"""Snapshot All support for Keysight InfiniiVision 3000 X-Series scopes.

The Programmer's Guide documents ``:MEASure:ALL`` as the front-panel-equivalent
Snapshot All command. This module keeps the reusable instrument-family logic in
the baseline repository so product applications do not need to duplicate SCPI
knowledge.

Hardware qualification target: DSO-X 3034A. The command set is manual-backed;
full Snapshot All execution remains hardware-pending until a real-device run is
recorded in the qualification directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Callable, Protocol


CancelCheck = Callable[[], bool]


class SnapshotDriver(Protocol):
    def write(self, command: str) -> None: ...
    def query(self, command: str) -> str: ...


@dataclass(frozen=True)
class SnapshotMeasurementSpec:
    key: str
    label: str
    query_template: str
    unit: str


SNAPSHOT_ALL_MEASUREMENTS: tuple[SnapshotMeasurementSpec, ...] = (
    SnapshotMeasurementSpec("peak_to_peak", "Pk-Pk", ":MEASure:VPP? {source}", "V"),
    SnapshotMeasurementSpec("maximum", "Max", ":MEASure:VMAX? {source}", "V"),
    SnapshotMeasurementSpec("minimum", "Min", ":MEASure:VMIN? {source}", "V"),
    SnapshotMeasurementSpec("amplitude", "Ampl", ":MEASure:VAMPlitude? {source}", "V"),
    SnapshotMeasurementSpec("top", "Top", ":MEASure:VTOP? {source}", "V"),
    SnapshotMeasurementSpec("base", "Base", ":MEASure:VBASe? {source}", "V"),
    SnapshotMeasurementSpec("overshoot", "Over", ":MEASure:OVERshoot? {source}", "%"),
    SnapshotMeasurementSpec("preshoot", "Pre", ":MEASure:PREShoot? {source}", "%"),
    SnapshotMeasurementSpec("average_cycle", "Avg - Cyc", ":MEASure:VAVerage? CYCLe,{source}", "V"),
    SnapshotMeasurementSpec("average_display", "Avg - FS", ":MEASure:VAVerage? DISPlay,{source}", "V"),
    SnapshotMeasurementSpec("dc_rms_cycle", "DC RMS - Cyc", ":MEASure:VRMS? CYCLe,DC,{source}", "V"),
    SnapshotMeasurementSpec("dc_rms_display", "DC RMS - FS", ":MEASure:VRMS? DISPlay,DC,{source}", "V"),
    SnapshotMeasurementSpec("ac_rms_cycle", "AC RMS - Cyc", ":MEASure:VRMS? CYCLe,AC,{source}", "V"),
    SnapshotMeasurementSpec("ac_rms_display", "AC RMS - FS", ":MEASure:VRMS? DISPlay,AC,{source}", "V"),
    SnapshotMeasurementSpec("period", "Period", ":MEASure:PERiod? {source}", "s"),
    SnapshotMeasurementSpec("frequency", "Freq", ":MEASure:FREQuency? {source}", "Hz"),
    SnapshotMeasurementSpec("positive_width", "+Width", ":MEASure:PWIDth? {source}", "s"),
    SnapshotMeasurementSpec("negative_width", "-Width", ":MEASure:NWIDth? {source}", "s"),
    SnapshotMeasurementSpec("burst_width", "Burst Width", ":MEASure:BWIDth? {source}", "s"),
    SnapshotMeasurementSpec("positive_duty", "+Duty", ":MEASure:DUTYcycle? {source}", "%"),
    SnapshotMeasurementSpec("negative_duty", "-Duty", ":MEASure:NDUTy? {source}", "%"),
    SnapshotMeasurementSpec("rise_time", "Rise", ":MEASure:RISetime? {source}", "s"),
    SnapshotMeasurementSpec("fall_time", "Fall", ":MEASure:FALLtime? {source}", "s"),
    SnapshotMeasurementSpec("x_at_min", "X@Min", ":MEASure:XMIN? {source}", "s"),
    SnapshotMeasurementSpec("x_at_max", "X@Max", ":MEASure:XMAX? {source}", "s"),
    SnapshotMeasurementSpec("positive_pulse_count", "+ Pulse Count", ":MEASure:PPULses? {source}", "count"),
    SnapshotMeasurementSpec("negative_pulse_count", "- Pulse Count", ":MEASure:NPULses? {source}", "count"),
    SnapshotMeasurementSpec("rising_edge_count", "Rise Edge", ":MEASure:PEDGes? {source}", "count"),
    SnapshotMeasurementSpec("falling_edge_count", "Fall Edge", ":MEASure:NEDGes? {source}", "count"),
    SnapshotMeasurementSpec("area_cycle", "Area - Cyc", ":MEASure:AREa? CYCLe,{source}", "V*s"),
    SnapshotMeasurementSpec("area_display", "Area - FS", ":MEASure:AREa? DISPlay,{source}", "V*s"),
)


def read_snapshot_all(
    driver: SnapshotDriver,
    channel: int,
    *,
    cancel_check: CancelCheck | None = None,
    install_snapshot: bool = True,
) -> dict[str, object]:
    """Read the 31-value Snapshot All set for one analog channel.

    Invalid scope measurements (normally represented by a value around 9.9E+37)
    are preserved in ``raw`` while exposed as ``value=None`` and ``valid=False``.
    Signal-dependent query failures are recorded per measurement. A transport
    failure stops the remaining queries so one broken session does not cause a
    long sequence of timeouts.
    """

    channel_number = int(channel)
    if channel_number not in {1, 2, 3, 4}:
        raise ValueError("DSO-X Snapshot All channel must be 1, 2, 3 or 4")

    source = f"CHANnel{channel_number}"
    snapshot: dict[str, object] = {
        "schema_version": 1,
        "kind": "keysight_infiniivision_snapshot_all",
        "source": source,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "install_command": ":MEASure:ALL" if install_snapshot else None,
        "measurement_count": len(SNAPSHOT_ALL_MEASUREMENTS),
        "measurements": {},
    }

    if install_snapshot:
        try:
            driver.write(f":MEASure:SOURce {source}")
            driver.write(":MEASure:ALL")
        except Exception as exc:
            snapshot["install_error"] = _error_record(exc)
            if _is_transport_failure(exc):
                snapshot.update(
                    {
                        "collection_complete": False,
                        "stop_reason": "transport_error",
                        "successful_measurements": 0,
                        "failed_or_invalid_measurements": 0,
                        "unread_measurements": len(SNAPSHOT_ALL_MEASUREMENTS),
                    }
                )
                return snapshot

    results: dict[str, object] = {}
    successful = 0
    stop_reason: str | None = None

    for spec in SNAPSHOT_ALL_MEASUREMENTS:
        if cancel_check is not None and cancel_check():
            stop_reason = "canceled"
            break

        command = spec.query_template.format(source=source)
        entry: dict[str, object] = {
            "label": spec.label,
            "command": command,
            "unit": spec.unit,
        }
        try:
            raw = str(driver.query(command)).strip()
            value, valid = parse_snapshot_value(raw)
            entry.update({"raw": raw, "value": value, "valid": valid})
            if valid:
                successful += 1
        except Exception as exc:
            entry.update(
                {
                    "raw": None,
                    "value": None,
                    "valid": False,
                    "error": _error_record(exc),
                }
            )
            results[spec.key] = entry
            if _is_transport_failure(exc):
                stop_reason = "transport_error"
                break
            continue

        results[spec.key] = entry

    unread = len(SNAPSHOT_ALL_MEASUREMENTS) - len(results)
    snapshot["measurements"] = results
    snapshot["successful_measurements"] = successful
    snapshot["failed_or_invalid_measurements"] = len(results) - successful
    snapshot["unread_measurements"] = unread
    snapshot["collection_complete"] = stop_reason is None and unread == 0
    if stop_reason is not None:
        snapshot["stop_reason"] = stop_reason
    return snapshot


def parse_snapshot_value(raw: str) -> tuple[float | None, bool]:
    """Parse a scalar Snapshot value while preserving invalid sentinels."""

    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, False
    if not math.isfinite(value) or abs(value) >= 9.0e37:
        return None, False
    return value, True


def _error_record(exc: Exception) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def _is_transport_failure(exc: Exception) -> bool:
    names = {cls.__name__ for cls in type(exc).__mro__}
    return bool(
        names
        & {
            "InstrumentTimeoutError",
            "InstrumentConnectionError",
            "InstrumentCommunicationError",
            "OperationCanceledError",
            "VisaIOError",
        }
    )
