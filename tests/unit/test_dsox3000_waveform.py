import struct
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
    WaveformPreamble,
    build_waveform,
    decode_word_samples,
)


def test_preamble():
    preamble = WaveformPreamble.parse(
        "1,0,4,1,"
        "1.0E-6,0,0,"
        "1.0E-3,0,0"
    )

    assert preamble.points == 4
    assert preamble.x_increment == 1e-6
    assert preamble.y_increment == 1e-3


def test_decode():
    payload = struct.pack(
        "<4h",
        0,
        100,
        -100,
        200,
    )

    samples = decode_word_samples(
        payload,
        byte_order="LSBFirst",
        unsigned=False,
    )

    assert samples == (
        0,
        100,
        -100,
        200,
    )


def test_conversion():
    preamble = WaveformPreamble(
        format=1,
        acquisition_type=0,
        points=3,
        count=1,
        x_increment=1e-6,
        x_origin=0.0,
        x_reference=0.0,
        y_increment=1e-3,
        y_origin=0.0,
        y_reference=0.0,
    )

    waveform = build_waveform(
        (0, 100, -100),
        preamble,
    )

    assert waveform.time_seconds == (
        0.0,
        1e-6,
        2e-6,
    )

    assert waveform.voltage_volts == (
        0.0,
        0.1,
        -0.1,
    )


def test_complete_scenario():
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

    driver.connect()

    transport.queue_response(
        "1,0,4,1,"
        "1.0E-6,0,0,"
        "1.0E-3,0,0\n"
    )

    transport.queue_response(
        "LSBFirst\n"
    )

    transport.queue_response(
        "0\n"
    )

    payload = struct.pack(
        "<4h",
        0,
        100,
        -100,
        200,
    )

    header = (
        b"#1"
        + str(len(payload)).encode()
    )

    transport.queue_raw_response(
        header
        + payload
        + b"\n"
    )

    waveform = (
        driver.acquire_word_waveform(1)
    )

    assert (
        waveform.raw_samples
        == (
            0,
            100,
            -100,
            200,
        )
    )

    assert len(
        waveform.time_seconds
    ) == 4

    assert len(
        waveform.voltage_volts
    ) == 4

    assert (
        ":WAVeform:SOURce CHANnel1"
        in transport.writes
    )

    assert (
        ":WAVeform:FORMat WORD"
        in transport.writes
    )

    assert (
        ":DIGitize CHANnel1"
        in transport.writes
    )

    assert (
        ":WAVeform:PREamble?"
        in transport.writes
    )

    assert (
        ":WAVeform:DATA?"
        in transport.writes
    )

    driver.disconnect()


def main():
    test_preamble()
    test_decode()
    test_conversion()
    test_complete_scenario()

    print(
        "DSOX3000 waveform scenario PASS"
    )


if __name__ == "__main__":
    main()
