"""DSO-X waveform operation registered by the Qt control-panel module.

This module intentionally has no Qt dependency. It bridges the existing
front-panel-equivalent Single capture helper into Instrument Lab's operation
registry without duplicating the low-level acquisition sequence in the GUI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .models import SafetyLevel
from .operations import (
    DEFAULT_OPERATION_REGISTRY,
    InstrumentOperation,
    OperationParameter,
)


_OPERATION_ID = "keysight.dsox3000.single_waveform"


@dataclass(frozen=True, slots=True)
class WaveformDataPayload:
    """Full waveform arrays with compact text representation for Raw JSON."""

    time_seconds: tuple[float, ...]
    voltage_volts: tuple[float, ...]

    def __str__(self) -> str:
        return f"<WaveformDataPayload {len(self.time_seconds)} points>"

    __repr__ = __str__


def _run_single_waveform(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    from instrument_drivers.keysight.dsox3000 import (
        KeysightDSOX3000Driver,
        acquire_single_word_waveform,
    )

    channel = int(parameters.get("channel", 1))
    timeout_s = float(parameters.get("timeout_s", 30.0))
    if timeout_s <= 0:
        raise ValueError("Single waveform timeout must be greater than 0 seconds")

    driver = KeysightDSOX3000Driver(transport)
    waveform = acquire_single_word_waveform(
        driver,
        channel,
        timeout_s=timeout_s,
    )

    voltages = waveform.voltage_volts
    times = waveform.time_seconds
    point_count = len(voltages)

    return {
        "kind": "keysight_dsox3000_single_waveform",
        "source": f"CHANnel{channel}",
        "channel": channel,
        "point_count": point_count,
        "data": WaveformDataPayload(times, voltages),
        "time_start_s": times[0] if times else None,
        "time_stop_s": times[-1] if times else None,
        "voltage_min_v": min(voltages) if voltages else None,
        "voltage_max_v": max(voltages) if voltages else None,
        "preamble": asdict(waveform.preamble),
    }


def ensure_dsox_waveform_operation_registered() -> None:
    """Register the operation once and keep module import idempotent."""

    try:
        DEFAULT_OPERATION_REGISTRY.get(_OPERATION_ID)
    except KeyError:
        DEFAULT_OPERATION_REGISTRY.register(
            InstrumentOperation(
                id=_OPERATION_ID,
                title="Single Waveform Data",
                description=(
                    "执行前面板等效 Single acquisition，等待本次采集完成后读取 "
                    "WORD waveform，并返回时间轴与电压数组供 Data View 使用。"
                ),
                profile_keys=("keysight/dsox3000",),
                safety=SafetyLevel.DISRUPTIVE,
                parameters=(
                    OperationParameter(
                        name="channel",
                        label="Channel",
                        kind="choice",
                        default="1",
                        choices=("1", "2", "3", "4"),
                    ),
                    OperationParameter(
                        name="timeout_s",
                        label="Trigger Timeout (s)",
                        kind="float",
                        default=30.0,
                        description=(
                            "One deadline covers arming and acquisition completion."
                        ),
                    ),
                ),
                runner=_run_single_waveform,
            )
        )
