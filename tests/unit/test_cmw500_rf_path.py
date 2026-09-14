import pytest

from instrument_core.transport import MockTransport
from instrument_drivers.rohde_schwarz.cmw500 import (
    CMWRFPathExternalAttenuation,
    RohdeSchwarzCMW500Driver,
)
from instrument_scpi import SCPIClient


def test_generator_output_attenuation_set_and_query():
    transport = MockTransport()
    driver = RohdeSchwarzCMW500Driver(transport)

    driver.set_external_output_attenuation_db(
        application="GPRF",
        value_db=2.0,
    )

    assert transport.writes[-1] == (
        "SOURce:GPRF:GENerator1:RFSettings:EATTenuation 2"
    )

    transport.queue_response("2.000000E+000\n")

    assert driver.get_external_output_attenuation_db("GPRF") == 2.0
    assert transport.queries[-1] == (
        "SOURce:GPRF:GENerator1:RFSettings:EATTenuation?"
    )


def test_measurement_input_attenuation_set_and_query():
    transport = MockTransport()
    driver = RohdeSchwarzCMW500Driver(transport)

    driver.set_external_input_attenuation_db(
        application="WCDMa",
        value_db=3.2,
        instance=2,
    )

    assert transport.writes[-1] == (
        "CONFigure:WCDMA:MEASurement2:RFSettings:EATTenuation 3.2"
    )

    transport.queue_response("3.200000E+000\n")

    assert (
        driver.get_external_input_attenuation_db(
            "WCDMa",
            instance=2,
        )
        == 3.2
    )
    assert transport.queries[-1] == (
        "CONFigure:WCDMA:MEASurement2:RFSettings:EATTenuation?"
    )


def test_rf_path_controller_is_public_and_reusable():
    transport = MockTransport()
    controller = CMWRFPathExternalAttenuation(
        scpi=SCPIClient(transport),
        application="wlan",
        instance=1,
    )

    controller.set_input_attenuation_db(1.5)
    controller.set_output_attenuation_db(-3.0)

    assert transport.writes == [
        "CONFigure:WLAN:MEASurement1:RFSettings:EATTenuation 1.5",
        "SOURce:WLAN:GENerator1:RFSettings:EATTenuation -3",
    ]


def test_external_attenuation_validation():
    transport = MockTransport()
    driver = RohdeSchwarzCMW500Driver(transport)

    with pytest.raises(ValueError):
        driver.set_external_input_attenuation_db("GPRF", 90.1)

    with pytest.raises(ValueError):
        driver.set_external_output_attenuation_db("GPRF", -50.1)

    with pytest.raises(ValueError):
        driver.rf_path("GPRF;*RST")

    with pytest.raises(ValueError):
        driver.rf_path("GPRF", instance=5)

    with pytest.raises(TypeError):
        driver.rf_path("GPRF", instance=True)


def test_signaling_command_tree_is_not_guessed():
    """The common helper intentionally models standalone GEN/MEAS only."""

    transport = MockTransport()
    controller = CMWRFPathExternalAttenuation(
        scpi=SCPIClient(transport),
        application="LTE",
    )

    assert ":SIGN" not in controller.generator_output_command
    assert ":SIGN" not in controller.measurement_input_command
