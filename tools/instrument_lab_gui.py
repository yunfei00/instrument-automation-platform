#!/usr/bin/env python3
"""Launch Instrument Automation Studio from a repository checkout."""

from __future__ import annotations

import argparse
import faulthandler
from importlib import metadata
from pathlib import Path
import platform
import sys


# Native Qt/VISA faults do not become normal Python exceptions. Keep Python
# fatal-signal diagnostics enabled so a terminal run can still provide useful
# thread stacks when a vendor library crashes the process.
faulthandler.enable(all_threads=True)


ROOT = Path(__file__).resolve().parents[1]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
    "instrument_qualification",
]:
    source = ROOT / "packages" / package / "src"
    if source.is_dir():
        sys.path.insert(0, str(source))


def _package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def print_diagnostics() -> None:
    """Print environment details without opening an instrument session."""

    print("Instrument Automation Studio diagnostics")
    print(f"Python       : {sys.version.split()[0]}")
    print(f"Executable   : {sys.executable}")
    print(f"Platform     : {platform.platform()}")
    print(f"Machine      : {platform.machine()}")
    print(f"PySide6      : {_package_version('PySide6')}")
    print(f"PyVISA       : {_package_version('PyVISA')}")
    print(f"PyVISA-py    : {_package_version('PyVISA-py')}")
    print(f"Repo root    : {ROOT}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Instrument Automation Platform control and engineering GUI"
    )
    parser.add_argument(
        "--repo-root",
        default=str(ROOT),
        help="Repository root containing instrument_profiles",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Print Python/Qt/VISA package versions and exit",
    )
    args = parser.parse_args()

    if args.diagnostics:
        print_diagnostics()
        return 0

    try:
        from instrument_lab.gui_control import run_gui
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            print(
                "PySide6 is required for Instrument Automation Studio.\n"
                "Install GUI dependencies with:\n\n"
                "    python -m pip install -r requirements-gui.txt\n",
                file=sys.stderr,
            )
            return 2
        raise

    return run_gui(repo_root=args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
