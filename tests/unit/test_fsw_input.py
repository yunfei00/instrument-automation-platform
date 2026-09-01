import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
]:
    sys.path.insert(
        0,
        str(ROOT / f"packages/{package}/src"),
    )

from instrument_core.transport import MockTransport
from instrument_drivers.rohde_schwarz.fsw import RohdeSchwarzFSWDriver


def main():
    transport = MockTransport()
    transport.open()
    driver = RohdeSchwarzFSWDriver(transport)

    # Real-hardware observed preamp contract.
    transport.queue_response("0\n")
    assert driver.get_preamp_db() == 0

    transport.queue_response("1\n")
    transport.queue_response("15\n")
    assert driver.get_preamp_db() == 15

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

    driver.set_preamp_db(30)
    assert transport.writes[-2:] == [
        "INPut:GAIN:STATe ON",
        "INPut:GAIN:VALue 30",
    ]

    try:
        driver.set_preamp_db(20)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported preamp gain was accepted")

    # RF attenuation: AUTO? determines Auto/Manual, ATT? reads the dB value.
    transport.queue_response("0\n")
    assert driver.get_rf_attenuation_auto() is False

    transport.queue_response("1\n")
    assert driver.get_rf_attenuation_auto() is True

    transport.queue_response("2.000000E+01\n")
    assert driver.get_rf_attenuation_db() == 20.0

    driver.set_rf_attenuation_manual_db(25)
    assert transport.writes[-1] == "INPut:ATTenuation 25 DB"

    driver.set_rf_attenuation_auto(True)
    assert transport.writes[-1] == "INPut:ATTenuation:AUTO ON"

    transport.queue_response("LNO\n")
    assert driver.get_rf_attenuation_auto_mode() == "LNO"

    driver.set_rf_attenuation_auto_mode("LNOise")
    assert transport.writes[-1] == "INPut:ATTenuation:AUTO:MODE LNOise"

    driver.set_rf_attenuation_auto_mode("LDIStortion")
    assert transport.writes[-1] == "INPut:ATTenuation:AUTO:MODE LDIStortion"

    # Optional electronic attenuator command path.
    transport.queue_response("1\n")
    assert driver.get_electronic_attenuator_enabled() is True

    transport.queue_response("0\n")
    assert driver.get_electronic_attenuation_auto() is False

    transport.queue_response("1.000000E+01\n")
    assert driver.get_electronic_attenuation_db() == 10.0

    driver.set_electronic_attenuation_manual_db(10)
    assert transport.writes[-2:] == [
        "INPut:EATT:AUTO OFF",
        "INPut:EATT 10 DB",
    ]

    print("FSW input controls self-test PASS")


if __name__ == "__main__":
    main()
