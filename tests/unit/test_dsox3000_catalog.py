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
        str(ROOT / f"packages/{package}/src"),
    )

from instrument_lab import (
    CommandCatalog,
    VerificationStatus,
)


COMMAND_DIR = (
    ROOT
    / "instrument_profiles"
    / "keysight"
    / "dsox3000"
    / "commands"
)


def check_catalog(name):
    catalog = CommandCatalog.load_json(
        COMMAND_DIR / name
    )

    assert catalog.commands

    ids = [
        command.id
        for command in catalog.commands
    ]

    assert len(ids) == len(set(ids))

    for command in catalog.commands:
        assert (
            command.verification_status
            == VerificationStatus.MANUAL_VERIFIED
        )

        assert command.manual_id
        assert command.manual_page is not None

    return catalog


def main():
    acquisition = check_catalog(
        "acquisition.json"
    )

    waveform = check_catalog(
        "waveform.json"
    )

    digitize = acquisition.get(
        "root.digitize"
    )

    assert not digitize.probe_enabled

    waveform_data = waveform.get(
        "waveform.data"
    )

    assert not waveform_data.probe_enabled

    preamble = waveform.get(
        "waveform.preamble"
    )

    assert preamble.probe_enabled

    print(
        "DSOX3000 verified catalog test PASS"
    )

    print(
        "Acquisition commands:",
        len(acquisition.commands),
    )

    print(
        "Waveform commands:",
        len(waveform.commands),
    )


if __name__ == "__main__":
    main()
