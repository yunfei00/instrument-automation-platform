import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
]:
    sys.path.insert(
        0,
        str(
            ROOT
            / "packages"
            / package
            / "src"
        ),
    )


from instrument_core.transport import (
    MockTransport,
)
from instrument_drivers.keysight.dsox3000 import (
    KeysightDSOX3000Driver,
)


def main():
    transport = MockTransport()

    driver = KeysightDSOX3000Driver(
        transport
    )

    transport.queue_response(
        "KEYSIGHT TECHNOLOGIES,"
        "DSO-X 3034A,"
        "MY123456,"
        "02.50\n"
    )

    identity = driver.connect()

    assert identity.model == (
        "DSO-X 3034A"
    )

    transport.queue_response(
        "5.000000E-01\n"
    )

    assert (
        driver.get_channel_scale(1)
        == 0.5
    )

    transport.queue_response(
        "1.000000E-04\n"
    )

    assert (
        driver.get_timebase_scale()
        == 0.0001
    )

    transport.queue_response(
        "EDGE\n"
    )

    assert (
        driver.get_trigger_mode()
        == "EDGE"
    )

    transport.queue_response(
        "CHAN1\n"
    )

    assert (
        driver.get_trigger_source()
        == "CHAN1"
    )

    transport.queue_response(
        "NORM\n"
    )

    assert (
        driver.get_acquisition_type()
        == "NORM"
    )

    transport.queue_response(
        "10000\n"
    )

    assert (
        driver.get_acquisition_points()
        == 10000
    )

    transport.queue_response(
        "WORD\n"
    )

    assert (
        driver.get_waveform_format()
        == "WORD"
    )

    transport.queue_response(
        "1,0,10000,1,"
        "1.0E-9,0,0,"
        "1.0E-3,0,0\n"
    )

    preamble = (
        driver.get_waveform_preamble()
    )

    assert len(preamble) == 10

    driver.set_timebase_scale(
        1e-4
    )

    assert (
        transport.writes[-1]
        == ":TIMebase:SCALe 0.0001"
    )

    driver.set_waveform_source(
        1
    )

    assert (
        transport.writes[-1]
        == ":WAVeform:SOURce CHANnel1"
    )

    driver.set_waveform_format(
        "WORD"
    )

    assert (
        transport.writes[-1]
        == ":WAVeform:FORMat WORD"
    )

    driver.digitize(
        1
    )

    assert (
        transport.writes[-1]
        == ":DIGitize CHANnel1"
    )

    try:
        driver.get_channel_scale(
            5
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid channel was accepted"
        )

    driver.disconnect()

    print(
        "DSOX3000 driver self-test PASS"
    )


def test_delay_and_n_pulses_measurements():
    transport = MockTransport()

    driver = KeysightDSOX3000Driver(
        transport
    )

    transport.queue_response(
        "1.250000E-06\n"
    )

    delay = driver.measure_delay()

    assert delay == 1.25e-6

    assert (
        transport.writes[-1]
        == ":MEASure:DELay?"
    )

    transport.queue_response(
        "12\n"
    )

    pulse_count = (
        driver.measure_n_pulses()
    )

    assert pulse_count == 12.0

    assert (
        transport.writes[-1]
        == ":MEASure:NPUlSes?"
    )


def test_define_delay_command():
    transport = MockTransport()

    driver = KeysightDSOX3000Driver(
        transport
    )

    driver.define_delay(
        "+1",
        "-1",
    )

    assert (
        transport.writes[-1]
        == ":MEASure:DEFine DELay,+1,-1"
    )

    driver.define_delay(
        "+2",
        "+3",
        "CHANnel1",
    )

    assert (
        transport.writes[-1]
        == ":MEASure:DEFine DELay,+2,+3,CHANnel1"
    )


def test_measure_delay_with_sources():
    transport = MockTransport()

    driver = KeysightDSOX3000Driver(
        transport
    )

    transport.queue_response(
        "2.500000E-06\n"
    )

    value = driver.measure_delay(
        "CHANnel1",
        "CHANnel2",
    )

    assert value == 2.5e-6

    assert (
        transport.writes[-1]
        == ":MEASure:DELay? CHANnel1,CHANnel2"
    )


def test_delay_validation():
    transport = MockTransport()

    driver = KeysightDSOX3000Driver(
        transport
    )

    driver.define_delay(
        "1",
        "2",
    )

    assert (
        transport.writes[-1]
        == ":MEASure:DEFine DELay,1,2"
    )

    invalid_edges = (
        "",
        "+0",
        "-0",
        "+abc",
    )

    for edge in invalid_edges:
        with pytest.raises(ValueError):
            driver.define_delay(
                edge,
                "+1",
            )

    with pytest.raises(ValueError):
        driver.define_delay(
            "+1",
            "BAD",
        )

    with pytest.raises(
        ValueError,
        match="source1 is required",
    ):
        driver.measure_delay(
            source2="CHANnel2",
        )


if __name__ == "__main__":
    main()
