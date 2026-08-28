#!/usr/bin/env python3
"""Launch Instrument Port Bridge from a repository checkout or frozen EXE."""

from __future__ import annotations

import argparse
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parents[1]

# Keep repository-checkout execution consistent with Instrument Lab GUI.
# Frozen PyInstaller builds already contain their Python modules, so package
# source paths only need to be injected for a normal repository checkout.
if not getattr(sys, "frozen", False):
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


def _write_diagnostics(lines: list[str], output_path: str | None) -> None:
    text = "\n".join(lines) + "\n"
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        return

    # PyInstaller --windowed applications on Windows have no console and may
    # expose stdout as None.  Diagnostics must therefore remain safe even when
    # no terminal is attached.
    if sys.stdout is not None:
        sys.stdout.write(text)
        sys.stdout.flush()


def run_diagnostics(output_path: str | None = None) -> int:
    """Import runtime dependencies without touching a real instrument."""

    try:
        import PySide6
        import pyvisa
        import pyvisa_py
        import instrument_core
        import instrument_scpi
        from instrument_core.bridge import TcpBridgeServer, VisaBridgeServer
        from instrument_lab.port_bridge_gui import PortBridgeWindow

        lines = [
            "Instrument Port Bridge diagnostics",
            "status=ok",
            f"python={platform.python_version()}",
            f"platform={platform.platform()}",
            f"frozen={bool(getattr(sys, 'frozen', False))}",
            f"pyside6={getattr(PySide6, '__version__', 'unknown')}",
            f"pyvisa={getattr(pyvisa, '__version__', 'unknown')}",
            f"pyvisa_py={getattr(pyvisa_py, '__version__', 'available')}",
            f"instrument_core={instrument_core.__name__}",
            f"instrument_scpi={instrument_scpi.__name__}",
            f"tcp_bridge={TcpBridgeServer.__name__}",
            f"visa_bridge={VisaBridgeServer.__name__}",
            f"gui={PortBridgeWindow.__name__}",
        ]
        _write_diagnostics(lines, output_path)
        return 0
    except Exception as exc:
        _write_diagnostics(
            [
                "Instrument Port Bridge diagnostics",
                "status=failed",
                f"error={type(exc).__name__}: {exc}",
            ],
            output_path,
        )
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Instrument Port Bridge / 仪表端口桥接工具"
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Import packaged runtime dependencies and exit",
    )
    parser.add_argument(
        "--diagnostics-file",
        default=None,
        help="Write diagnostics to this UTF-8 text file",
    )
    args = parser.parse_args()

    if args.diagnostics or args.diagnostics_file:
        return run_diagnostics(args.diagnostics_file)

    try:
        from instrument_lab.port_bridge_gui import run_port_bridge_gui
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            message = (
                "PySide6 is required for Instrument Port Bridge.\n"
                "Install GUI dependencies with:\n\n"
                "    python -m pip install -r requirements-gui.txt\n"
            )
            if sys.stderr is not None:
                print(message, file=sys.stderr)
            return 2
        raise

    return run_port_bridge_gui()


if __name__ == "__main__":
    raise SystemExit(main())
