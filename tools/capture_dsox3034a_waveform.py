#!/usr/bin/env python3

"""Capture and validate one waveform from a real DSO-X 3034A."""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
]:
    sys.path.insert(
        0,
        str(
            ROOT
            / "packages"
            / package
            / "src"
        ),
    )


from instrument_core import (
    TransportConfig,
    VisaTransport,
)
from instrument_drivers.keysight.dsox3000 import (
    KeysightDSOX3000Driver,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--resource",
        required=True,
    )

    parser.add_argument(
        "--channel",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
    )

    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
    )

    parser.add_argument(
        "--backend",
        default=None,
    )

    parser.add_argument(
        "--output",
        default="captures",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    transport = VisaTransport(
        TransportConfig(
            resource=args.resource,
            timeout_ms=args.timeout_ms,
        ),
        backend=args.backend,
    )

    driver = KeysightDSOX3000Driver(
        transport
    )

    try:
        identity = driver.connect()

        print(
            "Instrument:",
            identity.raw,
        )

        print(
            "Capturing CH",
            args.channel,
            "...",
        )

        waveform = (
            driver.acquire_word_waveform(
                args.channel
            )
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_dir = Path(
            args.output
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        stem = (
            f"dsox3034a_ch{args.channel}_"
            f"{timestamp}"
        )

        csv_path = (
            output_dir
            / f"{stem}.csv"
        )

        json_path = (
            output_dir
            / f"{stem}.json"
        )

        with csv_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.writer(handle)

            writer.writerow(
                [
                    "index",
                    "time_s",
                    "voltage_v",
                    "raw_sample",
                ]
            )

            for index, (
                time_value,
                voltage,
                raw,
            ) in enumerate(
                zip(
                    waveform.time_seconds,
                    waveform.voltage_volts,
                    waveform.raw_samples,
                )
            ):
                writer.writerow(
                    [
                        index,
                        time_value,
                        voltage,
                        raw,
                    ]
                )

        metadata = {
            "manufacturer": (
                identity.manufacturer
            ),
            "model": identity.model,
            "serial": (
                identity.serial_number
            ),
            "firmware": (
                identity.firmware
            ),
            "resource": args.resource,
            "channel": args.channel,
            "points": len(
                waveform.raw_samples
            ),
            "preamble": {
                "format": (
                    waveform.preamble.format
                ),
                "acquisition_type": (
                    waveform.preamble.acquisition_type
                ),
                "points": (
                    waveform.preamble.points
                ),
                "count": (
                    waveform.preamble.count
                ),
                "x_increment": (
                    waveform.preamble.x_increment
                ),
                "x_origin": (
                    waveform.preamble.x_origin
                ),
                "x_reference": (
                    waveform.preamble.x_reference
                ),
                "y_increment": (
                    waveform.preamble.y_increment
                ),
                "y_origin": (
                    waveform.preamble.y_origin
                ),
                "y_reference": (
                    waveform.preamble.y_reference
                ),
            },
        }

        json_path.write_text(
            json.dumps(
                metadata,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        print()
        print(
            "===== CAPTURE RESULT ====="
        )

        print(
            "Points:",
            len(
                waveform.raw_samples
            ),
        )

        print(
            "Time start:",
            waveform.time_seconds[0]
            if waveform.time_seconds
            else None,
        )

        print(
            "Time end:",
            waveform.time_seconds[-1]
            if waveform.time_seconds
            else None,
        )

        print(
            "Voltage min:",
            min(
                waveform.voltage_volts
            )
            if waveform.voltage_volts
            else None,
        )

        print(
            "Voltage max:",
            max(
                waveform.voltage_volts
            )
            if waveform.voltage_volts
            else None,
        )

        print(
            "CSV:",
            csv_path,
        )

        print(
            "Metadata:",
            json_path,
        )

        return 0

    finally:
        try:
            driver.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
