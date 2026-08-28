"""PyInstaller helpers for a consistent Windows MSVC runtime.

PyInstaller can collect one Visual C++ runtime from CPython and newer copies
from PySide6/shiboken6. Windows reuses the first loaded DLL by basename, so
mixing v14 runtime revisions can make Qt fail with
"The specified procedure could not be found" even though every DLL exists.

Use the PySide6 wheel's runtime set as the canonical app-local runtime. Qt is
the newest native component in this application, so its runtime revision must
also satisfy the older CPython components. Microsoft guarantees binary
compatibility for newer v14 runtimes with binaries built by older v14 tools.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable


MSVC_RUNTIME_NAMES = {
    "msvcp140.dll",
    "msvcp140_1.dll",
    "msvcp140_2.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
}


def _pyside6_directory() -> Path:
    spec = importlib.util.find_spec("PySide6")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("PySide6 package directory could not be resolved")
    return Path(next(iter(spec.submodule_search_locations))).resolve()


def _canonical_runtime_sources() -> dict[str, Path]:
    root = _pyside6_directory()
    sources: dict[str, Path] = {}
    for name in MSVC_RUNTIME_NAMES:
        candidate = root / name
        if candidate.is_file():
            sources[name] = candidate
    if "vcruntime140.dll" not in sources or "vcruntime140_1.dll" not in sources:
        raise RuntimeError(
            f"PySide6 at {root} does not contain the required MSVC runtime DLLs"
        )
    return sources


def normalize_msvc_runtime_binaries(binaries: Iterable[tuple]) -> list[tuple]:
    """Replace every collected MSVC v14 runtime with the PySide6 copy.

    Destination paths are preserved, but all copies with the same runtime DLL
    name originate from one canonical source. This also replaces PyInstaller's
    root-level CPython VCRUNTIME 14.38 copy with the newer PySide6 runtime used
    by Qt 6.9.3.
    """

    sources = _canonical_runtime_sources()
    normalized: list[tuple] = []
    for entry in binaries:
        if len(entry) != 3:
            normalized.append(entry)
            continue
        destination, source, typecode = entry
        key = Path(destination).name.lower()
        canonical = sources.get(key)
        if canonical is not None:
            source = str(canonical)
        normalized.append((destination, source, typecode))
    return normalized
