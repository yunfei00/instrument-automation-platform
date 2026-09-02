import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core.transport import MockTransport
from instrument_drivers.keysight.dsox3000 import (
    KeysightDSOX3000Driver,
    normalize_edge_trigger_source,
    set_channel_display,
    set_edge_trigger,
)


def test_channel_display_helper_writes_selected_channel_state():
    transport = MockTransport()
    driver = KeysightDSOX3000Driver(transport)

    set_channel_display(driver, 2, True)
    set_channel_display(driver, 2, False)

    assert transport.writes == [
        ":CHANnel2:DISPlay ON",
        ":CHANnel2:DISPlay OFF",
    ]


def test_edge_trigger_helper_applies_sweep_source_and_level():
    transport = MockTransport()
    driver = KeysightDSOX3000Driver(transport)

    applied = set_edge_trigger(
        driver,
        sweep="norm",
        source="ch3",
        level_v=0.125,
    )

    assert applied == {
        "sweep": "NORM",
        "source": "CHANnel3",
        "level_v": 0.125,
    }
    assert transport.writes == [
        ":TRIGger:SWEep NORM",
        ":TRIGger:EDGE:SOURce CHANnel3",
        ":TRIGger:EDGE:LEVel 0.125,CHANnel3",
    ]


def test_edge_trigger_level_can_be_left_unchanged():
    transport = MockTransport()
    driver = KeysightDSOX3000Driver(transport)

    applied = set_edge_trigger(
        driver,
        sweep="AUTO",
        source=1,
    )

    assert applied == {"sweep": "AUTO", "source": "CHANnel1"}
    assert transport.writes == [
        ":TRIGger:SWEep AUTO",
        ":TRIGger:EDGE:SOURce CHANnel1",
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CH1", "CHANnel1"),
        ("CHAN2", "CHANnel2"),
        ("CHANNEL3", "CHANnel3"),
        (4, "CHANnel4"),
    ],
)
def test_trigger_source_aliases(raw, expected):
    assert normalize_edge_trigger_source(raw) == expected


def test_control_helpers_reject_invalid_values():
    transport = MockTransport()
    driver = KeysightDSOX3000Driver(transport)

    with pytest.raises(ValueError, match="channel"):
        set_channel_display(driver, 5, True)

    with pytest.raises(ValueError, match="source"):
        set_edge_trigger(driver, sweep="AUTO", source="EXT")

    with pytest.raises(ValueError, match="sweep"):
        set_edge_trigger(driver, sweep="SINGLE", source="CH1")
