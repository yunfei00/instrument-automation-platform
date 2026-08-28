#!/usr/bin/env python3
"""Validate native Windows dependencies in a frozen Port Bridge build."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pefile


BLOCKED_QT_SYSTEM_DLLS = {
    "icu.dll",
    "icuuc.dll",
    "icuin.dll",
}


def imported_dlls(path: Path) -> list[str]:
    pe = pefile.PE(str(path), fast_load=True)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
    )
    names: list[str] = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        names.append(entry.dll.decode("ascii", errors="replace"))
    return sorted(set(names), key=str.lower)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dll", type=Path)
    args = parser.parse_args()

    dll = args.dll.resolve()
    if not dll.is_file():
        print(f"missing={dll}", file=sys.stderr)
        return 2

    imports = imported_dlls(dll)
    print(f"dependency_check={dll}")
    for name in imports:
        print(f"import={name}")

    blocked = sorted(
        {name.lower() for name in imports} & BLOCKED_QT_SYSTEM_DLLS
    )
    if blocked:
        print(
            "blocked_system_dependency=" + ",".join(blocked),
            file=sys.stderr,
        )
        return 1

    print("portable_qt_dependency_check=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
