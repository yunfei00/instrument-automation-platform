"""Reusable instrument operation registry for Instrument Lab.

A command is one SCPI request. An operation is a higher-level instrument action
that can combine multiple writes, queries, parsing steps and validation into one
user-facing task, for example Snapshot All or a single spectrum trace capture.

This module intentionally has no Qt dependency. It can be imported in headless
CI and reused by future desktop, CLI or web front ends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .models import SafetyLevel


OperationRunner = Callable[[object, Mapping[str, object]], object]
BINARY_OPERATION_MIN_TIMEOUT_MS = 30000


@dataclass(frozen=True, slots=True)
class OperationParameter:
    """One user-editable parameter required by an instrument operation."""

    name: str
    label: str
    kind: str = "string"
    default: object | None = None
    choices: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True, slots=True)
class InstrumentOperation:
    """Metadata plus runner for one reusable instrument-level operation."""

    id: str
    title: str
    description: str
    profile_keys: tuple[str, ...]
    safety: SafetyLevel
    parameters: tuple[OperationParameter, ...]
    runner: OperationRunner

    def supports_profile(self, profile_key: str) -> bool:
        normalized = profile_key.strip("/")
        return any(
            normalized == prefix.strip("/")
            or normalized.startswith(prefix.strip("/") + "/")
            for prefix in self.profile_keys
        )


class InstrumentOperationRegistry:
    """Registry of higher-level operations exposed by Instrument Lab."""

    def __init__(self) -> None:
        self._operations: dict[str, InstrumentOperation] = {}

    def register(self, operation: InstrumentOperation) -> None:
        if operation.id in self._operations:
            raise ValueError(f"Duplicate instrument operation id: {operation.id}")
        self._operations[operation.id] = operation

    def get(self, operation_id: str) -> InstrumentOperation:
        try:
            return self._operations[operation_id]
        except KeyError as exc:
            raise KeyError(f"Unknown instrument operation: {operation_id}") from exc

    def list_for_profile(self, profile_key: str) -> tuple[InstrumentOperation, ...]:
        return tuple(
            operation
            for operation in self._operations.values()
            if operation.supports_profile(profile_key)
        )

    def run(
        self,
        operation_id: str,
        transport: object,
        parameters: Mapping[str, object] | None = None,
    ) -> object:
        operation = self.get(operation_id)
        return operation.runner(transport, parameters or {})


def _dsox_driver(transport: object):
    from instrument_drivers.keysight.dsox3000 import KeysightDSOX3000Driver

    return KeysightDSOX3000Driver(transport)


def _query_ieee_block_bytes(
    transport: object,
    command: str,
) -> bytes:
    """Run a bounded IEEE 488.2 binary query on a transport that supports it."""

    query = getattr(transport, "query_ieee_block_bytes", None)
    if not callable(query):
        raise TypeError(
            "This instrument operation requires a transport with "
            "query_ieee_block_bytes() support"
        )

    config = getattr(transport, "config", None)
    previous_timeout_ms = getattr(config, "timeout_ms", None)
    set_timeout = getattr(transport, "set_timeout_ms", None)
    changed_timeout = (
        isinstance(previous_timeout_ms, int)
        and previous_timeout_ms < BINARY_OPERATION_MIN_TIMEOUT_MS
        and callable(set_timeout)
    )

    if changed_timeout:
        set_timeout(BINARY_OPERATION_MIN_TIMEOUT_MS)

    try:
        return bytes(query(command, expect_termination=False))
    finally:
        if changed_timeout:
            try:
                set_timeout(previous_timeout_ms)
            except Exception:
                pass


def _run_dsox_snapshot_all(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    """Run the DSO-X Snapshot All helper on an already-open transport."""

    from instrument_drivers.keysight.dsox3000 import read_snapshot_all

    channel = int(parameters.get("channel", 1))
    driver = _dsox_driver(transport)
    return read_snapshot_all(driver, channel=channel)


def _run_dsox_screenshot(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    """Capture the physical DSO-X screen as image-file bytes.

    The Programmer's Guide documents :DISPlay:DATA? as an IEEE 488.2 binary
    block. INKSaver is temporarily disabled so the returned colors match the
    physical screen, then restored after a successful transfer.
    """

    from instrument_core.errors import InstrumentTimeoutError

    format_key = str(parameters.get("format", "PNG")).strip().upper()
    palette_key = str(parameters.get("palette", "COLOR")).strip().upper()

    formats = {
        "PNG": ("PNG", "image/png"),
        "BMP": ("BMP", "image/bmp"),
        "BMP8BIT": ("BMP8bit", "image/bmp"),
    }
    palettes = {
        "COLOR": "COLor",
        "COLOUR": "COLor",
        "GRAYSCALE": "GRAYscale",
        "GREYSCALE": "GRAYscale",
        "GRAY": "GRAYscale",
        "GREY": "GRAYscale",
    }

    try:
        format_scpi, mime_type = formats[format_key]
    except KeyError as exc:
        raise ValueError("Screenshot format must be PNG, BMP or BMP8bit") from exc
    try:
        palette_scpi = palettes[palette_key]
    except KeyError as exc:
        raise ValueError("Screenshot palette must be COLor or GRAYscale") from exc

    # Check binary-query support before changing any instrument state.
    if not callable(getattr(transport, "query_ieee_block_bytes", None)):
        raise TypeError(
            "Screenshot capture requires query_ieee_block_bytes() transport support"
        )

    driver = _dsox_driver(transport)
    original_inksaver = driver.query(":HARDcopy:INKSaver?").strip()
    original_inksaver_on = original_inksaver.upper() in {"1", "ON", "TRUE"}

    if original_inksaver_on:
        driver.write(":HARDcopy:INKSaver OFF")

    command = f":DISPlay:DATA? {format_scpi},{palette_scpi}"

    try:
        payload = _query_ieee_block_bytes(transport, command)
    except InstrumentTimeoutError:
        # Do not send more SCPI after a binary timeout. The owning I/O worker
        # will invalidate the VISA session before any later operation.
        raise
    except Exception:
        if original_inksaver_on:
            try:
                driver.write(":HARDcopy:INKSaver ON")
            except Exception:
                pass
        raise

    restore_error: str | None = None
    if original_inksaver_on:
        try:
            driver.write(":HARDcopy:INKSaver ON")
        except Exception as exc:
            restore_error = str(exc)

    return {
        "kind": "instrument_screenshot",
        "instrument_family": "keysight_dsox3000",
        "format": format_scpi,
        "palette": palette_scpi,
        "mime_type": mime_type,
        "byte_count": len(payload),
        "data": payload,
        "inksaver_original": original_inksaver,
        "inksaver_restore_error": restore_error,
    }


def _run_dsox_read_control_state(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    """Read the main settings needed by the first DSO-X control panel."""

    channel = int(parameters.get("channel", 1))
    driver = _dsox_driver(transport)

    return {
        "kind": "keysight_dsox3000_control_state",
        "channel": channel,
        "channel_display": driver.get_channel_display(channel),
        "channel_scale_v_div": driver.get_channel_scale(channel),
        "channel_offset_v": driver.get_channel_offset(channel),
        "timebase_scale_s_div": driver.get_timebase_scale(),
        "timebase_position_s": driver.get_timebase_position(),
        "trigger_mode": driver.get_trigger_mode().strip(),
        "trigger_sweep": driver.get_trigger_sweep().strip(),
        "trigger_source": driver.get_trigger_source().strip(),
        "trigger_level_v": driver.get_trigger_level(),
        "acquisition_type": driver.get_acquisition_type().strip(),
        "acquisition_points": driver.get_acquisition_points(),
        "sample_rate_sps": driver.get_sample_rate(),
    }


def _optional_float(
    parameters: Mapping[str, object],
    name: str,
) -> float | None:
    raw = parameters.get(name)
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    return float(text)


def _run_dsox_set_channel(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    channel = int(parameters.get("channel", 1))
    scale = _optional_float(parameters, "scale_v_div")
    offset = _optional_float(parameters, "offset_v")
    driver = _dsox_driver(transport)

    applied: dict[str, object] = {"channel": channel}
    if scale is not None:
        if scale <= 0:
            raise ValueError("Channel scale must be greater than 0 V/div")
        driver.set_channel_scale(channel, scale)
        applied["scale_v_div"] = scale
    if offset is not None:
        driver.set_channel_offset(channel, offset)
        applied["offset_v"] = offset

    if len(applied) == 1:
        raise ValueError("Enter channel scale and/or offset before applying")

    return {
        "kind": "keysight_dsox3000_setting_applied",
        "setting": "channel",
        "applied": applied,
    }


def _run_dsox_set_timebase(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    scale = _optional_float(parameters, "scale_s_div")
    position = _optional_float(parameters, "position_s")
    driver = _dsox_driver(transport)

    applied: dict[str, object] = {}
    if scale is not None:
        if scale <= 0:
            raise ValueError("Timebase scale must be greater than 0 s/div")
        driver.set_timebase_scale(scale)
        applied["scale_s_div"] = scale
    if position is not None:
        driver.set_timebase_position(position)
        applied["position_s"] = position

    if not applied:
        raise ValueError("Enter timebase scale and/or position before applying")

    return {
        "kind": "keysight_dsox3000_setting_applied",
        "setting": "timebase",
        "applied": applied,
    }


def _run_dsox_single(
    transport: object,
    _parameters: Mapping[str, object],
) -> object:
    """Press the programming equivalent of the front-panel Single key."""

    driver = _dsox_driver(transport)
    driver.write(":SINGle")
    return {
        "kind": "keysight_dsox3000_action",
        "action": "single",
        "status": "started",
    }


def _run_dsox_stop(
    transport: object,
    _parameters: Mapping[str, object],
) -> object:
    driver = _dsox_driver(transport)
    driver.abort()
    return {
        "kind": "keysight_dsox3000_action",
        "action": "stop",
        "status": "sent",
    }


def build_default_operation_registry() -> InstrumentOperationRegistry:
    registry = InstrumentOperationRegistry()

    dsox_profiles = ("keysight/dsox3000",)

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.read_control_state",
            title="读取控制状态",
            description=(
                "读取当前 Channel、Timebase、Trigger 与 Acquisition 的常用状态，"
                "用于刷新 DSO-X 虚拟控制面板。"
            ),
            profile_keys=dsox_profiles,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    name="channel",
                    label="Channel",
                    kind="choice",
                    default="1",
                    choices=("1", "2", "3", "4"),
                ),
            ),
            runner=_run_dsox_read_control_state,
        )
    )

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.set_channel",
            title="设置 Channel",
            description="设置指定模拟通道的 Scale 和/或 Offset。空值保持不变。",
            profile_keys=dsox_profiles,
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
                    name="scale_v_div",
                    label="Scale (V/div)",
                    kind="float",
                    description="Leave empty to keep current scale.",
                ),
                OperationParameter(
                    name="offset_v",
                    label="Offset (V)",
                    kind="float",
                    description="Leave empty to keep current offset.",
                ),
            ),
            runner=_run_dsox_set_channel,
        )
    )

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.set_timebase",
            title="设置 Timebase",
            description="设置水平 Scale 和/或 Position。空值保持不变。",
            profile_keys=dsox_profiles,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    name="scale_s_div",
                    label="Scale (s/div)",
                    kind="float",
                    description="Leave empty to keep current scale.",
                ),
                OperationParameter(
                    name="position_s",
                    label="Position (s)",
                    kind="float",
                    description="Leave empty to keep current position.",
                ),
            ),
            runner=_run_dsox_set_timebase,
        )
    )

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.single",
            title="Single",
            description="执行前面板 Single 键等效动作。",
            profile_keys=dsox_profiles,
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(),
            runner=_run_dsox_single,
        )
    )

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.stop",
            title="Stop",
            description="停止当前 DSO-X acquisition。",
            profile_keys=dsox_profiles,
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(),
            runner=_run_dsox_stop,
        )
    )

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.screenshot",
            title="Instrument Screenshot",
            description=(
                "读取真实 DSO-X 屏幕图像。使用 :DISPlay:DATA? IEEE 488.2 "
                "binary block，并在成功传输后恢复原 INKSaver 状态。"
            ),
            profile_keys=dsox_profiles,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    name="format",
                    label="Format",
                    kind="choice",
                    default="PNG",
                    choices=("PNG", "BMP", "BMP8bit"),
                ),
                OperationParameter(
                    name="palette",
                    label="Palette",
                    kind="choice",
                    default="COLor",
                    choices=("COLor", "GRAYscale"),
                ),
            ),
            runner=_run_dsox_screenshot,
        )
    )

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.snapshot_all",
            title="Snapshot All",
            description=(
                "安装 DSO-X Snapshot All，并逐项读取 31 个测量结果。"
                "该操作不是单条 SCPI Query，而是由多条命令组成的仪表级操作。"
            ),
            profile_keys=dsox_profiles,
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(
                OperationParameter(
                    name="channel",
                    label="Channel",
                    kind="choice",
                    default="1",
                    choices=("1", "2", "3", "4"),
                    description="Analog input channel used as the Snapshot source.",
                ),
            ),
            runner=_run_dsox_snapshot_all,
        )
    )

    return registry


DEFAULT_OPERATION_REGISTRY = build_default_operation_registry()
