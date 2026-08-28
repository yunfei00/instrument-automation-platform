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

## Reproducible Qt baseline

Windows release builds use `packaging/requirements-windows-build.txt` instead
of whichever Qt packages happen to be installed in the developer environment.
The release baseline intentionally pins PySide6 6.9.3. Qt 6.10+ Windows builds
added dependencies on system ICU DLLs such as `icuuc.dll`; those dependencies
can make an otherwise valid packaged application fail with:

```text
ImportError: DLL load failed while importing QtCore
```

on older or tightly-managed Windows lab PCs. The build therefore also inspects
the packaged `Qt6Core.dll` and rejects release output that imports the blocked
ICU system DLLs.

## Local Windows build

From PowerShell at the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

The default local build deletes and recreates `.venv-port-bridge-build`,
installs the pinned Windows build toolchain, clears Qt/Conda/Python environment
variables that can contaminate DLL discovery, builds both formats, and launches
both frozen executables in diagnostics mode.

To build only one format:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 -Mode Onedir
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 -Mode Onefile
```

Use `-SkipInstall` only in a controlled CI environment that has already
installed `packaging/requirements-windows-build.txt`. It is not recommended for
normal developer builds.

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
`windows-latest` using the same pinned Windows dependency set. Pull requests
touching the bridge packaging path perform a full Windows packaging check. A
pushed tag matching `v*` additionally creates or updates the GitHub Release and
uploads:

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
