import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "instrument_lab" / "src"))

from instrument_lab.units import (
    FREQUENCY_UNITS,
    TIME_UNITS,
    best_unit,
    from_base,
    to_base,
)


def test_frequency_units_round_trip():
    assert to_base(800, "MHz", FREQUENCY_UNITS) == 800e6
    assert from_base(800e6, "MHz", FREQUENCY_UNITS) == 800
    assert to_base(2.5, "GHz", FREQUENCY_UNITS) == 2.5e9
    assert to_base(100, "kHz", FREQUENCY_UNITS) == 100e3


def test_best_frequency_unit_prefers_readable_engineering_scale():
    assert best_unit(2.4e9, FREQUENCY_UNITS) == "GHz"
    assert best_unit(800e6, FREQUENCY_UNITS) == "MHz"
    assert best_unit(100e3, FREQUENCY_UNITS) == "kHz"
    assert best_unit(100, FREQUENCY_UNITS) == "Hz"
    assert best_unit(0, FREQUENCY_UNITS, zero_unit="MHz") == "MHz"


def test_time_units_round_trip_and_auto_selection():
    assert to_base(2, "ms", TIME_UNITS) == 0.002
    assert from_base(0.002, "ms", TIME_UNITS) == 2
    assert best_unit(0.002, TIME_UNITS) == "ms"
    assert best_unit(5e-6, TIME_UNITS) == "us"
    assert best_unit(20e-9, TIME_UNITS) == "ns"
