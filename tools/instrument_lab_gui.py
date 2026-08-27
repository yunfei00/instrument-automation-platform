#!/usr/bin/env python3
"""Launch Instrument Lab GUI from a repository checkout."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Instrument Automation Platform engineering GUI"
    )
    parser.add_argument(
        "--repo-root",
        default=str(ROOT),
        help="Repository root containing instrument_profiles",
    )
    args = parser.parse_args()

    try:
        from instrument_lab.gui import run_gui
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            print(
                "PySide6 is required for Instrument Lab GUI.\n"
                "Install GUI dependencies with:\n\n"
                "    python -m pip install -r requirements-gui.txt\n",
                file=sys.stderr,
            )
            return 2
        raise

    return run_gui(repo_root=args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
