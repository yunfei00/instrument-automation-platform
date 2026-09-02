import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
]:
    sys.path.insert(
        0,
        str(ROOT / "packages" / package / "src"),
    )

from instrument_drivers.keysight.dsox3000 import (
    SNAPSHOT_ALL_MEASUREMENTS,
    parse_snapshot_value,
    read_snapshot_all,
)


class FakeSnapshotDriver:
    def __init__(self, responses=None):
        self.writes = []
        self.queries = []
        self.responses = dict(responses or {})

    def write(self, command):
        self.writes.append(command)

    def query(self, command):
        self.queries.append(command)
        return self.responses.get(command, "1.25")


def test_snapshot_all_has_31_measurements_and_installs_front_panel_snapshot():
    driver = FakeSnapshotDriver()

    result = read_snapshot_all(driver, 1)

    assert len(SNAPSHOT_ALL_MEASUREMENTS) == 31
    assert result["measurement_count"] == 31
    assert result["successful_measurements"] == 31
    assert result["failed_or_invalid_measurements"] == 0
    assert result["unread_measurements"] == 0
    assert result["collection_complete"] is True
    assert result["source"] == "CHANnel1"
    assert driver.writes == [
        ":MEASure:SOURce CHANnel1",
        ":MEASure:ALL",
    ]
    assert len(driver.queries) == 31
    assert driver.queries[0] == ":MEASure:VPP? CHANnel1"
    assert driver.queries[-1] == ":MEASure:AREa? DISPlay,CHANnel1"


def test_snapshot_all_preserves_invalid_scope_sentinel():
    driver = FakeSnapshotDriver(
        {":MEASure:VPP? CHANnel2": "9.9E+37"}
    )

    result = read_snapshot_all(driver, 2)
    vpp = result["measurements"]["peak_to_peak"]

    assert vpp["raw"] == "9.9E+37"
    assert vpp["value"] is None
    assert vpp["valid"] is False
    assert result["successful_measurements"] == 30
    assert result["failed_or_invalid_measurements"] == 1
    assert result["collection_complete"] is True


def test_snapshot_all_can_stop_cooperatively_between_queries():
    driver = FakeSnapshotDriver()
    checks = 0

    def cancel_check():
        nonlocal checks
        checks += 1
        return checks > 3

    result = read_snapshot_all(driver, 3, cancel_check=cancel_check)

    assert len(driver.queries) == 3
    assert result["collection_complete"] is False
    assert result["stop_reason"] == "canceled"
    assert result["unread_measurements"] == 28


def test_snapshot_all_can_query_without_installing_snapshot_display():
    driver = FakeSnapshotDriver()

    result = read_snapshot_all(driver, 4, install_snapshot=False)

    assert driver.writes == []
    assert result["install_command"] is None
    assert result["collection_complete"] is True


def test_snapshot_value_parser_handles_numeric_and_invalid_values():
    assert parse_snapshot_value("1.5") == (1.5, True)
    assert parse_snapshot_value("INF") == (None, False)
    assert parse_snapshot_value("not-a-number") == (None, False)


def test_snapshot_all_rejects_non_analog_channel():
    driver = FakeSnapshotDriver()
    try:
        read_snapshot_all(driver, 5)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid Snapshot All channel was accepted")
