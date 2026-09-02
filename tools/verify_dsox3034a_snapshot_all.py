#!/usr/bin/env python3

"""Verify DSO-X 3034A Snapshot All immediately after one Single waveform."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core import TransportConfig, VisaTransport
from instrument_drivers.keysight.dsox3000 import (
    KeysightDSOX3000Driver,
    acquire_single_word_waveform,
    read_snapshot_all,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Acquire one DSO-X Single waveform, then read Snapshot All."
    )
    parser.add_argument("--resource", required=True)
    parser.add_argument("--channel", type=int, default=1, choices=[1, 2, 3, 4])
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--single-timeout-s", type=float, default=30.0)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--output", default="captures")
    return parser.parse_args()


def main():
    args = parse_args()
    transport = VisaTransport(
        TransportConfig(resource=args.resource, timeout_ms=args.timeout_ms),
        backend=args.backend,
    )
    driver = KeysightDSOX3000Driver(transport)

    result = None
    try:
        identity = driver.connect()
        driver.clear_errors()

        print("Instrument:", identity.raw)
        print(f"Single CH{args.channel} -> Snapshot All ...")

        waveform = acquire_single_word_waveform(
            driver,
            args.channel,
            timeout_s=args.single_timeout_s,
        )
        snapshot = read_snapshot_all(driver, args.channel)
        errors = driver.get_errors()

        result = {
            "schema_version": 1,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "instrument": {
                "manufacturer": identity.manufacturer,
                "model": identity.model,
                "serial_number": identity.serial_number,
                "firmware": identity.firmware,
                "resource": args.resource,
            },
            "channel": args.channel,
            "single_waveform": {
                "points": len(waveform.raw_samples),
                "x_increment_s": waveform.preamble.x_increment,
                "y_increment_v": waveform.preamble.y_increment,
            },
            "snapshot_all": snapshot,
            "error_queue": errors,
            "qualification": {
                "snapshot_count_ok": snapshot.get("measurement_count") == 31,
                "collection_complete": bool(snapshot.get("collection_complete")),
                "error_queue_clean": len(errors) == 0,
            },
        }

        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"dsox3034a_snapshot_all_ch{args.channel}_{timestamp}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        print("Snapshot measurements:", snapshot.get("measurement_count"))
        print("Successful:", snapshot.get("successful_measurements"))
        print("Invalid/failed:", snapshot.get("failed_or_invalid_measurements"))
        print("Collection complete:", snapshot.get("collection_complete"))
        print("SCPI errors:", errors)
        print("Saved:", path)

        if not result["qualification"]["snapshot_count_ok"]:
            return 2
        if not result["qualification"]["collection_complete"]:
            return 3
        if not result["qualification"]["error_queue_clean"]:
            return 4
        return 0
    finally:
        try:
            driver.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
