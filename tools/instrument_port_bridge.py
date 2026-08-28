#!/usr/bin/env python3
"""Launch Instrument Port Bridge from a repository checkout."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

# Keep repository-checkout execution consistent with Instrument Lab GUI.
# Importing ``instrument_lab.port_bridge_gui`` first initializes the
# ``instrument_lab`` package, whose public API currently imports SCPI probing
# helpers.  Therefore all baseline packages that may be reached during package
# initialization must be visible on sys.path, even when the bridge itself only
# needs a subset of them.
for package in (
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
    "instrument_qualification",
):
    source = ROOT / "packages" / package / "src"
    if source.is_dir():
        sys.path.insert(0, str(source))


def main() -> int:
    try:
        from instrument_lab.port_bridge_gui import run_port_bridge_gui
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            print(
                "PySide6 is required for Instrument Port Bridge.\n"
                "Install GUI dependencies with:\n\n"
                "    python -m pip install -r requirements-gui.txt\n",
                file=sys.stderr,
            )
            return 2
        raise

    return run_port_bridge_gui()


if __name__ == "__main__":
    raise SystemExit(main())
