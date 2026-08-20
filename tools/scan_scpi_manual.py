#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SCPI_PATTERN = re.compile(
    r"""
    (?<![A-Za-z0-9_])
    (
        \*
        [A-Za-z]{3,}
        \?
        |
        \*
        [A-Za-z]{3,}
        |
        :
        [A-Za-z][A-Za-z0-9]*
        (?:<[^>\s]+>)?
        (?:
            :
            [A-Za-z][A-Za-z0-9]*
            (?:<[^>\s]+>)?
        )*
        \?
        |
        :
        [A-Za-z][A-Za-z0-9]*
        (?:<[^>\s]+>)?
        (?:
            :
            [A-Za-z][A-Za-z0-9]*
            (?:<[^>\s]+>)?
        )*
    )
    """,
    re.VERBOSE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def canonical_key(command: str) -> str:
    return re.sub(
        r"\s+",
        "",
        command,
    ).upper()


def namespace(command: str) -> str:
    if command.startswith("*"):
        return "COMMON"

    value = command.lstrip(":")
    first = value.split(":", 1)[0]
    first = re.sub(
        r"<[^>]+>",
        "",
        first,
    )

    return first.upper()


def valid_candidate(command: str) -> bool:
    if command.startswith("*"):
        return len(command) >= 4

    if not command.startswith(":"):
        return False

    if len(command) < 4:
        return False

    body = command.lstrip(":")

    if not any(
        char.isalpha()
        for char in body
    ):
        return False

    return True


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "text_file",
    )

    parser.add_argument(
        "--manual",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    text_path = Path(
        args.text_file
    )

    manual_path = Path(
        args.manual
    )

    output_path = Path(
        args.output
    )

    text = text_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = text.splitlines()

    found = {}

    occurrence_count = Counter()

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        for match in SCPI_PATTERN.finditer(
            line
        ):
            command = match.group(1)

            command = command.strip()

            if not valid_candidate(
                command
            ):
                continue

            key = canonical_key(
                command
            )

            occurrence_count[key] += 1

            if key not in found:
                found[key] = {
                    "command": command,
                    "namespace": namespace(
                        command
                    ),
                    "first_text_line": line_number,
                    "occurrences": 0,
                    "status": "candidate",
                }

    for key, count in occurrence_count.items():
        found[key]["occurrences"] = count

    candidates = sorted(
        found.values(),
        key=lambda item: (
            item["namespace"],
            item["command"].upper(),
        ),
    )

    namespace_counts = Counter(
        candidate["namespace"]
        for candidate in candidates
    )

    payload = {
        "metadata": {
            "instrument_family": (
                "Keysight DSO-X 3000 X-Series"
            ),
            "target_model": (
                "DSO-X 3034A"
            ),
            "source_manual": (
                manual_path.name
            ),
            "source_manual_sha256": (
                sha256_file(
                    manual_path
                )
            ),
            "source_text": (
                text_path.name
            ),
            "candidate_count": (
                len(candidates)
            ),
            "status": (
                "automatically_extracted_unverified"
            ),
            "note": (
                "Candidates must be verified against "
                "the manual before entering the "
                "production Command Catalog."
            ),
        },
        "namespace_counts": dict(
            sorted(
                namespace_counts.items()
            )
        ),
        "commands": candidates,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "SCPI candidates:",
        len(candidates),
    )

    print()
    print(
        "===== NAMESPACE COUNTS ====="
    )

    for name, count in sorted(
        namespace_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):
        print(
            f"{name:20s} {count:5d}"
        )

    print()
    print(
        "===== FIRST 80 CANDIDATES ====="
    )

    for item in candidates[:80]:
        print(
            f"{item['namespace']:15s} "
            f"{item['command']:45s} "
            f"count={item['occurrences']}"
        )


if __name__ == "__main__":
    main()
