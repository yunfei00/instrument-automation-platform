"""DSO-X waveform operation registered by the Qt control-panel module.

This module intentionally has no Qt dependency. It bridges the existing
front-panel-equivalent Single capture helper into Instrument Lab's operation
registry without duplicating the low-level acquisition sequence in the GUI.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Mapping

from .models import SafetyLevel
from .operations import (
    DEFAULT_OPERATION_REGISTRY,
    InstrumentOperation,
    OperationParameter,
)


_OPERATION_ID = "keysight.dsox3000.single_waveform"


class WaveformOperationResult(dict[str, object]):
    """Dict-compatible metadata plus private full-resolution waveform arrays.

    The GUI panel expects normal ``dict.get()`` access to ``time_seconds`` and
    ``voltage_volts``. Instrument Lab's Raw JSON sanitizer iterates ``items()``;
    keeping the large arrays outside the actual mapping prevents a 10k/1M-point
    waveform from being expanded into the diagnostic text widget.
    """

    def __init__(
        self,
        metadata: Mapping[str, object],
        time_seconds: tuple[float, ...],
        voltage_volts: tuple[float, ...],
    ) -> None:
        super().__init__(metadata)
        self._time_seconds = time_seconds
        self._voltage_volts = voltage_volts

    def get(self, key: str, default: object = None) -> object:
        if key == "time_seconds":
            return self._time_seconds
        if key == "voltage_volts":
            return self._voltage_volts
        return super().get(key, default)

    def __getitem__(self, key: str) -> object:
        if key == "time_seconds":
            return self._time_seconds
        if key == "voltage_volts":
            return self._voltage_volts
        return super().__getitem__(key)


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
    metadata = {
        "kind": "keysight_dsox3000_single_waveform",
        "source": f"CHANnel{channel}",
        "channel": channel,
        "point_count": point_count,
        "waveform_data": f"<{point_count} time/voltage points>",
        "time_start_s": times[0] if times else None,
        "time_stop_s": times[-1] if times else None,
        "voltage_min_v": min(voltages) if voltages else None,
        "voltage_max_v": max(voltages) if voltages else None,
        "preamble": asdict(waveform.preamble),
    }
    return WaveformOperationResult(metadata, times, voltages)


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
