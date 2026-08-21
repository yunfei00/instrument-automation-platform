#!/usr/bin/env python3

"""Static baseline audit for instrument-automation-platform."""

from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]

errors = []
warnings = []


def ok(message):
    print(f"[PASS] {message}")


def fail(message):
    print(f"[FAIL] {message}")
    errors.append(message)


def warn(message):
    print(f"[WARN] {message}")
    warnings.append(message)


def require_path(relative):
    path = ROOT / relative

    if path.exists():
        ok(relative)
    else:
        fail(f"Missing: {relative}")


def check_json(relative):
    path = ROOT / relative

    if not path.exists():
        fail(f"Missing JSON: {relative}")
        return

    try:
        json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        fail(
            f"Invalid JSON {relative}: "
            f"{type(exc).__name__}: {exc}"
        )
    else:
        ok(f"JSON {relative}")


print()
print("===== CORE ARCHITECTURE =====")

required_paths = [
    "README.md",
    "VERSION",

    "docs/architecture/ARCHITECTURE.md",
    "docs/architecture/SCOPE.md",
    "docs/architecture/DRIVER_CONTRACT.md",
    "docs/architecture/TRANSPORT_SCPI.md",
    "docs/architecture/INSTRUMENT_LAB_V01.md",
    "docs/architecture/RECORD_REPLAY.md",
    "docs/architecture/QUALIFICATION.md",

    "packages/instrument_core/src/instrument_core",
    "packages/instrument_scpi/src/instrument_scpi",
    "packages/instrument_drivers/src/instrument_drivers",
    "packages/instrument_lab/src/instrument_lab",
    "packages/instrument_qualification/src/instrument_qualification",

    "instrument_profiles/keysight/dsox3000",
    "instrument_profiles/rohde_schwarz/fsw",

    "tests/unit",
]

for relative in required_paths:
    require_path(relative)


print()
print("===== DSOX3000 ASSETS =====")

dsox_files = [
    "instrument_profiles/keysight/dsox3000/manuals.json",
    "instrument_profiles/keysight/dsox3000/commands/acquisition.json",
    "instrument_profiles/keysight/dsox3000/commands/channel.json",
    "instrument_profiles/keysight/dsox3000/commands/measurement.json",
    "instrument_profiles/keysight/dsox3000/commands/system.json",
    "instrument_profiles/keysight/dsox3000/commands/timebase.json",
    "instrument_profiles/keysight/dsox3000/commands/trigger.json",
    "instrument_profiles/keysight/dsox3000/commands/waveform.json",
    "instrument_profiles/keysight/dsox3000/qualification/requirements.json",
]

for relative in dsox_files:
    check_json(relative)

require_path(
    "packages/instrument_drivers/src/"
    "instrument_drivers/keysight/dsox3000/driver.py"
)

require_path(
    "packages/instrument_drivers/src/"
    "instrument_drivers/keysight/dsox3000/waveform.py"
)


print()
print("===== FSW ASSETS =====")

fsw_files = [
    "instrument_profiles/rohde_schwarz/fsw/manuals.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/frequency.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/bandwidth.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/amplitude.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/sweep.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/trigger.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/initiate.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/trace.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/marker.json",
    "instrument_profiles/rohde_schwarz/fsw/commands/system.json",
    "instrument_profiles/rohde_schwarz/fsw/qualification/requirements.json",
]

for relative in fsw_files:
    check_json(relative)

require_path(
    "packages/instrument_drivers/src/"
    "instrument_drivers/rohde_schwarz/fsw/driver.py"
)

require_path(
    "packages/instrument_drivers/src/"
    "instrument_drivers/rohde_schwarz/fsw/spectrum.py"
)


print()
print("===== PLATFORM BOUNDARY =====")

forbidden_paths = [
    "products",
    "packages/instrument_ui",
    "packages/instrument_acquisition",
]

for relative in forbidden_paths:
    path = ROOT / relative

    if path.exists():
        fail(
            "Application/product code still exists: "
            + relative
        )
    else:
        ok(
            "No application code: "
            + relative
        )


print()
print("===== GENERATED / LOCAL ARTIFACT POLICY =====")

gitignore = (
    ROOT / ".gitignore"
).read_text(
    encoding="utf-8",
    errors="replace",
)

required_ignore_tokens = [
    "/vendor_manuals/",
    "/sessions/",
    "/captures/",
    "hardware_results",
    "docs/generated",
]

for token in required_ignore_tokens:
    if token in gitignore:
        ok(
            f".gitignore contains {token}"
        )
    else:
        warn(
            f".gitignore may be missing {token}"
        )


print()
print("===== TEST ASSETS =====")

required_tests = [
    "tests/unit/test_record_replay.py",
    "tests/unit/test_qualification_framework.py",
    "tests/unit/test_dsox3000_driver.py",
    "tests/unit/test_dsox3000_waveform.py",
    "tests/unit/test_fsw_catalogs.py",
    "tests/unit/test_fsw_driver.py",
]

for relative in required_tests:
    require_path(relative)


print()
print("===== SUMMARY =====")

print(
    "Errors:",
    len(errors),
)

print(
    "Warnings:",
    len(warnings),
)

if warnings:
    print()
    print("Warnings:")

    for item in warnings:
        print(
            " -",
            item,
        )

if errors:
    print()
    print("Baseline audit FAILED")

    for item in errors:
        print(
            " -",
            item,
        )

    sys.exit(1)

print()
print(
    "PLATFORM BASELINE STATIC AUDIT PASS"
)
