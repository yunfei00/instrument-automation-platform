# -*- mode: python ; coding: utf-8 -*-
"""Stable onedir PyInstaller build for Instrument Port Bridge."""

import importlib.util
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata


ROOT = Path(SPEC).resolve().parents[1]
PACKAGE_PATHS = [
    str(ROOT / "packages" / name / "src")
    for name in (
        "instrument_core",
        "instrument_scpi",
        "instrument_lab",
        "instrument_drivers",
        "instrument_qualification",
    )
]

helper_spec = importlib.util.spec_from_file_location(
    "port_bridge_pyinstaller_runtime",
    ROOT / "packaging" / "pyinstaller_runtime.py",
)
if helper_spec is None or helper_spec.loader is None:
    raise RuntimeError("Unable to load PyInstaller runtime helper")
runtime_helper = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(runtime_helper)

# PyVISA-py is discovered dynamically as a VISA backend. Explicitly collect
# its runtime modules and distribution metadata so ResourceManager("@py") works
# in a frozen application. Test-suite modules are excluded from production
# builds to avoid pulling pytest and lab-only test helpers into the EXE.
hiddenimports = collect_submodules(
    "pyvisa_py",
    filter=lambda name: not name.startswith("pyvisa_py.testsuite"),
)
datas = copy_metadata("PyVISA") + copy_metadata("PyVISA-py")


a = Analysis(
    [str(ROOT / "tools" / "instrument_port_bridge.py")],
    pathex=PACKAGE_PATHS,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# CPython 3.11 from the GitHub/local build host may contribute VCRUNTIME 14.38
# while PySide6 6.9.3 contributes 14.44. Windows reuses the first DLL loaded by
# basename, which can make QtCore fail with ERROR_PROC_NOT_FOUND. Normalize all
# collected MSVC v14 DLLs to the PySide6 14.44 runtime before assembling output.
a.binaries = runtime_helper.normalize_msvc_runtime_binaries(a.binaries)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InstrumentPortBridge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="InstrumentPortBridge",
)
