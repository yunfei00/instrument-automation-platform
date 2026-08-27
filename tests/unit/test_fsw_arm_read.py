import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core.transport import MockTransport
from instrument_drivers.rohde_schwarz.fsw import RohdeSchwarzFSWDriver


def make_driver():
    transport = MockTransport()
    driver = RohdeSchwarzFSWDriver(transport)
    transport.queue_response("Rohde&Schwarz,FSW-26,123456,6.00\n")
    driver.connect()
    return driver, transport


def test_arm_trace_does_not_wait_or_read():
    driver, transport = make_driver()

    driver.arm_trace_ascii(channel=1)

    assert transport.writes[-3:] == [
        "INITiate1:CONTinuous OFF",
        "FORMat:DATA ASCii",
        "INITiate1:IMMediate",
    ]
    assert "*OPC?" not in transport.writes
    assert "TRACe1:DATA? TRACE1" not in transport.writes


def test_wait_and_read_completes_previously_armed_trace():
    driver, transport = make_driver()
    driver.arm_trace_ascii(channel=1)

    # bounded wait: clear stale ESR, then one completion poll
    transport.queue_response("0\n")
    transport.queue_response("1\n")
    transport.queue_response("500000000\n")
    transport.queue_response("700000000\n")
    transport.queue_response("-80,-60,-70\n")

    result = driver.wait_and_read_trace_ascii(
        timeout_s=1.0,
        poll_interval_s=0.001,
    )

    assert result.frequencies_hz == (500e6, 600e6, 700e6)
    assert result.levels == (-80.0, -60.0, -70.0)
    assert "*OPC" in transport.writes
    assert "*OPC?" not in transport.writes
    assert transport.writes.index("INITiate1:IMMediate") < transport.writes.index("*OPC")


def test_read_completed_trace_does_not_rearm():
    driver, transport = make_driver()
    transport.queue_response("500000000\n")
    transport.queue_response("700000000\n")
    transport.queue_response("-80,-60,-70\n")

    result = driver.read_completed_trace_ascii()

    assert result.points == 3
    assert "INITiate1:IMMediate" not in transport.writes
