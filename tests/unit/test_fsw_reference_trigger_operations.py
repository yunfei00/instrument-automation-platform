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
from instrument_lab.fsw_reference_trigger_operations import (
    ensure_fsw_reference_trigger_operations_registered,
)
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


ensure_fsw_reference_trigger_operations_registered()


def test_reference_level_read_is_explicit_and_candidate():
    transport = MockTransport()
    transport.queue_response("-20\n")

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.read_reference_level",
        transport,
        {},
    )

    assert result["reference_level_dbm"] == -20.0
    assert result["verification_status"] == "candidate"
    assert transport.writes == [
        "DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel?",
    ]


def test_reference_level_set_reads_back_without_joining_auto_state():
    transport = MockTransport()
    transport.queue_response("-15\n")

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.set_reference_level",
        transport,
        {"reference_level_dbm": -15},
    )

    assert result["setting"] == "reference_level"
    assert result["readback_dbm"] == -15.0
    assert result["verification_status"] == "candidate"
    assert transport.writes == [
        "DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel -15",
        "DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel?",
    ]


def test_trigger_source_can_return_to_immediate():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.set_trigger_source",
        transport,
        {"source": "IMMediate"},
    )

    assert result["applied"]["source"] == "IMMediate"
    assert transport.writes == ["TRIGger:SEQuence:SOURce IMMediate"]


def test_video_trigger_operation_uses_manual_verified_helper_and_readback():
    transport = MockTransport()
    for response in ["VID\n", "45.9\n", "-0.005\n", "POS\n"]:
        transport.queue_response(response)

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.configure_video_trigger",
        transport,
        {
            "level_pct": 45.9,
            "offset_s": -0.005,
            "slope": "POSitive",
        },
    )

    assert result["source"] == "VID"
    assert result["video_level_pct"] == 45.9
    assert result["trigger_offset_s"] == -0.005
    assert result["slope"] == "POS"
    assert transport.writes[:4] == [
        "TRIGger:SEQuence:SOURce VID",
        "TRIGger:SEQuence:LEVel:VIDeo 45.9 PCT",
        "TRIGger:SEQuence:HOLDoff:TIME -0.005 S",
        "TRIGger:SEQuence:SLOPe POSitive",
    ]
