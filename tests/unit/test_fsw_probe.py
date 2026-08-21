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


from instrument_drivers.rohde_schwarz.fsw.catalog_probe import (
    load_probe_commands,
)


COMMAND_DIR = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "fsw"
    / "commands"
)


def main():
    commands = load_probe_commands(
        COMMAND_DIR,
        channel=1,
        window=1,
        marker=1,
        trace=1,
    )

    texts = [
        command.probe_command
        for command in commands
    ]

    assert (
        "SENSe:FREQuency:CENTer?"
        in texts
    )

    assert (
        "SENSe:BANDwidth:RESolution?"
        in texts
    )

    assert (
        "SENSe:BANDwidth:VIDeo?"
        in texts
    )

    assert (
        "INITiate1:CONTinuous?"
        in texts
    )

    assert (
        "FORMat:DATA?"
        in texts
    )

    assert (
        "SYSTem:ERRor:NEXT?"
        in texts
    )

    assert not any(
        "[" in command
        or "]" in command
        or "<" in command
        or ">" in command
        for command in texts
    )

    assert (
        "TRACe1:DATA? TRACE1"
        not in texts
    )

    print(
        "FSW catalog probe PASS"
    )

    print(
        "Safe probe commands:",
        len(commands),
    )

    for command in texts:
        print(
            " ",
            command
        )


if __name__ == "__main__":
    main()
