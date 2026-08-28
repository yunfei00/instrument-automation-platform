from __future__ import annotations

from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_port_bridge_launcher_exposes_baseline_packages() -> None:
    launcher = ROOT / "tools" / "instrument_port_bridge.py"
    runpy.run_path(str(launcher), run_name="instrument_port_bridge_launcher_test")

    import instrument_core  # noqa: F401
    import instrument_scpi  # noqa: F401
    import instrument_lab  # noqa: F401
    import instrument_drivers  # noqa: F401
    import instrument_qualification  # noqa: F401

    expected_paths = {
        str(ROOT / "packages" / package / "src")
        for package in (
            "instrument_core",
            "instrument_scpi",
            "instrument_lab",
            "instrument_drivers",
            "instrument_qualification",
        )
    }
    assert expected_paths.issubset(set(sys.path))
