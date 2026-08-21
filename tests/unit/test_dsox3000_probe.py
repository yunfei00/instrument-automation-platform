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


from instrument_drivers.keysight.dsox3000.catalog_probe import (
    load_probe_commands,
)


COMMAND_DIR = (
    ROOT
    / "instrument_profiles"
    / "keysight"
    / "dsox3000"
    / "commands"
)


def main():
    commands = load_probe_commands(
        COMMAND_DIR,
        channel=1,
        include_measurements=False,
    )

    assert commands

    command_texts = [
        command.probe_command
        for command in commands
    ]

    assert (
        ":CHANnel1:SCALe?"
        in command_texts
    )

    assert (
        ":TIMebase:SCALe?"
        in command_texts
    )

    assert (
        ":WAVeform:PREamble?"
        in command_texts
    )

    assert (
        ":WAVeform:DATA?"
        not in command_texts
    )

    assert (
        ":DIGitize"
        not in command_texts
    )

    assert all(
        "<n>" not in value
        for value in command_texts
    )

    assert all(
        not command.id.startswith(
            "measure."
        )
        for command in commands
    )

    measurement_commands = (
        load_probe_commands(
            COMMAND_DIR,
            channel=1,
            include_measurements=True,
        )
    )

    assert any(
        command.id
        == "measure.frequency"
        for command
        in measurement_commands
    )

    print(
        "DSOX3000 catalog probe test PASS"
    )

    print(
        "Default safe probe commands:",
        len(commands),
    )

    print(
        "With measurements:",
        len(measurement_commands),
    )


if __name__ == "__main__":
    main()
