# -*- mode: python ; coding: utf-8 -*-
"""FSW legacy onedir build: Python 3.8 + Tkinter + PyVISA, no Qt."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata


ROOT = Path(SPEC).resolve().parents[1]
CORE_PATH = str(ROOT / "packages" / "instrument_core" / "src")

hiddenimports = collect_submodules("pyvisa")
datas = copy_metadata("PyVISA")

a = Analysis(
    [str(ROOT / "tools" / "instrument_port_bridge_fsw_legacy.py")],
    pathex=[CORE_PATH],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6", "PyQt5", "PyQt6", "numpy"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InstrumentPortBridgeFSWLegacy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="InstrumentPortBridgeFSWLegacy",
)
