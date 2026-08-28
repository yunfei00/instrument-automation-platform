# -*- mode: python ; coding: utf-8 -*-
"""Portable onefile PyInstaller build for Instrument Port Bridge."""

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
a.binaries = runtime_helper.normalize_msvc_runtime_binaries(a.binaries)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
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
