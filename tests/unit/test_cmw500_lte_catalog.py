import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
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


from instrument_lab import (
    CommandCatalog,
    SafetyLevel,
    VerificationStatus,
)


CMD_DIR = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "cmw500"
    / "lte"
    / "commands"
)


def main():

    lifecycle = (
        CommandCatalog.load_json(
            CMD_DIR
            / "mevaluation_lifecycle.json"
        )
    )

    results = (
        CommandCatalog.load_json(
            CMD_DIR
            / "mevaluation_results.json"
        )
    )

    assert len(
        lifecycle.commands
    ) == 5

    assert len(
        results.commands
    ) == 2

    commands = (
        lifecycle.commands
        + results.commands
    )

    ids = {
        command.id
        for command in commands
    }

    assert len(ids) == 7

    for command in commands:

        assert (
            command.verification_status
            == VerificationStatus.MANUAL_VERIFIED
        )

        assert (
            command.manual_id
            == "cmw_lte_ue_rev22"
        )

        assert "<i>" in (
            command.command
        )

    state = lifecycle.get(
        "lte.mevaluation.state"
    )

    assert (
        state.safety
        == SafetyLevel.SAFE
    )

    read_evm = results.get(
        "lte.mevaluation.evm.average"
    )

    assert (
        read_evm.safety
        == SafetyLevel.DISRUPTIVE
    )

    # Important CMW500 rule:
    # READ is syntactically a query but may start
    # a single-shot measurement.
    assert (
        read_evm.probe_enabled
        is False
    )

    print(
        "CMW500 LTE catalog test PASS"
    )

    print(
        "Lifecycle commands:",
        len(lifecycle.commands),
    )

    print(
        "Initial result commands:",
        len(results.commands),
    )

    for command in commands:
        print(
            command.id,
            "=>",
            command.command,
        )


if __name__ == "__main__":
    main()
