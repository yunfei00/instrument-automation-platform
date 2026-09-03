"""Explicit FSW amplitude/trigger operations used by the dedicated GUI.

Reference Level is intentionally kept out of automatic state refresh because its
catalog entry is still candidate.  The explicit read/set operations exist so it
can be qualified on real hardware without silently expanding the baseline.
Trigger operations only use commands that are already manual_verified in the FSW
trigger catalog.
"""

from __future__ import annotations

from typing import Mapping

from .models import SafetyLevel
from .operations import (
    DEFAULT_OPERATION_REGISTRY,
    InstrumentOperation,
    OperationParameter,
)


_PROFILE_KEYS = ("rohde_schwarz/fsw",)
_READ_REFERENCE_LEVEL_ID = "rohde_schwarz.fsw.read_reference_level"
_SET_REFERENCE_LEVEL_ID = "rohde_schwarz.fsw.set_reference_level"
_SET_TRIGGER_SOURCE_ID = "rohde_schwarz.fsw.set_trigger_source"
_CONFIGURE_VIDEO_TRIGGER_ID = "rohde_schwarz.fsw.configure_video_trigger"


def _driver(transport: object):
    from instrument_drivers.rohde_schwarz.fsw import RohdeSchwarzFSWDriver

    return RohdeSchwarzFSWDriver(transport)


def _required_float(
    parameters: Mapping[str, object],
    name: str,
    label: str,
) -> float:
    raw = parameters.get(name)
    if raw is None or not str(raw).strip():
        raise ValueError(f"{label} is required")
    return float(raw)


def _run_read_reference_level(
    transport: object,
    _parameters: Mapping[str, object],
) -> object:
    driver = _driver(transport)
    return {
        "kind": "rohde_schwarz_fsw_reference_level",
        "reference_level_dbm": driver.get_reference_level_dbm(),
        "verification_status": "candidate",
    }


def _run_set_reference_level(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    value_dbm = _required_float(parameters, "reference_level_dbm", "Reference Level")
    driver = _driver(transport)
    driver.set_reference_level_dbm(value_dbm)
    readback_dbm = driver.get_reference_level_dbm()
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "reference_level",
        "applied": {"reference_level_dbm": value_dbm},
        "readback_dbm": readback_dbm,
        "verification_status": "candidate",
    }


def _run_set_trigger_source(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    source = str(parameters.get("source", "IMMediate")).strip().upper()
    aliases = {
        "IMM": "IMMediate",
        "IMMEDIATE": "IMMediate",
        "VID": "VIDeo",
        "VIDEO": "VIDeo",
    }
    try:
        normalized = aliases[source]
    except KeyError as exc:
        raise ValueError("This baseline UI currently supports IMMediate or VIDeo") from exc

    driver = _driver(transport)
    driver.set_trigger_source(normalized)
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "trigger_source",
        "applied": {"source": normalized},
    }


def _run_configure_video_trigger(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    from instrument_drivers.rohde_schwarz.fsw import configure_video_trigger

    level_pct = _required_float(parameters, "level_pct", "VIDEO Trigger Level")
    offset_s = _required_float(parameters, "offset_s", "Trigger Offset")
    slope = str(parameters.get("slope", "POSitive")).strip()

    driver = _driver(transport)
    readback = configure_video_trigger(
        driver,
        level_pct=level_pct,
        offset_s=offset_s,
        slope=slope,
    )
    return {
        "kind": "rohde_schwarz_fsw_video_trigger",
        "setting": "video_trigger",
        **readback,
    }


def ensure_fsw_reference_trigger_operations_registered() -> None:
    """Register explicit FSW Reference Level and trigger qualification actions."""

    definitions = (
        InstrumentOperation(
            id=_READ_REFERENCE_LEVEL_ID,
            title="读取 FSW Reference Level（待验证）",
            description=(
                "显式读取 Reference Level。该命令当前仍为 candidate，因此不会加入"
                "自动状态刷新；本操作用于真实硬件资格验证。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(),
            runner=_run_read_reference_level,
        ),
        InstrumentOperation(
            id=_SET_REFERENCE_LEVEL_ID,
            title="设置 FSW Reference Level（待验证）",
            description=(
                "显式设置并读回 Reference Level。真实硬件验证通过前保持 candidate。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    "reference_level_dbm",
                    "Reference Level (dBm)",
                    "float",
                ),
            ),
            runner=_run_set_reference_level,
        ),
        InstrumentOperation(
            id=_SET_TRIGGER_SOURCE_ID,
            title="设置 FSW Trigger Source",
            description="当前专用界面只开放 IMMediate 与 VIDeo 两个已进入基线的常用路径。",
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(
                OperationParameter(
                    "source",
                    "Trigger Source",
                    "choice",
                    "IMMediate",
                    ("IMMediate", "VIDeo"),
                ),
            ),
            runner=_run_set_trigger_source,
        ),
        InstrumentOperation(
            id=_CONFIGURE_VIDEO_TRIGGER_ID,
            title="配置 FSW VIDEO Trigger",
            description=(
                "切换到 VIDeo Trigger，并设置 Level、Trigger Offset 与 Slope；"
                "完成后读取关键值确认。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(
                OperationParameter("level_pct", "VIDEO Level (%)", "float", 50.0),
                OperationParameter("offset_s", "Trigger Offset (s)", "float", 0.0),
                OperationParameter(
                    "slope",
                    "Slope",
                    "choice",
                    "POSitive",
                    ("POSitive", "NEGative"),
                ),
            ),
            runner=_run_configure_video_trigger,
        ),
    )

    for operation in definitions:
        try:
            DEFAULT_OPERATION_REGISTRY.get(operation.id)
        except KeyError:
            DEFAULT_OPERATION_REGISTRY.register(operation)
