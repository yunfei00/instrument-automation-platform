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
from instrument_lab.fsw_operations import ensure_fsw_operations_registered
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


ensure_fsw_operations_registered()


def test_fsw_center_span_operation_uses_driver_api():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.set_center_span",
        transport,
        {"center_hz": "750e6", "span_hz": "100e6"},
    )

    assert result["setting"] == "center_span"
    assert result["applied"] == {
        "center_hz": 750e6,
        "span_hz": 100e6,
    }
    assert transport.writes == [
        "SENSe:FREQuency:CENTer 750000000.0",
        "SENSe:FREQuency:SPAN 100000000.0",
    ]


def test_fsw_input_operation_keeps_hardware_verified_manual_attenuation_sequence():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.set_input",
        transport,
        {
            "attenuation_mode": "MANUAL",
            "attenuation_db": "2",
            "preamp_db": "0",
        },
    )

    assert result["setting"] == "input"
    assert transport.writes == [
        "INPut:ATTenuation:AUTO OFF",
        "INPut:ATTenuation 2 DB",
        "INPut:GAIN:STATe OFF",
    ]


def test_fsw_read_control_state_avoids_candidate_reference_level_query():
    transport = MockTransport()
    for response in [
        "750000000",
        "100000000",
        "700000000",
        "800000000",
        "100000",
        "300000",
        "0.01",
        "IMMediate",
        "1",
        "0",
        "2",
        "1",
        "15",
    ]:
        transport.queue_response(response)

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.read_control_state",
        transport,
        {},
    )

    assert result["center_hz"] == 750e6
    assert result["rbw_hz"] == 100000.0
    assert result["continuous"] is True
    assert result["rf_attenuation_auto"] is False
    assert result["rf_attenuation_db"] == 2.0
    assert result["preamp_db"] == 15
    assert not any("RLEVel" in command for command in transport.writes)


def test_fsw_single_trace_uses_bounded_completion_and_builds_axis():
    transport = MockTransport()
    for response in [
        "0",
        "1",
        "100",
        "200",
        "-10,-5,-12",
    ]:
        transport.queue_response(response)

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.single_trace",
        transport,
        {"timeout_s": 1},
    )

    assert result["points"] == 3
    assert result["frequencies_hz"] == (100.0, 150.0, 200.0)
    assert result["levels_dbm"] == (-10.0, -5.0, -12.0)
    assert result["peak_frequency_hz"] == 150.0
    assert result["peak_level_dbm"] == -5.0
    assert transport.writes[:4] == [
        "INITiate1:CONTinuous OFF",
        "FORMat:DATA ASCii",
        "INITiate1:IMMediate",
        "*ESR?",
    ]
    assert "*OPC" in transport.writes
