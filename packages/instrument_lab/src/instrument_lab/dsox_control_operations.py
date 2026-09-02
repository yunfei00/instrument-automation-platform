"""DSO-X quick-control operations for the virtual front panel.

This module has no Qt dependency. It connects reusable driver-family control
helpers to Instrument Lab's Operation Registry so desktop and future front ends
share one control path.
"""

from __future__ import annotations

from typing import Mapping

from .models import SafetyLevel
from .operations import (
    DEFAULT_OPERATION_REGISTRY,
    InstrumentOperation,
    OperationParameter,
)


_CHANNEL_DISPLAY_ID = "keysight.dsox3000.set_channel_display"
_EDGE_TRIGGER_ID = "keysight.dsox3000.set_edge_trigger"


def _driver(transport: object):
    from instrument_drivers.keysight.dsox3000 import KeysightDSOX3000Driver

    return KeysightDSOX3000Driver(transport)


def _run_set_channel_display(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    from instrument_drivers.keysight.dsox3000 import set_channel_display

    channel = int(parameters.get("channel", 1))
    state = str(parameters.get("state", "ON")).strip().upper()
    if state not in {"ON", "OFF"}:
        raise ValueError("Channel Display state must be ON or OFF")

    set_channel_display(_driver(transport), channel, state == "ON")
    return {
        "kind": "keysight_dsox3000_setting_applied",
        "setting": "channel_display",
        "applied": {"channel": channel, "state": state},
    }


def _run_set_edge_trigger(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    from instrument_drivers.keysight.dsox3000 import set_edge_trigger

    level_raw = parameters.get("level_v")
    level_v: float | None
    if level_raw is None or str(level_raw).strip() == "":
        level_v = None
    else:
        level_v = float(level_raw)

    applied = set_edge_trigger(
        _driver(transport),
        sweep=str(parameters.get("sweep", "AUTO")),
        source=str(parameters.get("source", "CH1")),
        level_v=level_v,
    )
    return {
        "kind": "keysight_dsox3000_setting_applied",
        "setting": "edge_trigger",
        "applied": applied,
    }


def ensure_dsox_control_operations_registered() -> None:
    """Register DSO-X quick-control operations once."""

    try:
        DEFAULT_OPERATION_REGISTRY.get(_CHANNEL_DISPLAY_ID)
    except KeyError:
        DEFAULT_OPERATION_REGISTRY.register(
            InstrumentOperation(
                id=_CHANNEL_DISPLAY_ID,
                title="Channel Display",
                description="打开或关闭 DSO-X 3034A 指定模拟通道显示。",
                profile_keys=("keysight/dsox3000",),
                safety=SafetyLevel.SAFE,
                parameters=(
                    OperationParameter(
                        name="channel",
                        label="Channel",
                        kind="choice",
                        default="1",
                        choices=("1", "2", "3", "4"),
                    ),
                    OperationParameter(
                        name="state",
                        label="Display",
                        kind="choice",
                        default="ON",
                        choices=("ON", "OFF"),
                    ),
                ),
                runner=_run_set_channel_display,
            )
        )

    try:
        DEFAULT_OPERATION_REGISTRY.get(_EDGE_TRIGGER_ID)
    except KeyError:
        DEFAULT_OPERATION_REGISTRY.register(
            InstrumentOperation(
                id=_EDGE_TRIGGER_ID,
                title="Edge Trigger",
                description=(
                    "设置常用 Edge Trigger Sweep、模拟通道 Source 和可选 Level。"
                    "不会自动改变当前 Trigger Mode。"
                ),
                profile_keys=("keysight/dsox3000",),
                safety=SafetyLevel.SAFE,
                parameters=(
                    OperationParameter(
                        name="sweep",
                        label="Sweep",
                        kind="choice",
                        default="AUTO",
                        choices=("AUTO", "NORM"),
                    ),
                    OperationParameter(
                        name="source",
                        label="Source",
                        kind="choice",
                        default="CH1",
                        choices=("CH1", "CH2", "CH3", "CH4"),
                    ),
                    OperationParameter(
                        name="level_v",
                        label="Level (V)",
                        kind="float",
                        description="可留空；留空时保持当前 Edge Trigger Level。",
                    ),
                ),
                runner=_run_set_edge_trigger,
            )
        )
