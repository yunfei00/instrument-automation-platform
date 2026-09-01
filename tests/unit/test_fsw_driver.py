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
)


def main():
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

    identity = driver.connect()

    assert identity.model == "FSW"

    transport.queue_response(
        "1.000000E+09\n"
    )

    assert (
        driver.get_center_frequency()
        == 1e9
    )

    driver.set_center_frequency(
        2e9
    )

    assert (
        transport.writes[-1]
        == "SENSe:FREQuency:CENTer 2000000000.0"
    )

    transport.queue_response(
        "1.000000E+06\n"
    )

    assert driver.get_rbw() == 1e6

    transport.queue_response(
        "3.000000E+06\n"
    )

    assert driver.get_vbw() == 3e6

    transport.queue_response(
        "EXT\n"
    )

    assert (
        driver.get_trigger_source()
        == "EXT"
    )

    transport.queue_response(
        "0\n"
    )

    assert (
        driver.get_continuous(1)
        is False
    )

    driver.set_continuous(
        False,
        channel=1,
    )

    assert (
        transport.writes[-1]
        == "INITiate1:CONTinuous OFF"
    )

    transport.queue_response(
        "ASC,0\n"
    )

    assert (
        driver.get_trace_format()
        == "ASC,0"
    )

    # Preamp: target hardware has verified Off / 15 dB / 30 dB.
    transport.queue_response("1\n")
    assert driver.get_preamp_enabled() is True

    transport.queue_response("15\n")
    assert driver.get_preamp_gain_db() == 15

    transport.queue_response("1\n")
    transport.queue_response("30\n")
    assert driver.get_preamp_db() == 30

    driver.set_preamp_db(0)
    assert transport.writes[-1] == "INPut:GAIN:STATe OFF"

    driver.set_preamp_db(15)
    assert transport.writes[-2:] == [
        "INPut:GAIN:STATe ON",
        "INPut:GAIN:VALue 15",
    ]

    # RF Atten Manual: target hardware accepted 2 dB and returned 2.
    transport.queue_response("0\n")
    assert driver.get_rf_attenuation_auto() is False

    transport.queue_response("2\n")
    assert driver.get_rf_attenuation_db() == 2.0

    driver.set_rf_attenuation_manual_db(2)
    assert transport.writes[-1] == "INPut:ATTenuation 2 DB"

    driver.set_rf_attenuation_auto(False)
    assert transport.writes[-1] == "INPut:ATTenuation:AUTO OFF"

    driver.disconnect()

    print(
        "FSW driver self-test PASS"
    )


if __name__ == "__main__":
    main()
