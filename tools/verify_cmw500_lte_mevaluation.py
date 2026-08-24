#!/usr/bin/env python3

"""CMW500 LTE Multi Evaluation hardware qualification smoke test."""

import argparse
import sys
import time
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
from instrument_drivers.rohde_schwarz.cmw500.applications.lte import (
    LTEMultiEvaluation,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Verify CMW500 LTE Multi Evaluation "
            "using the platform driver."
        )
    )

    parser.add_argument(
        "--resource",
        required=True,
        help="VISA resource. It will not be printed.",
    )

    parser.add_argument(
        "--instance",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--wait",
        type=float,
        default=0.5,
        help="Seconds to wait after INITiate.",
    )

    return parser.parse_args()


def print_state(
    title,
    state,
):
    print(
        f"{title}: "
        f"{state.main},"
        f"{state.sync},"
        f"{state.resource}"
    )


def main():
    args = parse_args()

    transport = VisaTransport(
        TransportConfig(
            resource=args.resource,
            timeout_ms=args.timeout_ms,
        )
    )

    driver = RohdeSchwarzCMW500Driver(
        transport
    )

    measurement = LTEMultiEvaluation(
        driver.scpi,
        instance=args.instance,
    )

    passed = True

    print(
        "===== CMW500 LTE HARDWARE QUALIFICATION ====="
    )

    print(
        "VISA resource: [MASKED]"
    )

    try:
        driver.connect()

        print(
            "Connection: PASS"
        )

        print()
        print(
            "===== INITIAL STATE ====="
        )

        initial = (
            measurement.fetch_state_all()
        )

        print_state(
            "Initial",
            initial,
        )

        print()
        print(
            "===== INITIATE ====="
        )

        measurement.initiate()

        time.sleep(
            args.wait
        )

        state = (
            measurement.fetch_state()
        )

        state_all = (
            measurement.fetch_state_all()
        )

        print(
            "State:",
            state.main,
        )

        print_state(
            "State ALL",
            state_all,
        )

        if state.main not in {
            "RUN",
            "RDY",
        }:
            print(
                "Lifecycle after INIT: FAIL"
            )
            passed = False
        else:
            print(
                "Lifecycle after INIT: PASS"
            )

        print()
        print(
            "===== FETCH EVM AVERAGE ====="
        )

        evm = (
            measurement.fetch_evm_average()
        )

        print(
            "Reliability:",
            evm.reliability,
        )

        print(
            "Reliability label:",
            evm.reliability_label,
        )

        print(
            "Cyclic prefix:",
            evm.cyclic_prefix,
        )

        print(
            "Symbol count:",
            evm.symbol_count,
        )

        valid_low = sum(
            value is not None
            for value
            in evm.low_window
        )

        valid_high = sum(
            value is not None
            for value
            in evm.high_window
        )

        print(
            "Valid EVMLow:",
            f"{valid_low}/{evm.symbol_count}",
        )

        print(
            "Valid EVMHigh:",
            f"{valid_high}/{evm.symbol_count}",
        )

        if evm.reliability == 0:
            print(
                "Measurement data: VALID"
            )
        else:
            print(
                "Measurement data: INVALID "
                "(command path still valid)"
            )

        print()
        print(
            "===== SCPI ERROR QUEUE ====="
        )

        errors = (
            driver.get_errors()
        )

        if errors:
            print(
                "Errors:",
                errors,
            )
            passed = False
        else:
            print(
                "Error queue: EMPTY"
            )

    except Exception as exc:
        passed = False

        print()
        print(
            "EXCEPTION:",
            type(exc).__name__,
            str(exc),
        )

    finally:
        print()
        print(
            "===== ABORT / CLEANUP ====="
        )

        try:
            measurement.abort()
            time.sleep(0.2)

            final_state = (
                measurement.fetch_state_all()
            )

            print_state(
                "Final",
                final_state,
            )

            if final_state.main == "OFF":
                print(
                    "Cleanup: PASS"
                )
            else:
                print(
                    "Cleanup: FAIL"
                )
                passed = False

        except Exception as exc:
            print(
                "Cleanup exception:",
                type(exc).__name__,
                str(exc),
            )

            passed = False

        try:
            driver.disconnect()
        except Exception:
            pass

    print()
    print(
        "===== QUALIFICATION RESULT ====="
    )

    if passed:
        print(
            "CMW500 LTE Multi Evaluation "
            "hardware smoke test PASS"
        )

        return 0

    print(
        "CMW500 LTE Multi Evaluation "
        "hardware smoke test FAIL"
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
