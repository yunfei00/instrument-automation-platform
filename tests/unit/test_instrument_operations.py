import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core.transport import MockTransport
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


def test_dsox_snapshot_operation_is_profile_scoped():
    dsox = DEFAULT_OPERATION_REGISTRY.list_for_profile("keysight/dsox3000")
    fsw = DEFAULT_OPERATION_REGISTRY.list_for_profile("rohde_schwarz/fsw")

    assert [operation.id for operation in dsox] == [
        "keysight.dsox3000.snapshot_all"
    ]
    assert fsw == ()


def test_dsox_snapshot_operation_runs_composite_sequence():
    transport = MockTransport()
    for _ in range(31):
        transport.queue_response("1\n")

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.snapshot_all",
        transport,
        {"channel": "2"},
    )

    assert result["source"] == "CHANnel2"
    assert result["measurement_count"] == 31
    assert result["successful_measurements"] == 31
    assert result["collection_complete"] is True

    assert transport.writes[0] == ":MEASure:SOURce CHANnel2"
    assert transport.writes[1] == ":MEASure:ALL"
    assert ":MEASure:VPP? CHANnel2" in transport.writes
    assert ":MEASure:FREQuency? CHANnel2" in transport.writes
