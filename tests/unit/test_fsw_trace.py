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
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
    build_frequency_axis,
    parse_ascii_trace,
)


def main():
    levels = parse_ascii_trace(
        "-80,-70,-60"
    )

    assert levels == (
        -80.0,
        -70.0,
        -60.0,
    )

    axis = build_frequency_axis(
        100e6,
        200e6,
        3,
    )

    assert axis == (
        100e6,
        150e6,
        200e6,
    )

    transport = MockTransport()

    driver = RohdeSchwarzFSWDriver(
        transport
    )

    transport.queue_response(
        "Rohde&Schwarz,"
        "FSW,"
        "123456,"
        "6.30\n"
    )

    driver.connect()

    # *OPC?
    transport.queue_response(
        "1\n"
    )

    # start frequency
    transport.queue_response(
        "100000000\n"
    )

    # stop frequency
    transport.queue_response(
        "200000000\n"
    )

    # TRACE1 data
    transport.queue_response(
        "-80,-70,-60\n"
    )

    spectrum = (
        driver.acquire_trace_ascii(
            channel=1,
            window=1,
            trace=1,
        )
    )

    assert spectrum.points == 3

    assert (
        spectrum.frequencies_hz
        == (
            100e6,
            150e6,
            200e6,
        )
    )

    assert spectrum.levels == (
        -80.0,
        -70.0,
        -60.0,
    )

    assert (
        spectrum.peak_frequency_hz
        == 200e6
    )

    assert (
        spectrum.peak_level
        == -60.0
    )

    required_writes = [
        "INITiate1:CONTinuous OFF",
        "FORMat:DATA ASCii",
        "INITiate1:IMMediate",
        "*OPC?",
        "SENSe:FREQuency:STARt?",
        "SENSe:FREQuency:STOP?",
        "TRACe1:DATA? TRACE1",
    ]

    for command in required_writes:
        assert command in transport.writes

    driver.disconnect()

    print(
        "FSW trace scenario PASS"
    )


if __name__ == "__main__":
    main()
