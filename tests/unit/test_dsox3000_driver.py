import sys
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


if __name__ == "__main__":
    main()
