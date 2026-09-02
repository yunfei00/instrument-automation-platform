import sys
from pathlib import Path

import pytest

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


def test_dsox_operations_are_profile_scoped():
    dsox = DEFAULT_OPERATION_REGISTRY.list_for_profile("keysight/dsox3000")
    fsw = DEFAULT_OPERATION_REGISTRY.list_for_profile("rohde_schwarz/fsw")

    assert [operation.id for operation in dsox] == [
        "keysight.dsox3000.read_control_state",
        "keysight.dsox3000.set_channel",
        "keysight.dsox3000.set_timebase",
        "keysight.dsox3000.single",
        "keysight.dsox3000.stop",
        "keysight.dsox3000.snapshot_all",
    ]
    assert fsw == ()


def test_dsox_read_control_state_operation():
    transport = MockTransport()
    for response in [
        "1\n",
        "0.5\n",
        "0.1\n",
        "1e-4\n",
        "2e-6\n",
        "EDGE\n",
        "NORM\n",
        "CHAN1\n",
        "0.2\n",
        "NORM\n",
        "10000\n",
        "4e9\n",
    ]:
        transport.queue_response(response)

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.read_control_state",
        transport,
        {"channel": "1"},
    )

    assert result["kind"] == "keysight_dsox3000_control_state"
    assert result["channel_display"] is True
    assert result["channel_scale_v_div"] == 0.5
    assert result["channel_offset_v"] == 0.1
    assert result["timebase_scale_s_div"] == 1e-4
    assert result["trigger_source"] == "CHAN1"
    assert result["acquisition_points"] == 10000
    assert result["sample_rate_sps"] == 4e9

    assert transport.writes[:3] == [
        ":CHANnel1:DISPlay?",
        ":CHANnel1:SCALe?",
        ":CHANnel1:OFFSet?",
    ]


def test_dsox_setting_operations_write_only_requested_values():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.set_channel",
        transport,
        {
            "channel": "2",
            "scale_v_div": "0.25",
            "offset_v": "-0.1",
        },
    )
    assert result["setting"] == "channel"
    assert transport.writes == [
        ":CHANnel2:SCALe 0.25",
        ":CHANnel2:OFFSet -0.1",
    ]

    transport.writes.clear()
    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.set_timebase",
        transport,
        {
            "scale_s_div": "1e-5",
            "position_s": "0",
        },
    )
    assert result["setting"] == "timebase"
    assert transport.writes == [
        ":TIMebase:SCALe 1e-05",
        ":TIMebase:POSition 0.0",
    ]


def test_dsox_setting_operations_validate_empty_or_invalid_values():
    transport = MockTransport()

    with pytest.raises(ValueError, match="Enter channel scale"):
        DEFAULT_OPERATION_REGISTRY.run(
            "keysight.dsox3000.set_channel",
            transport,
            {"channel": "1", "scale_v_div": "", "offset_v": ""},
        )

    with pytest.raises(ValueError, match="greater than 0"):
        DEFAULT_OPERATION_REGISTRY.run(
            "keysight.dsox3000.set_timebase",
            transport,
            {"scale_s_div": "0"},
        )


def test_dsox_single_and_stop_operations():
    transport = MockTransport()

    single = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.single",
        transport,
    )
    stop = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.stop",
        transport,
    )

    assert single["action"] == "single"
    assert stop["action"] == "stop"
    assert transport.writes == [":SINGle", ":STOP"]


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
