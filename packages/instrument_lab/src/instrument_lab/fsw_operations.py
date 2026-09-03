"""Reusable R&S FSW operations for the dedicated control surface.

The module is intentionally Qt-free. It connects the existing FSW driver to
Instrument Lab's operation registry so GUI, CLI and future front ends can reuse
the same higher-level actions without copying SCPI strings into view code.
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
_READ_STATE_ID = "rohde_schwarz.fsw.read_control_state"
_SET_CENTER_SPAN_ID = "rohde_schwarz.fsw.set_center_span"
_SET_START_STOP_ID = "rohde_schwarz.fsw.set_start_stop"
_SET_BANDWIDTH_ID = "rohde_schwarz.fsw.set_bandwidth"
_SET_INPUT_ID = "rohde_schwarz.fsw.set_input"
_SET_CONTINUOUS_ID = "rohde_schwarz.fsw.set_continuous"
_SET_SWEEP_TIME_ID = "rohde_schwarz.fsw.set_sweep_time"
_MARKER_PEAK_ID = "rohde_schwarz.fsw.marker_peak"
_SINGLE_TRACE_ID = "rohde_schwarz.fsw.single_trace"


def _driver(transport: object):
    from instrument_drivers.rohde_schwarz.fsw import RohdeSchwarzFSWDriver

    return RohdeSchwarzFSWDriver(transport)


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


def _positive_optional_float(
    parameters: Mapping[str, object],
    name: str,
    label: str,
) -> float | None:
    value = _optional_float(parameters, name)
    if value is not None and value <= 0:
        raise ValueError(f"{label} must be greater than 0")
    return value


def _nonnegative_optional_float(
    parameters: Mapping[str, object],
    name: str,
    label: str,
) -> float | None:
    value = _optional_float(parameters, name)
    if value is not None and value < 0:
        raise ValueError(f"{label} must be non-negative")
    return value


def _build_time_axis(sweep_time_s: float, points: int) -> tuple[float, ...]:
    """Build the Zero Span time axis from the manual-verified sweep time."""
    if sweep_time_s < 0:
        raise ValueError("Sweep time must be non-negative")
    if points <= 0:
        raise ValueError("Trace point count must be positive")
    if points == 1:
        return (0.0,)

    step_s = sweep_time_s / (points - 1)
    return tuple(index * step_s for index in range(points))


def _run_read_control_state(
    transport: object,
    _parameters: Mapping[str, object],
) -> object:
    driver = _driver(transport)
    return {
        "kind": "rohde_schwarz_fsw_control_state",
        "center_hz": driver.get_center_frequency(),
        "span_hz": driver.get_span(),
        "start_hz": driver.get_start_frequency(),
        "stop_hz": driver.get_stop_frequency(),
        "rbw_hz": driver.get_rbw(),
        "vbw_hz": driver.get_vbw(),
        "sweep_time_s": driver.get_sweep_time(),
        "trigger_source": driver.get_trigger_source().strip(),
        "continuous": driver.get_continuous(),
        "rf_attenuation_auto": driver.get_rf_attenuation_auto(),
        "rf_attenuation_db": driver.get_rf_attenuation_db(),
        "preamp_db": driver.get_preamp_db(),
        # Reference Level is deliberately omitted here. Its current FSW
        # catalog entry is still candidate and must not become an automatic
        # state query merely because a Driver API exists.
    }


def _run_set_center_span(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    center = _positive_optional_float(parameters, "center_hz", "Center frequency")
    # Span=0 is a valid and important FSW Zero Span configuration.
    span = _nonnegative_optional_float(parameters, "span_hz", "Span")
    if center is None and span is None:
        raise ValueError("Enter Center and/or Span before applying")

    driver = _driver(transport)
    applied: dict[str, object] = {}
    if center is not None:
        driver.set_center_frequency(center)
        applied["center_hz"] = center
    if span is not None:
        driver.set_span(span)
        applied["span_hz"] = span
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "center_span",
        "applied": applied,
    }


def _run_set_start_stop(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    start = _positive_optional_float(parameters, "start_hz", "Start frequency")
    stop = _positive_optional_float(parameters, "stop_hz", "Stop frequency")
    if start is None and stop is None:
        raise ValueError("Enter Start and/or Stop before applying")
    if start is not None and stop is not None and stop <= start:
        raise ValueError("Stop frequency must be greater than Start frequency")

    driver = _driver(transport)
    applied: dict[str, object] = {}
    if start is not None:
        driver.set_start_frequency(start)
        applied["start_hz"] = start
    if stop is not None:
        driver.set_stop_frequency(stop)
        applied["stop_hz"] = stop
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "start_stop",
        "applied": applied,
    }


def _run_set_bandwidth(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    rbw = _positive_optional_float(parameters, "rbw_hz", "RBW")
    vbw = _positive_optional_float(parameters, "vbw_hz", "VBW")
    if rbw is None and vbw is None:
        raise ValueError("Enter RBW and/or VBW before applying")

    driver = _driver(transport)
    applied: dict[str, object] = {}
    if rbw is not None:
        driver.set_rbw(rbw)
        applied["rbw_hz"] = rbw
    if vbw is not None:
        driver.set_vbw(vbw)
        applied["vbw_hz"] = vbw
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "bandwidth",
        "applied": applied,
    }


def _run_set_input(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    attenuation_mode = str(
        parameters.get("attenuation_mode", "AUTO")
    ).strip().upper()
    preamp_db = int(str(parameters.get("preamp_db", "0")).strip())
    attenuation_db = _optional_float(parameters, "attenuation_db")

    if attenuation_mode not in {"AUTO", "MANUAL"}:
        raise ValueError("RF attenuation mode must be AUTO or MANUAL")
    if preamp_db not in {0, 15, 30}:
        raise ValueError("FSW preamp must be 0, 15 or 30 dB")
    if attenuation_db is not None and attenuation_db < 0:
        raise ValueError("RF attenuation must be non-negative")
    if attenuation_mode == "MANUAL" and attenuation_db is None:
        raise ValueError("Manual RF attenuation requires an attenuation value")

    driver = _driver(transport)
    applied: dict[str, object] = {
        "attenuation_mode": attenuation_mode,
        "preamp_db": preamp_db,
    }

    if attenuation_mode == "AUTO":
        driver.set_rf_attenuation_auto(True)
    else:
        driver.set_rf_attenuation_manual_db(float(attenuation_db))
        applied["attenuation_db"] = float(attenuation_db)

    driver.set_preamp_db(preamp_db)
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "input",
        "applied": applied,
    }


def _run_set_continuous(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    state = str(parameters.get("state", "ON")).strip().upper()
    if state not in {"ON", "OFF"}:
        raise ValueError("Continuous state must be ON or OFF")
    driver = _driver(transport)
    driver.set_continuous(state == "ON")
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "continuous",
        "applied": {"state": state},
    }


def _run_set_sweep_time(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    sweep_time_s = _positive_optional_float(parameters, "sweep_time_s", "Sweep time")
    if sweep_time_s is None:
        raise ValueError("Enter Sweep Time before applying")

    from instrument_drivers.rohde_schwarz.fsw import set_sweep_time_s

    applied = set_sweep_time_s(_driver(transport), sweep_time_s)
    return {
        "kind": "rohde_schwarz_fsw_setting_applied",
        "setting": "sweep_time",
        "applied": {"sweep_time_s": applied},
    }


def _run_marker_peak(
    transport: object,
    _parameters: Mapping[str, object],
) -> object:
    from instrument_drivers.rohde_schwarz.fsw import marker_peak_search

    level_dbm = marker_peak_search(_driver(transport), window=1, marker=1)
    return {
        "kind": "rohde_schwarz_fsw_marker_peak",
        "window": 1,
        "marker": 1,
        "level_dbm": level_dbm,
    }


def _run_single_trace(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    timeout_s = float(parameters.get("timeout_s", 30.0))
    if timeout_s <= 0:
        raise ValueError("Trace timeout must be greater than 0 seconds")

    driver = _driver(transport)
    trace = driver.acquire_trace_ascii(timeout_s=timeout_s)

    # In Zero Span the analyzer observes level versus time at one fixed RF
    # frequency. Start and Stop are therefore equal and must not be presented as
    # a frequency sweep. Use the manual-verified Sweep Time query to construct
    # a physical time axis from the number of returned trace samples.
    zero_span = trace.start_hz == trace.stop_hz
    if zero_span:
        sweep_time_s = driver.get_sweep_time()
        times_s = _build_time_axis(sweep_time_s, trace.points)
        peak_index = trace.peak_index
        peak_time_s = None if peak_index is None else times_s[peak_index]
        return {
            "kind": "rohde_schwarz_fsw_trace",
            "axis_kind": "time",
            "zero_span": True,
            "points": trace.points,
            "center_frequency_hz": trace.start_hz,
            "sweep_time_s": sweep_time_s,
            "peak_time_s": peak_time_s,
            "peak_level_dbm": trace.peak_level,
            "times_s": times_s,
            "levels_dbm": trace.levels,
        }

    return {
        "kind": "rohde_schwarz_fsw_trace",
        "axis_kind": "frequency",
        "zero_span": False,
        "points": trace.points,
        "start_hz": trace.start_hz,
        "stop_hz": trace.stop_hz,
        "peak_frequency_hz": trace.peak_frequency_hz,
        "peak_level_dbm": trace.peak_level,
        "frequencies_hz": trace.frequencies_hz,
        "levels_dbm": trace.levels,
    }


def ensure_fsw_operations_registered() -> None:
    """Register the FSW control-surface operations exactly once."""

    definitions = (
        InstrumentOperation(
            id=_READ_STATE_ID,
            title="读取 FSW 常用状态",
            description=(
                "读取 Frequency、Bandwidth、Sweep、Trigger、RF Attenuation、"
                "Preamp 与 Continuous 常用状态。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(),
            runner=_run_read_control_state,
        ),
        InstrumentOperation(
            id=_SET_CENTER_SPAN_ID,
            title="设置 Center / Span",
            description="设置中心频率和/或 Span；Span=0 表示 Zero Span；空值保持当前值。",
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter("center_hz", "Center (Hz)", "float"),
                OperationParameter("span_hz", "Span (Hz)", "float"),
            ),
            runner=_run_set_center_span,
        ),
        InstrumentOperation(
            id=_SET_START_STOP_ID,
            title="设置 Start / Stop",
            description="设置频率扫描 Start 和/或 Stop；空值保持当前值。",
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter("start_hz", "Start (Hz)", "float"),
                OperationParameter("stop_hz", "Stop (Hz)", "float"),
            ),
            runner=_run_set_start_stop,
        ),
        InstrumentOperation(
            id=_SET_BANDWIDTH_ID,
            title="设置 RBW / VBW",
            description="设置 RBW 和/或 VBW；空值保持当前值。",
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter("rbw_hz", "RBW (Hz)", "float"),
                OperationParameter("vbw_hz", "VBW (Hz)", "float"),
            ),
            runner=_run_set_bandwidth,
        ),
        InstrumentOperation(
            id=_SET_INPUT_ID,
            title="设置 RF Input",
            description=(
                "设置硬件已验证的 RF Attenuation Auto/Manual 与内部 Preamp。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    "attenuation_mode",
                    "RF Atten",
                    "choice",
                    "AUTO",
                    ("AUTO", "MANUAL"),
                ),
                OperationParameter(
                    "attenuation_db",
                    "Manual Atten (dB)",
                    "float",
                    description="AUTO 时可留空。",
                ),
                OperationParameter(
                    "preamp_db",
                    "Preamp (dB)",
                    "choice",
                    "0",
                    ("0", "15", "30"),
                ),
            ),
            runner=_run_set_input,
        ),
        InstrumentOperation(
            id=_SET_CONTINUOUS_ID,
            title="Continuous",
            description="设置 FSW Continuous Sweep ON/OFF。",
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    "state",
                    "Continuous",
                    "choice",
                    "ON",
                    ("ON", "OFF"),
                ),
            ),
            runner=_run_set_continuous,
        ),
        InstrumentOperation(
            id=_SET_SWEEP_TIME_ID,
            title="设置 Sweep Time",
            description="使用已人工核对的 Sweep Time 命令设置扫描/Zero Span 时间。",
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter("sweep_time_s", "Sweep Time (s)", "float"),
            ),
            runner=_run_set_sweep_time,
        ),
        InstrumentOperation(
            id=_MARKER_PEAK_ID,
            title="Marker 1 Peak Search",
            description=(
                "将 Marker 1 移动到当前 Trace 最大值并读取 Y 结果。"
                "本操作只使用已 manual_verified 的 MAXimum:PEAK 与 MARKer:Y?。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(),
            runner=_run_marker_peak,
        ),
        InstrumentOperation(
            id=_SINGLE_TRACE_ID,
            title="Single Spectrum / Zero Span Trace",
            description=(
                "关闭 Continuous 并执行一次有界等待的测量。普通 Span 返回 Frequency/Level；"
                "Span=0 时使用 Sweep Time 返回 Time/Level。"
            ),
            profile_keys=_PROFILE_KEYS,
            safety=SafetyLevel.SAFE,
            parameters=(
                OperationParameter(
                    "timeout_s",
                    "Timeout (s)",
                    "float",
                    30.0,
                    description="外触发环境应设置合理上限，避免无限等待。",
                ),
            ),
            runner=_run_single_trace,
        ),
    )

    for operation in definitions:
        try:
            DEFAULT_OPERATION_REGISTRY.get(operation.id)
        except KeyError:
            DEFAULT_OPERATION_REGISTRY.register(operation)
