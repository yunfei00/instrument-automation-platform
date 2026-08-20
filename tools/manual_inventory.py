#!/usr/bin/env python3

import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def inspect_directory(path: Path) -> list[dict]:
    results = []

    if not path.exists():
        return results

    for pdf in sorted(path.glob("*.pdf")):
        results.append(
            {
                "filename": pdf.name,
                "size_bytes": pdf.stat().st_size,
                "size_mb": round(
                    pdf.stat().st_size / 1024 / 1024,
                    2,
                ),
                "sha256": sha256_file(pdf),
            }
        )

    return results


def main() -> int:
    root = Path(__file__).resolve().parents[1]

    directories = {
        "keysight_dsox3000": (
            root
            / "vendor_manuals"
            / "keysight"
            / "dsox3000"
        ),
        "rohde_schwarz_fsw": (
            root
            / "vendor_manuals"
            / "rohde_schwarz"
            / "fsw"
        ),
    }

    report = {
        name: inspect_directory(path)
        for name, path in directories.items()
    }

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
