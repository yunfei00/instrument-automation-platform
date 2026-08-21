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
from instrument_scpi import (
    SCPIClient,
)
from instrument_drivers.rohde_schwarz.cmw500.applications.lte import (
    LTEMultiEvaluation,
    parse_evm_magnitude,
    parse_state_all,
)


def main():

    observed = (
        "6,"
        + ",".join(
            ["INV"] * 14
        )
        + "\n"
    )

    result = (
        parse_evm_magnitude(
            observed
        )
    )

    assert result.reliability == 6

    assert (
        result.reliability_label
        == "trigger_timeout"
    )

    assert (
        result.cyclic_prefix
        == "normal"
    )

    assert result.symbol_count == 7
    assert result.reference_symbol == 3

    assert all(
        value is None
        for value
        in result.low_window
    )

    assert all(
        value is None
        for value
        in result.high_window
    )

    extended = (
        "0,"
        "1,2,3,4,5,6,"
        "11,12,13,14,15,16"
    )

    result2 = (
        parse_evm_magnitude(
            extended
        )
    )

    assert (
        result2.cyclic_prefix
        == "extended"
    )

    assert result2.symbol_count == 6
    assert result2.reference_symbol == 2

    state = parse_state_all(
        "RDY,ADJ,INV"
    )

    assert state.main == "RDY"
    assert state.sync == "ADJ"
    assert state.resource == "INV"

    transport = MockTransport()
    transport.open()

    scpi = SCPIClient(
        transport
    )

    measurement = (
        LTEMultiEvaluation(
            scpi,
            instance=1,
        )
    )

    measurement.initiate()

    assert (
        transport.writes[-1]
        == (
            "INITiate:LTE:"
            "MEAS1:MEValuation"
        )
    )

    transport.queue_response(
        "RDY\n"
    )

    assert (
        measurement
        .fetch_state()
        .main
        == "RDY"
    )

    transport.queue_response(
        "RDY,ADJ,INV\n"
    )

    state = (
        measurement
        .fetch_state_all()
    )

    assert state.sync == "ADJ"

    transport.queue_response(
        observed
    )

    evm = (
        measurement
        .fetch_evm_average()
    )

    assert evm.reliability == 6
    assert evm.symbol_count == 7

    measurement.abort()

    assert (
        transport.writes[-1]
        == (
            "ABORt:LTE:"
            "MEAS1:MEValuation"
        )
    )

    print(
        "CMW500 LTE Multi Evaluation "
        "domain test PASS"
    )

    print(
        "Observed reliability:",
        evm.reliability,
        evm.reliability_label,
    )

    print(
        "Cyclic prefix:",
        evm.cyclic_prefix,
    )

    print(
        "Symbols:",
        evm.symbol_count,
    )


if __name__ == "__main__":
    main()
