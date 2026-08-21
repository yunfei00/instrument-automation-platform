#!/usr/bin/env python3

"""Hardware qualification probe for Keysight DSO-X 3034A."""

import argparse
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
from instrument_lab import (
    generate_markdown,
    save_probe_results,
)
from instrument_drivers.keysight.dsox3000 import (
    KeysightDSOX3000Driver,
)
from instrument_drivers.keysight.dsox3000.catalog_probe import (
    run_catalog_probe,
)


COMMAND_DIR = (
    ROOT
    / "instrument_profiles"
    / "keysight"
    / "dsox3000"
    / "commands"
)

RESULT_DIR = (
    ROOT
    / "instrument_profiles"
    / "keysight"
    / "dsox3000"
    / "hardware_results"
)

DOC_DIR = (
    ROOT
    / "instrument_profiles"
    / "keysight"
    / "dsox3000"
    / "docs"
    / "generated"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Probe a real Keysight "
            "DSO-X 3034A using VISA."
        )
    )

    parser.add_argument(
        "--resource",
        required=True,
        help=(
            "VISA resource string, for example "
            "USB0::...::INSTR or "
            "TCPIP0::192.168.1.10::inst0::INSTR"
        ),
    )

    parser.add_argument(
        "--channel",
        type=int,
        default=1,
        choices=[
            1,
            2,
            3,
            4,
        ],
    )

    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--backend",
        default=None,
        help=(
            "Optional PyVISA backend, "
            "for example @py"
        ),
    )

    parser.add_argument(
        "--include-measurements",
        action="store_true",
        help=(
            "Also probe measurement queries. "
            "Requires a meaningful input signal."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print(
        "========================================"
    )
    print(
        " Keysight DSO-X 3034A Hardware Probe"
    )
    print(
        "========================================"
    )
    print()

    config = TransportConfig(
        resource=args.resource,
        timeout_ms=args.timeout_ms,
    )

    transport = VisaTransport(
        config,
        backend=args.backend,
    )

    driver = KeysightDSOX3000Driver(
        transport
    )

    print(
        "Connecting:",
        args.resource,
    )

    try:
        identity = driver.connect()

        print()
        print(
            "===== INSTRUMENT ====="
        )
        print(
            "Manufacturer:",
            identity.manufacturer,
        )
        print(
            "Model:",
            identity.model,
        )
        print(
            "Serial:",
            identity.serial_number,
        )
        print(
            "Firmware:",
            identity.firmware,
        )

        model_upper = (
            identity.model
            .upper()
            .replace(" ", "")
        )

        if "DSO-X3034A" not in model_upper:
            print()
            print(
                "WARNING: connected model is "
                "not DSO-X 3034A."
            )

        print()
        print(
            "===== SAFE COMMAND PROBE ====="
        )

        commands, results = run_catalog_probe(
            driver.scpi,
            COMMAND_DIR,
            channel=args.channel,
            include_measurements=(
                args.include_measurements
            ),
        )

        for index, result in enumerate(
            results,
            start=1,
        ):
            print()
            print(
                f"[{index:03d}/{len(results):03d}] "
                f"{result.status}"
            )
            print(
                "ID:",
                result.command_id,
            )
            print(
                "TX:",
                result.command,
            )

            if result.raw_response is not None:
                print(
                    "RAW:",
                    repr(
                        result.raw_response
                    ),
                )

            if result.parsed_value is not None:
                print(
                    "PARSED:",
                    repr(
                        result.parsed_value
                    ),
                )

            if result.parsed_type:
                print(
                    "TYPE:",
                    result.parsed_type,
                )

            if result.unit:
                print(
                    "UNIT:",
                    result.unit,
                )

            if result.elapsed_ms is not None:
                print(
                    "TIME:",
                    result.elapsed_ms,
                    "ms",
                )

            if result.error:
                print(
                    "ERROR:",
                    result.error,
                )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        base_name = (
            f"dsox3034a_"
            f"{timestamp}"
        )

        RESULT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        DOC_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        result_path = (
            RESULT_DIR
            / f"{base_name}.json"
        )

        doc_path = (
            DOC_DIR
            / f"{base_name}.md"
        )

        metadata = {
            "manufacturer": (
                identity.manufacturer
            ),
            "model": identity.model,
            "serial_number": (
                identity.serial_number
            ),
            "firmware": identity.firmware,
            "resource": args.resource,
            "channel": args.channel,
            "include_measurements": (
                args.include_measurements
            ),
        }

        save_probe_results(
            result_path,
            results,
            metadata=metadata,
        )

        generate_markdown(
            doc_path,
            title=(
                "DSO-X 3034A "
                "Hardware Probe Report"
            ),
            commands=commands,
            results=results,
            metadata={
                "Manufacturer": (
                    identity.manufacturer
                ),
                "Model": (
                    identity.model
                ),
                "Serial": (
                    identity.serial_number
                ),
                "Firmware": (
                    identity.firmware
                ),
                "Resource": (
                    args.resource
                ),
                "Channel": (
                    args.channel
                ),
            },
        )

        passed = sum(
            result.status == "PASS"
            for result in results
        )

        failed = sum(
            result.status == "FAIL"
            for result in results
        )

        skipped = sum(
            result.status == "SKIPPED"
            for result in results
        )

        print()
        print(
            "===== SUMMARY ====="
        )
        print(
            "Total:",
            len(results),
        )
        print(
            "PASS:",
            passed,
        )
        print(
            "FAIL:",
            failed,
        )
        print(
            "SKIPPED:",
            skipped,
        )

        print()
        print(
            "JSON:",
            result_path,
        )

        print(
            "Markdown:",
            doc_path,
        )

        return 0 if failed == 0 else 2

    finally:
        try:
            driver.disconnect()
        except Exception as exc:
            print(
                "Disconnect warning:",
                exc,
            )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
