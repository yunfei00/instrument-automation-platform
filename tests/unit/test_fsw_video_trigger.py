import sys
from pathlib import Path

import pytest


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

from instrument_core.transport import MockTransport
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
    configure_video_trigger,
    get_trigger_offset_s,
    get_trigger_slope,
    get_video_trigger_level_pct,
    set_trigger_offset_s,
    set_trigger_slope,
    set_video_trigger_level_pct,
)


def _driver():
    transport = MockTransport()
    return transport, RohdeSchwarzFSWDriver(transport)


def test_video_trigger_level_query_set_and_validation():
    transport, driver = _driver()
    transport.queue_response("45.9\n")

    assert get_video_trigger_level_pct(driver) == 45.9
    assert transport.writes[-1] == "TRIGger:SEQuence:LEVel:VIDeo?"

    set_video_trigger_level_pct(driver, 45.9)
    assert transport.writes[-1] == "TRIGger:SEQuence:LEVel:VIDeo 45.9 PCT"

    with pytest.raises(ValueError):
        set_video_trigger_level_pct(driver, -0.1)
    with pytest.raises(ValueError):
        set_video_trigger_level_pct(driver, 100.1)


def test_trigger_offset_allows_negative_pretrigger():
    transport, driver = _driver()
    transport.queue_response("-5.000000E-03\n")

    assert get_trigger_offset_s(driver) == -0.005
    assert transport.writes[-1] == "TRIGger:SEQuence:HOLDoff:TIME?"

    set_trigger_offset_s(driver, -0.005)
    assert transport.writes[-1] == "TRIGger:SEQuence:HOLDoff:TIME -0.005 S"


def test_trigger_slope_query_set_and_validation():
    transport, driver = _driver()
    transport.queue_response("POS\n")

    assert get_trigger_slope(driver) == "POS"
    set_trigger_slope(driver, "negative")
    assert transport.writes[-1] == "TRIGger:SEQuence:SLOPe NEGative"

    with pytest.raises(ValueError):
        set_trigger_slope(driver, "both")


def test_configure_video_trigger_returns_readback():
    transport, driver = _driver()
    transport.queue_response("VID\n")
    transport.queue_response("45.9\n")
    transport.queue_response("-0.005\n")
    transport.queue_response("POS\n")

    result = configure_video_trigger(
        driver,
        level_pct=45.9,
        offset_s=-0.005,
    )

    assert result == {
        "source": "VID",
        "video_level_pct": 45.9,
        "trigger_offset_s": -0.005,
        "slope": "POS",
    }
    assert transport.writes[:3] == [
        "TRIGger:SEQuence:SOURce VID",
        "TRIGger:SEQuence:LEVel:VIDeo 45.9 PCT",
        "TRIGger:SEQuence:HOLDoff:TIME -0.005 S",
    ]


def test_video_trigger_composes_with_existing_single_trace_arm():
    transport, driver = _driver()

    driver.set_trigger_source("VID")
    set_video_trigger_level_pct(driver, 45.9)
    set_trigger_offset_s(driver, -0.005)
    driver.arm_trace_ascii(channel=1)

    assert transport.writes == [
        "TRIGger:SEQuence:SOURce VID",
        "TRIGger:SEQuence:LEVel:VIDeo 45.9 PCT",
        "TRIGger:SEQuence:HOLDoff:TIME -0.005 S",
        "INITiate1:CONTinuous OFF",
        "FORMat:DATA ASCii",
        "INITiate1:IMMediate",
    ]
