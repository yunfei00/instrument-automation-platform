import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in ["instrument_core", "instrument_scpi", "instrument_drivers"]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core.transport import MockTransport
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
    marker_peak_search,
    set_sweep_time_s,
)


def test_set_sweep_time_uses_manual_verified_command():
    transport = MockTransport()
    driver = RohdeSchwarzFSWDriver(transport)

    result = set_sweep_time_s(driver, 0.002)

    assert result == 0.002
    assert transport.writes == ["SENSe:SWEep:TIME 0.002"]


def test_set_sweep_time_rejects_non_positive_value():
    transport = MockTransport()
    driver = RohdeSchwarzFSWDriver(transport)

    try:
        set_sweep_time_s(driver, 0)
    except ValueError as exc:
        assert "greater than 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-positive sweep time")


def test_marker_peak_search_uses_only_verified_marker_commands():
    transport = MockTransport()
    transport.queue_response("-42.25")
    driver = RohdeSchwarzFSWDriver(transport)

    level = marker_peak_search(driver)

    assert level == -42.25
    assert transport.writes == [
        "CALCulate1:MARKer1:MAXimum:PEAK",
        "CALCulate1:MARKer1:Y?",
    ]
