import pytest

from instrument_core.transport import MockTransport
from instrument_drivers.rohde_schwarz.cmw500.applications.lte import (
    LTESignalingRFPath,
)
from instrument_scpi import SCPIClient


def test_default_lte_signaling_input_output_commands():
    transport = MockTransport()
    rf = LTESignalingRFPath(SCPIClient(transport))

    rf.set_input_attenuation_db(2.0)
    rf.set_output_attenuation_db(3.5)

    assert transport.writes == [
        "CONFigure:LTE:SIGN:RFSettings:EATTenuation:INPut 2",
        "CONFigure:LTE:SIGN:RFSettings:EATTenuation:OUTPut 3.5",
    ]


def test_lte_signaling_query_readback():
    transport = MockTransport()
    rf = LTESignalingRFPath(SCPIClient(transport))

    transport.queue_response("2.000000E+000\n")
    assert rf.get_input_attenuation_db() == 2.0
    assert transport.writes[-1] == (
        "CONFigure:LTE:SIGN:RFSettings:EATTenuation:INPut?"
    )

    transport.queue_response("3.000000E+000\n")
    assert rf.get_output_attenuation_db() == 3.0
    assert transport.writes[-1] == (
        "CONFigure:LTE:SIGN:RFSettings:EATTenuation:OUTPut?"
    )


def test_lte_signaling_output_path_and_instance_are_explicit():
    transport = MockTransport()
    rf = LTESignalingRFPath(
        SCPIClient(transport),
        signaling_instance=2,
    )

    rf.set_output_attenuation_db(4.0, output_path=2)

    assert transport.writes[-1] == (
        "CONFigure:LTE:SIGNaling2:RFSettings:EATTenuation:OUTPut2 4"
    )


def test_lte_signaling_external_attenuation_validation():
    transport = MockTransport()
    rf = LTESignalingRFPath(SCPIClient(transport))

    with pytest.raises(ValueError):
        rf.set_input_attenuation_db(90.1)

    with pytest.raises(ValueError):
        rf.set_output_attenuation_db(-50.1)

    with pytest.raises(ValueError):
        rf.output_command(0)

    with pytest.raises(TypeError):
        LTESignalingRFPath(SCPIClient(transport), signaling_instance=True)
