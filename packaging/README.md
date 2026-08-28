# Instrument Port Bridge Windows Packaging

This directory contains the reproducible Windows packaging configuration for
Instrument Port Bridge.

## Release policy

Two Windows x64 deliverables are produced:

- `InstrumentPortBridge-<version>-win64.zip` — recommended stable distribution.
  It contains the PyInstaller `onedir` build and should be preferred for lab
  deployment because Qt/VISA runtime files remain visible and diagnosable.
- `InstrumentPortBridge-<version>-win64-onefile.exe` — portable single-file
  build for convenient transfer and evaluation.

Both builds execute the same application code and both must pass frozen runtime
diagnostics before they are published.

## Local Windows build

From PowerShell at the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

To build only one format:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 -Mode Onedir
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 -Mode Onefile
```

The script installs `requirements-gui.txt` and PyInstaller by default. Use
`-SkipInstall` only when the build environment is already prepared.

## Frozen diagnostics

Source and packaged builds support a non-interactive runtime check:

```powershell
python tools\instrument_port_bridge.py --diagnostics --diagnostics-file diagnostics.txt
InstrumentPortBridge.exe --diagnostics-file diagnostics.txt
```

A valid build writes `status=ok` after importing PySide6, PyVISA,
PyVISA-py, the baseline bridge core, SCPI package, and GUI module. This catches
missing hidden imports before a release reaches a lab PC.

## VISA runtime requirement

PyVISA and the pure-Python `@py` backend are packaged. Vendor VISA runtimes are
not bundled into the application and should remain installed system components.
For USBTMC instruments such as Keysight oscilloscopes, install the appropriate
vendor VISA runtime/IO Libraries on the Windows host when using the vendor
backend.

Network TCP -> TCP forwarding does not require a vendor VISA runtime.

## GitHub release

The workflow `.github/workflows/instrument-port-bridge-release.yml` builds on
`windows-latest`. Pull requests touching the bridge packaging path perform a
full Windows packaging check. A pushed tag matching `v*` additionally creates
or updates the GitHub Release and uploads:

- stable onedir ZIP
- portable onefile EXE
- `SHA256SUMS.txt`

Typical release command:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Do not create a stable release tag until USB/VISA and network/TCP forwarding
have both passed the intended real-instrument validation.
