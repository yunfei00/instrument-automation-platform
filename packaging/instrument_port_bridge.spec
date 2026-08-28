# -*- mode: python ; coding: utf-8 -*-
"""Stable onedir PyInstaller build for Instrument Port Bridge."""

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

# PyVISA-py is discovered dynamically as a VISA backend.  Explicitly collect
# its modules and distribution metadata so ResourceManager("@py") works in a
# frozen application.  Vendor VISA runtimes/DLLs are intentionally external.
hiddenimports = collect_submodules("pyvisa_py")
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
