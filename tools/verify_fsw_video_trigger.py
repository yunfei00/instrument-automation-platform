#!/usr/bin/env python3

"""Hardware qualification helper for R&S FSW VIDEO-triggered single traces."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core import TransportConfig, VisaTransport
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
    configure_video_trigger,
    get_trigger_offset_s,
    get_video_trigger_level_pct,
    set_trigger_offset_s,
    set_video_trigger_level_pct,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify FSW VIDEO trigger level/offset and one-shot trace acquisition."
    )
    parser.add_argument("--resource", required=True)
    parser.add_argument("--video-level-pct", type=float, default=45.9)
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--window", type=int, default=1)
    parser.add_argument("--trace", type=int, default=1)
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--poll-interval-s", type=float, default=0.05)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--output", default="captures")
    return parser.parse_args()


def _try(call: Callable[[], Any]) -> Any:
    try:
        return call()
    except Exception as exc:
        return {
            "available": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }


def _is_value(value: Any) -> bool:
    return not isinstance(value, dict)


def main() -> int:
    args = parse_args()
    if not 0.0 <= args.video_level_pct <= 100.0:
        raise SystemExit("--video-level-pct must be between 0 and 100")
    if args.timeout_s <= 0:
        raise SystemExit("--timeout-s must be greater than 0")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"fsw_video_trigger_{stamp}"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"

    transport = VisaTransport(
        TransportConfig(
            resource=args.resource,
            timeout_ms=max(1000, int(args.timeout_s * 1000)),
        ),
        backend=args.backend,
    )
    driver = RohdeSchwarzFSWDriver(transport)

    result: dict[str, Any] = {
        "schema_version": 1,
        "qualification": "fsw_video_trigger",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "resource": args.resource,
        "requested_video_level_pct": args.video_level_pct,
        "status": "failed",
    }
    connected = False
    original: dict[str, Any] = {}
    trace = None

    try:
        identity = driver.connect()
        connected = True
        result["instrument"] = {
            "manufacturer": identity.manufacturer,
            "model": identity.model,
            "serial_number": identity.serial_number,
            "firmware": identity.firmware,
            "raw": identity.raw,
        }

        original = {
            "trigger_source": _try(lambda: str(driver.get_trigger_source()).strip()),
            "trigger_offset_s": _try(lambda: get_trigger_offset_s(driver)),
            "video_level_pct": _try(lambda: get_video_trigger_level_pct(driver)),
            "continuous": _try(lambda: driver.get_continuous(args.channel)),
            "span_hz": _try(driver.get_span),
        }
        result["original_state"] = original

        driver.clear_errors()
        sweep_time_s = float(driver.get_sweep_time())
        if sweep_time_s <= 0:
            raise ValueError(f"FSW returned invalid Sweep Time: {sweep_time_s}")
        trigger_offset_s = -sweep_time_s / 2.0

        result["sweep_time_s"] = sweep_time_s
        result["requested_trigger_offset_s"] = trigger_offset_s

        readback = configure_video_trigger(
            driver,
            level_pct=args.video_level_pct,
            offset_s=trigger_offset_s,
        )
        result["trigger_readback"] = readback

        driver.arm_trace_ascii(channel=args.channel)
        trace = driver.wait_and_read_trace_ascii(
            window=args.window,
            trace=args.trace,
            timeout_s=args.timeout_s,
            poll_interval_s=args.poll_interval_s,
        )

        result["trace"] = {
            "points": trace.points,
            "start_hz": trace.start_hz,
            "stop_hz": trace.stop_hz,
            "peak_frequency_hz": trace.peak_frequency_hz,
            "peak_level": trace.peak_level,
        }
        result["scpi_errors"] = driver.get_errors()
        result["status"] = "passed"

        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["index", "frequency_hz", "level"])
            for index, (frequency_hz, level) in enumerate(
                zip(trace.frequencies_hz, trace.levels)
            ):
                writer.writerow([index, frequency_hz, level])
        result["trace_csv"] = str(csv_path)

    except Exception as exc:
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        if connected:
            result["scpi_errors_after_failure"] = _try(driver.get_errors)
    finally:
        restore_errors = []
        if connected:
            try:
                driver.abort()
            except Exception as exc:
                restore_errors.append(f"abort: {type(exc).__name__}: {exc}")

            if _is_value(original.get("video_level_pct")):
                try:
                    set_video_trigger_level_pct(driver, float(original["video_level_pct"]))
                except Exception as exc:
                    restore_errors.append(
                        f"video_level: {type(exc).__name__}: {exc}"
                    )

            if _is_value(original.get("trigger_offset_s")):
                try:
                    set_trigger_offset_s(driver, float(original["trigger_offset_s"]))
                except Exception as exc:
                    restore_errors.append(
                        f"trigger_offset: {type(exc).__name__}: {exc}"
                    )

            if _is_value(original.get("trigger_source")):
                try:
                    driver.set_trigger_source(str(original["trigger_source"]))
                except Exception as exc:
                    restore_errors.append(
                        f"trigger_source: {type(exc).__name__}: {exc}"
                    )

            if _is_value(original.get("continuous")):
                try:
                    driver.set_continuous(bool(original["continuous"]), args.channel)
                except Exception as exc:
                    restore_errors.append(
                        f"continuous: {type(exc).__name__}: {exc}"
                    )

            try:
                driver.disconnect()
            except Exception as exc:
                restore_errors.append(f"disconnect: {type(exc).__name__}: {exc}")

        result["restore_errors"] = restore_errors
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        json_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json_path)
    if result["status"] == "passed":
        print(csv_path)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
