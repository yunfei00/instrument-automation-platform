import sys
from collections import Counter
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
    / "rohde_schwarz"
    / "fsw"
    / "commands"
)


FILES = [
    "frequency.json",
    "bandwidth.json",
    "amplitude.json",
    "sweep.json",
    "trigger.json",
    "initiate.json",
    "trace.json",
    "marker.json",
    "system.json",
]


def main():
    ids = set()
    statuses = Counter()
    total = 0

    print("R&S FSW Command Catalog")
    print()

    for filename in FILES:
        catalog = CommandCatalog.load_json(
            COMMAND_DIR / filename
        )

        print(
            f"{filename:20s} "
            f"{len(catalog.commands):3d}"
        )

        for command in catalog.commands:
            assert command.id not in ids
            ids.add(command.id)

            statuses[
                command.verification_status.value
            ] += 1

            if (
                command.verification_status
                == VerificationStatus.MANUAL_VERIFIED
            ):
                assert command.manual_id
                assert command.manual_page is not None

        total += len(catalog.commands)

    print()
    print("Total:", total)

    for status, count in sorted(
        statuses.items()
    ):
        print(
            f"{status}: {count}"
        )

    assert statuses["manual_verified"] >= 15
    assert statuses["candidate"] >= 1

    print()
    print(
        "FSW catalog validation PASS"
    )


if __name__ == "__main__":
    main()
