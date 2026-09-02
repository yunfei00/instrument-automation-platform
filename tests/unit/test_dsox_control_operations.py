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
from instrument_lab.dsox_control_operations import (
    ensure_dsox_control_operations_registered,
)
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


ensure_dsox_control_operations_registered()


def test_channel_display_operation():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.set_channel_display",
        transport,
        {"channel": "4", "state": "OFF"},
    )

    assert result["setting"] == "channel_display"
    assert result["applied"] == {"channel": 4, "state": "OFF"}
    assert transport.writes == [":CHANnel4:DISPlay OFF"]


def test_edge_trigger_operation():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.set_edge_trigger",
        transport,
        {"sweep": "NORM", "source": "CH2", "level_v": "0.2"},
    )

    assert result["setting"] == "edge_trigger"
    assert result["applied"] == {
        "sweep": "NORM",
        "source": "CHANnel2",
        "level_v": 0.2,
    }
    assert transport.writes == [
        ":TRIGger:SWEep NORM",
        ":TRIGger:EDGE:SOURce CHANnel2",
        ":TRIGger:EDGE:LEVel 0.2,CHANnel2",
    ]


def test_edge_trigger_operation_keeps_level_when_blank():
    transport = MockTransport()

    result = DEFAULT_OPERATION_REGISTRY.run(
        "keysight.dsox3000.set_edge_trigger",
        transport,
        {"sweep": "AUTO", "source": "CH1", "level_v": ""},
    )

    assert "level_v" not in result["applied"]
    assert transport.writes == [
        ":TRIGger:SWEep AUTO",
        ":TRIGger:EDGE:SOURce CHANnel1",
    ]
