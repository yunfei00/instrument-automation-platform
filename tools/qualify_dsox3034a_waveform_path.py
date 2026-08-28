#!/usr/bin/env python3

"""Staged real-hardware qualification for DSO-X 3034A waveform capture.

This tool deliberately separates acquisition from waveform transfer so a VISA
Timeout can be attributed to the exact SCPI stage instead of being reported as
one opaque ``acquire_word_waveform`` failure.

Run one stage at a time on real hardware:

    --stage state
    --stage digitize
    --stage binary

The active stages temporarily force a small, deterministic one-shot setup and
restore the front-panel state before disconnecting.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core import TransportConfig, VisaTransport
from instrument_drivers.keysight.dsox3000 import KeysightDSOX3000Driver


@dataclass
class ScopeState:
    channel_display: bool
    trigger_sweep: str
    acquisition_type: str
    timebase_mode: str
    timebase_scale: float
    waveform_source: str
    waveform_format: str
    waveform_points_mode: str
    waveform_points: int


def parse_args():
    parser = argparse.ArgumentParser(
        description="Staged DSO-X 3034A real-hardware waveform qualification"
    )
    parser.add_argument("--resource", required=True)
    parser.add_argument("--channel", type=int, default=1, choices=[1, 2, 3, 4])
    parser.add_argument(
        "--stage",
        required=True,
        choices=["state", "digitize", "binary"],
    )
    parser.add_argument("--timeout-ms", type=int, default=15000)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--timebase", type=float, default=5.0e-7)
    parser.add_argument("--points", type=int, default=1000)
    return parser.parse_args()


def timed(label, function):
    started = time.perf_counter()
    print(f"[RUN ] {label}", flush=True)
    try:
        value = function()
    except Exception as exc:
        elapsed = (time.perf_counter() - started) * 1000.0
        print(
            f"[FAIL] {label}  {elapsed:.1f} ms  "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        raise
    elapsed = (time.perf_counter() - started) * 1000.0
    print(f"[PASS] {label}  {elapsed:.1f} ms", flush=True)
    return value


def query_text(driver, command: str) -> str:
    value = timed(command, lambda: driver.query(command))
    text = str(value).strip()
    print(f"       -> {text}", flush=True)
    return text


def snapshot(driver, channel: int) -> ScopeState:
    print("\n===== CURRENT SCOPE STATE =====")
    channel_display = timed(
        f":CHANnel{channel}:DISPlay?",
        lambda: driver.get_channel_display(channel),
    )
    print(f"       -> {channel_display}")
    trigger_sweep = query_text(driver, ":TRIGger:SWEep?")
    acquisition_type = query_text(driver, ":ACQuire:TYPE?")
    timebase_mode = query_text(driver, ":TIMebase:MODE?")
    timebase_scale = timed(
        ":TIMebase:SCALe?",
        driver.get_timebase_scale,
    )
    print(f"       -> {timebase_scale}")
    waveform_source = query_text(driver, ":WAVeform:SOURce?")
    waveform_format = query_text(driver, ":WAVeform:FORMat?")
    waveform_points_mode = query_text(driver, ":WAVeform:POINts:MODE?")
    waveform_points = timed(
        ":WAVeform:POINts?",
        driver.get_waveform_points,
    )
    print(f"       -> {waveform_points}")
    return ScopeState(
        channel_display=bool(channel_display),
        trigger_sweep=trigger_sweep,
        acquisition_type=acquisition_type,
        timebase_mode=timebase_mode,
        timebase_scale=float(timebase_scale),
        waveform_source=waveform_source,
        waveform_format=waveform_format,
        waveform_points_mode=waveform_points_mode,
        waveform_points=int(waveform_points),
    )


def configure_known_state(driver, args) -> None:
    print("\n===== APPLY QUALIFICATION STATE =====")
    timed(":STOP", lambda: driver.write(":STOP"))
    timed("*CLS", driver.clear_errors)
    timed(":TIMebase:MODE MAIN", lambda: driver.write(":TIMebase:MODE MAIN"))
    timed(
        f":TIMebase:SCALe {args.timebase}",
        lambda: driver.set_timebase_scale(args.timebase),
    )
    timed(
        f":CHANnel{args.channel}:DISPlay ON",
        lambda: driver.write(f":CHANnel{args.channel}:DISPlay ON"),
    )
    timed(":TRIGger:SWEep AUTO", lambda: driver.set_trigger_sweep("AUTO"))
    timed(":ACQuire:TYPE NORMal", lambda: driver.set_acquisition_type("NORMal"))
    timed(
        f":WAVeform:SOURce CHANnel{args.channel}",
        lambda: driver.set_waveform_source(args.channel),
    )
    timed(":WAVeform:FORMat WORD", lambda: driver.set_waveform_format("WORD"))
    timed(
        ":WAVeform:POINts:MODE NORMal",
        lambda: driver.write(":WAVeform:POINts:MODE NORMal"),
    )
    timed(
        f":WAVeform:POINts {args.points}",
        lambda: driver.write(f":WAVeform:POINts {args.points}"),
    )

    print("\n===== VERIFY QUALIFICATION STATE =====")
    query_text(driver, ":TIMebase:MODE?")
    query_text(driver, ":TRIGger:SWEep?")
    query_text(driver, ":ACQuire:TYPE?")
    query_text(driver, ":WAVeform:SOURce?")
    query_text(driver, ":WAVeform:FORMat?")
    query_text(driver, ":WAVeform:POINts:MODE?")
    query_text(driver, ":WAVeform:POINts?")
    query_text(driver, ":SYSTem:ERRor?")


def restore(driver, state: ScopeState, channel: int) -> None:
    print("\n===== RESTORE FRONT-PANEL STATE =====")

    def best_effort(label, function):
        try:
            timed(label, function)
        except Exception:
            print(f"[WARN] restore skipped after failure: {label}")

    best_effort(":STOP", lambda: driver.write(":STOP"))
    best_effort(
        f":WAVeform:POINts:MODE {state.waveform_points_mode}",
        lambda: driver.write(
            f":WAVeform:POINts:MODE {state.waveform_points_mode}"
        ),
    )
    best_effort(
        f":WAVeform:POINts {state.waveform_points}",
        lambda: driver.write(f":WAVeform:POINts {state.waveform_points}"),
    )
    best_effort(
        f":WAVeform:FORMat {state.waveform_format}",
        lambda: driver.write(f":WAVeform:FORMat {state.waveform_format}"),
    )
    best_effort(
        f":WAVeform:SOURce {state.waveform_source}",
        lambda: driver.write(f":WAVeform:SOURce {state.waveform_source}"),
    )
    best_effort(
        f":ACQuire:TYPE {state.acquisition_type}",
        lambda: driver.set_acquisition_type(state.acquisition_type),
    )
    best_effort(
        f":TRIGger:SWEep {state.trigger_sweep}",
        lambda: driver.set_trigger_sweep(state.trigger_sweep),
    )
    best_effort(
        f":TIMebase:SCALe {state.timebase_scale}",
        lambda: driver.set_timebase_scale(state.timebase_scale),
    )
    best_effort(
        f":TIMebase:MODE {state.timebase_mode}",
        lambda: driver.write(f":TIMebase:MODE {state.timebase_mode}"),
    )
    display_value = "ON" if state.channel_display else "OFF"
    best_effort(
        f":CHANnel{channel}:DISPlay {display_value}",
        lambda: driver.write(f":CHANnel{channel}:DISPlay {display_value}"),
    )


def run_digitize(driver, channel: int) -> None:
    print("\n===== DIGITIZE ONLY =====")
    timed(
        f":DIGitize CHANnel{channel} [write]",
        lambda: driver.digitize(channel),
    )
    opc = query_text(driver, "*OPC?")
    if opc not in {"1", "+1"}:
        raise RuntimeError(f"unexpected *OPC? response after DIGitize: {opc!r}")
    query_text(driver, ":SYSTem:ERRor?")


def run_text_waveform_queries(driver) -> None:
    print("\n===== POST-ACQUISITION TEXT QUERIES =====")
    query_text(driver, ":WAVeform:PREamble?")
    query_text(driver, ":WAVeform:BYTeorder?")
    query_text(driver, ":WAVeform:UNSigned?")
    query_text(driver, ":WAVeform:TYPE?")
    query_text(driver, ":WAVeform:POINts?")


def run_binary_transfer(driver) -> None:
    print("\n===== BINARY TRANSFER =====")
    transport = driver.transport
    query_ieee = getattr(transport, "query_ieee_block_bytes", None)
    if not callable(query_ieee):
        raise RuntimeError(
            "active transport does not support query_ieee_block_bytes"
        )
    payload = timed(
        ":WAVeform:DATA? [IEEE length-aware, no termination wait]",
        lambda: query_ieee(
            ":WAVeform:DATA?",
            expect_termination=False,
        ),
    )
    print(f"       -> payload_bytes={len(payload)}")
    if not payload:
        raise RuntimeError("waveform payload is empty")
    if len(payload) % 2:
        raise RuntimeError(
            f"WORD payload length should be even, got {len(payload)} bytes"
        )
    print(f"       -> decoded_word_samples_expected={len(payload) // 2}")
    query_text(driver, ":SYSTem:ERRor?")


def main() -> int:
    args = parse_args()
    transport = VisaTransport(
        TransportConfig(
            resource=args.resource,
            timeout_ms=args.timeout_ms,
        ),
        backend=args.backend,
    )
    driver = KeysightDSOX3000Driver(transport)
    state = None

    try:
        identity = timed("connect / *IDN?", driver.connect)
        print(f"Instrument: {identity.raw}")
        state = snapshot(driver, args.channel)

        if args.stage == "state":
            print("\nRESULT: PASS - connection and safe state queries are valid")
            return 0

        configure_known_state(driver, args)
        run_digitize(driver, args.channel)

        if args.stage == "digitize":
            print("\nRESULT: PASS - DIGitize completed; acquisition path is valid")
            return 0

        run_text_waveform_queries(driver)
        run_binary_transfer(driver)
        print(
            "\nRESULT: PASS - acquisition, preamble and IEEE binary transfer are valid"
        )
        return 0

    except Exception as exc:
        print("\nRESULT: FAIL")
        print(f"Exact failure: {type(exc).__name__}: {exc}")
        return 2
    finally:
        if state is not None and args.stage != "state":
            try:
                restore(driver, state, args.channel)
            except Exception as exc:
                print(f"Restore warning: {type(exc).__name__}: {exc}")
        try:
            driver.disconnect()
        except Exception as exc:
            print(f"Disconnect warning: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
