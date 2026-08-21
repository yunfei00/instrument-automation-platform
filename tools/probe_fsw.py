#!/usr/bin/env python3

"""Safe hardware probe for R&S FSW."""

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
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
)
from instrument_drivers.rohde_schwarz.fsw.catalog_probe import (
    run_catalog_probe,
)


COMMAND_DIR = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "fsw"
    / "commands"
)

RESULT_DIR = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "fsw"
    / "hardware_results"
)

DOC_DIR = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "fsw"
    / "docs"
    / "generated"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Safe command probe for "
            "R&S FSW."
        )
    )

    parser.add_argument(
        "--resource",
        required=True,
    )

    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--backend",
        default=None,
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
        "--marker",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--trace",
        type=int,
        default=1,
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
            "========================================"
        )
        print(
            " R&S FSW Safe Hardware Probe"
        )
        print(
            "========================================"
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

        commands, results = (
            run_catalog_probe(
                driver.scpi,
                COMMAND_DIR,
                channel=args.channel,
                window=args.window,
                marker=args.marker,
                trace=args.trace,
            )
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
            / f"fsw_probe_{timestamp}.json"
        )

        doc_path = (
            DOC_DIR
            / f"fsw_probe_{timestamp}.md"
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
        }

        save_probe_results(
            result_path,
            results,
            metadata=metadata,
        )

        generate_markdown(
            doc_path,
            title="R&S FSW Hardware Probe Report",
            commands=commands,
            results=results,
            metadata={
                "Manufacturer": identity.manufacturer,
                "Model": identity.model,
                "Serial": identity.serial_number,
                "Firmware": identity.firmware,
                "Resource": args.resource,
            },
        )

        passed = sum(
            x.status == "PASS"
            for x in results
        )

        failed = sum(
            x.status == "FAIL"
            for x in results
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
            "JSON:",
            result_path,
        )
        print(
            "Markdown:",
            doc_path,
        )

        return (
            0
            if failed == 0
            else 2
        )

    finally:
        try:
            driver.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
