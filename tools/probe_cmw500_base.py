#!/usr/bin/env python3

"""Safe base-system discovery probe for R&S CMW500."""

import argparse
import json
import sys
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

for package in [
    "instrument_core",
    "instrument_scpi",
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
from instrument_drivers.rohde_schwarz.cmw500 import (
    RohdeSchwarzCMW500Driver,
)


RESULT_DIR = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "cmw500"
    / "hardware_results"
)


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Discover CMW500 base-system "
            "identity, software, options and "
            "sub-instrument configuration."
        )
    )

    parser.add_argument(
        "--resource",
        required=True,
        help=(
            "VISA resource, for example "
            "TCPIP0::192.168.1.10::"
            "hislip0::INSTR"
        ),
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
        "--resources",
        action="store_true",
        help=(
            "Also query remote VISA resource "
            "strings for discovered channels."
        ),
    )

    return parser.parse_args()


def safe_query(
    label,
    callback,
):
    try:
        value = callback()

        return {
            "status": "PASS",
            "value": value,
        }

    except Exception as exc:
        return {
            "status": "FAIL",
            "error": (
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        }


def main():
    args = parse_args()

    transport = VisaTransport(
        TransportConfig(
            resource=args.resource,
            timeout_ms=(
                args.timeout_ms
            ),
        ),
        backend=args.backend,
    )

    driver = (
        RohdeSchwarzCMW500Driver(
            transport
        )
    )

    report = {
        "timestamp": utc_now(),
        "resource": args.resource,
        "queries": {},
    }

    try:
        identity = (
            driver.connect()
        )

        report["identity"] = {
            "manufacturer": (
                identity.manufacturer
            ),
            "model": (
                identity.model
            ),
            "serial_number": (
                identity.serial_number
            ),
            "firmware": (
                identity.firmware
            ),
            "raw": (
                identity.raw
            ),
        }

        print(
            "========================================"
        )
        print(
            " R&S CMW500 Base Discovery"
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

        print()
        print(
            "===== BASE SYSTEM ====="
        )

        queries = {
            "device_id": safe_query(
                "device_id",
                driver.get_device_id,
            ),
            "options_raw": safe_query(
                "options_raw",
                driver.get_installed_options_raw,
            ),
            "software_versions_raw": (
                safe_query(
                    "software_versions_raw",
                    driver.get_software_versions_raw,
                )
            ),
            "subinstrument": {
                "status": "PENDING"
            },
        }

        # Avoid querying SUBinst three times.
        sub_result = safe_query(
            "subinstrument",
            driver.get_subinstrument_info,
        )

        if (
            sub_result["status"]
            == "PASS"
        ):
            sub = sub_result["value"]

            queries[
                "subinstrument"
            ] = {
                "status": "PASS",
                "value": {
                    "current_index": (
                        sub.current_index
                    ),
                    "current_number": (
                        sub.current_number
                    ),
                    "count": (
                        sub.count
                    ),
                },
            }

            sub_count = (
                sub.count
            )

        else:
            queries[
                "subinstrument"
            ] = sub_result

            sub_count = 1

        report["queries"] = queries

        for name, result in (
            queries.items()
        ):
            print()
            print(
                f"[{name}] "
                f"{result['status']}"
            )

            if (
                result["status"]
                == "PASS"
            ):
                print(
                    result["value"]
                )
            else:
                print(
                    result["error"]
                )

        if args.resources:
            print()
            print(
                "===== REMOTE RESOURCES ====="
            )

            resources = {}

            for channel in range(
                1,
                min(
                    sub_count,
                    4,
                )
                + 1,
            ):
                resources[
                    f"hislip{channel}"
                ] = safe_query(
                    f"hislip{channel}",
                    lambda ch=channel: (
                        driver
                        .get_hislip_resource(
                            ch
                        )
                    ),
                )

                resources[
                    f"vxi{channel}"
                ] = safe_query(
                    f"vxi{channel}",
                    lambda ch=channel: (
                        driver
                        .get_vxi_resource(
                            ch
                        )
                    ),
                )

            resources[
                "usb"
            ] = safe_query(
                "usb",
                driver.get_usb_resource,
            )

            report[
                "remote_resources"
            ] = resources

            for name, result in (
                resources.items()
            ):
                print(
                    name,
                    "=>",
                    result,
                )

        print()
        print(
            "===== SOFTWARE PACKAGES ====="
        )

        package_result = safe_query(
            "software_packages",
            driver.get_software_versions,
        )

        if (
            package_result["status"]
            == "PASS"
        ):
            package_rows = [
                {
                    "name": item.name,
                    "version": (
                        item.version
                    ),
                }
                for item
                in package_result["value"]
            ]

            report[
                "software_packages"
            ] = package_rows

            for item in package_rows:
                print(
                    item["name"],
                    "=>",
                    item["version"],
                )

        else:
            report[
                "software_packages"
            ] = package_result

            print(
                package_result["error"]
            )

        print()
        print(
            "===== ERROR QUEUE ====="
        )

        error_result = safe_query(
            "error_queue",
            driver.get_errors,
        )

        if (
            error_result["status"]
            == "PASS"
        ):
            report[
                "error_queue"
            ] = (
                error_result["value"]
            )

            print(
                error_result["value"]
            )
        else:
            report[
                "error_queue"
            ] = error_result

            print(
                error_result["error"]
            )

        RESULT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        output = (
            RESULT_DIR
            / (
                "cmw500_base_"
                f"{timestamp}.json"
            )
        )

        output.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        print()
        print(
            "===== RESULT ====="
        )

        print(
            "Saved:",
            output,
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
