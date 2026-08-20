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


FILES = [
    "acquisition.json",
    "channel.json",
    "measurement.json",
    "system.json",
    "timebase.json",
    "trigger.json",
    "waveform.json",
]


def main():
    all_ids = set()
    total = 0

    print("DSOX3000 Command Catalog")

    for filename in FILES:
        path = COMMAND_DIR / filename

        assert path.exists(), path

        catalog = CommandCatalog.load_json(
            path
        )

        count = len(catalog.commands)

        print(
            f"{filename:20s} {count:3d}"
        )

        for command in catalog.commands:
            assert (
                command.verification_status
                == VerificationStatus.MANUAL_VERIFIED
            )

            assert command.manual_id
            assert command.manual_page is not None

            assert command.id not in all_ids

            all_ids.add(command.id)

        total += count

    print()
    print(
        "Total manual-verified commands:",
        total,
    )

    assert total >= 40

    print(
        "DSOX3000 all-catalog validation PASS"
    )


if __name__ == "__main__":
    main()
