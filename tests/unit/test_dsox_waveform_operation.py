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
from instrument_lab.dsox_waveform_operation import (
    WaveformOperationResult,
    ensure_dsox_waveform_operation_registered,
)
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


def _waveform_transport() -> MockTransport:
    transport = MockTransport()
    for response in [
        "1\n",  # *OPC? after STOP
        "0\n",  # clear stale :AER?
        "1\n",  # newly armed
        "0\n",  # operation condition: stopped
        "1,0,2,1,1e-9,0,0,1e-3,0,0\n",  # waveform preamble
        "LSBF\n",
        "0\n",
    ]:
        transport.queue_response(response)
    transport.queue_raw_response(b"#14\x01\x00\x02\x00\n")
    return transport


def test_single_waveform_operation_returns_plot_ready_data():
    ensure_dsox_waveform_operation_registered()
    transport = _waveform_transport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.single_waveform",
        transport,
        {"channel": "1", "timeout_s": 1.0},
    )

    assert isinstance(result, WaveformOperationResult)
    assert result["kind"] == "keysight_dsox3000_single_waveform"
    assert result["source"] == "CHANnel1"
    assert result["point_count"] == 2
    assert result["time_seconds"] == (0.0, 1e-9)
    assert result["voltage_volts"] == (0.001, 0.002)
    assert result["voltage_min_v"] == 0.001
    assert result["voltage_max_v"] == 0.002

    assert ":STOP" in transport.writes
    assert ":SINGle" in transport.writes
    assert ":WAVeform:DATA?" in transport.writes
    assert not any(command.upper().startswith(":DIGITIZE") for command in transport.writes)


def test_waveform_arrays_do_not_expand_through_dict_items():
    result = WaveformOperationResult(
        {"kind": "waveform", "point_count": 3},
        (0.0, 1.0, 2.0),
        (3.0, 4.0, 5.0),
    )

    assert result.get("time_seconds") == (0.0, 1.0, 2.0)
    assert result.get("voltage_volts") == (3.0, 4.0, 5.0)
    assert "time_seconds" not in dict(result.items())
    assert "voltage_volts" not in dict(result.items())
