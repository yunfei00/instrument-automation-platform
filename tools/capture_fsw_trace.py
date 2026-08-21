#!/usr/bin/env python3

"""Capture one spectrum trace from R&S FSW."""

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
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Perform one FSW sweep and "
            "save TRACE1 as CSV."
        )
    )

    parser.add_argument(
        "--resource",
        required=True,
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
        "--center",
        type=float,
        default=None,
        help="Center frequency in Hz",
    )

    parser.add_argument(
        "--span",
        type=float,
        default=None,
        help="Frequency span in Hz",
    )

    parser.add_argument(
        "--rbw",
        type=float,
        default=None,
        help="Resolution bandwidth in Hz",
    )

    parser.add_argument(
        "--vbw",
        type=float,
        default=None,
        help="Video bandwidth in Hz",
    )

    parser.add_argument(
        "--trigger-source",
        default=None,
        help=(
            "Optional FSW trigger source. "
            "If omitted, current instrument "
            "trigger configuration is preserved."
        ),
    )

    parser.add_argument(
        "--channel",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--window",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--trace",
        type=int,
        default=1,
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

    driver = RohdeSchwarzFSWDriver(
        transport
    )

    try:
        identity = driver.connect()

        print(
            "Instrument:",
            identity.raw,
        )

        if args.center is not None:
            driver.set_center_frequency(
                args.center
            )

        if args.span is not None:
            driver.set_span(
                args.span
            )

        if args.rbw is not None:
            driver.set_rbw(
                args.rbw
            )

        if args.vbw is not None:
            driver.set_vbw(
                args.vbw
            )

        if args.trigger_source is not None:
            driver.set_trigger_source(
                args.trigger_source
            )

        print()
        print(
            "Starting single measurement..."
        )
        print(
            "Current trigger:",
            driver.get_trigger_source(),
        )

        spectrum = (
            driver.acquire_trace_ascii(
                channel=args.channel,
                window=args.window,
                trace=args.trace,
            )
        )

        output_dir = Path(
            args.output
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        stem = (
            f"fsw_trace_{timestamp}"
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
            writer = csv.writer(
                handle
            )

            writer.writerow(
                [
                    "index",
                    "frequency_hz",
                    "level",
                ]
            )

            for index, (
                frequency,
                level,
            ) in enumerate(
                zip(
                    spectrum.frequencies_hz,
                    spectrum.levels,
                )
            ):
                writer.writerow(
                    [
                        index,
                        frequency,
                        level,
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
            "points": spectrum.points,
            "start_hz": spectrum.start_hz,
            "stop_hz": spectrum.stop_hz,
            "peak_frequency_hz": (
                spectrum.peak_frequency_hz
            ),
            "peak_level": (
                spectrum.peak_level
            ),
            "rbw_hz": (
                driver.get_rbw()
            ),
            "vbw_hz": (
                driver.get_vbw()
            ),
            "sweep_time_s": (
                driver.get_sweep_time()
            ),
            "trigger_source": (
                driver.get_trigger_source()
            ),
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
            "===== TRACE RESULT ====="
        )
        print(
            "Points:",
            spectrum.points,
        )
        print(
            "Start:",
            spectrum.start_hz,
            "Hz",
        )
        print(
            "Stop:",
            spectrum.stop_hz,
            "Hz",
        )
        print(
            "Peak frequency:",
            spectrum.peak_frequency_hz,
            "Hz",
        )
        print(
            "Peak level:",
            spectrum.peak_level,
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
