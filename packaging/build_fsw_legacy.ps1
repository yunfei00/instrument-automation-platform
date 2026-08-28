param(
    [ValidateSet("Both", "Onedir", "Onefile")]
    [string]$Mode = "Both",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$BuildVenv = Join-Path $Root ".venv-port-bridge-fsw-legacy"
$Requirements = Join-Path $Root "packaging\requirements-fsw-legacy.txt"

function Get-Python38Command {
    try {
        & py -3.8 -c "import sys; print(sys.version_info[:2])" *> $null
        if ($LASTEXITCODE -eq 0) {
            return @("py", "-3.8")
        }
    } catch {}

    try {
        $version = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
        if ($LASTEXITCODE -eq 0 -and $version.Trim() -eq "3.8") {
            return @("python")
        }
    } catch {}

    throw "Python 3.8 is required for the FSW Legacy build. Install CPython 3.8.10 x64 first."
}

if ($SkipInstall) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
} else {
    Remove-Item -Recurse -Force $BuildVenv -ErrorAction SilentlyContinue
    $base = Get-Python38Command
    if ($base.Count -eq 2) {
        & $base[0] $base[1] -m venv $BuildVenv
    } else {
        & $base[0] -m venv $BuildVenv
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Python 3.8 legacy build environment" }

    $PythonExe = Join-Path $BuildVenv "Scripts\python.exe"
    & $PythonExe -m pip install --upgrade "pip<25"
    if ($LASTEXITCODE -ne 0) { throw "Failed to prepare pip" }
    & $PythonExe -m pip install -r $Requirements
    if ($LASTEXITCODE -ne 0) { throw "Failed to install FSW legacy build dependencies" }
}

$version = & $PythonExe -c "import platform,struct; print(platform.python_version()); print(struct.calcsize('P')*8)"
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect build Python" }
if (-not $version[0].StartsWith("3.8.")) {
    throw "FSW Legacy builds require Python 3.8.x; found $($version[0])"
}
if ($version[1] -ne "64") {
    throw "FSW Legacy builds require 64-bit Python"
}
Write-Host "FSW Legacy build Python: $($version[0]) / $($version[1])-bit"
& $PythonExe -c "import tkinter,pyvisa,PyInstaller; print('Tk=' + str(tkinter.TkVersion)); print('PyVISA=' + pyvisa.__version__); print('PyInstaller=' + PyInstaller.__version__)"

$sourceDiag = Join-Path $Root "build\fsw-legacy-source-diagnostics.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $sourceDiag) | Out-Null
& $PythonExe "tools\instrument_port_bridge_fsw_legacy.py" --diagnostics-file $sourceDiag
if ($LASTEXITCODE -ne 0) {
    if (Test-Path $sourceDiag) { Get-Content $sourceDiag }
    throw "FSW Legacy source diagnostics failed"
}
Get-Content $sourceDiag

function Assert-FrozenDiagnostics {
    param(
        [Parameter(Mandatory=$true)][string]$ExePath,
        [Parameter(Mandatory=$true)][string]$DiagnosticsPath,
        [Parameter(Mandatory=$true)][string]$Label
    )
    $exe = (Resolve-Path $ExePath).Path
    $diag = Join-Path $Root $DiagnosticsPath
    Remove-Item -Force $diag -ErrorAction SilentlyContinue
    $quotedDiag = '"' + $diag + '"'
    $process = Start-Process -FilePath $exe -ArgumentList @("--diagnostics-file", $quotedDiag) -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        if (Test-Path $diag) { Get-Content $diag }
        throw "$Label FSW Legacy diagnostics failed with exit code $($process.ExitCode)"
    }
    if (-not (Test-Path $diag)) { throw "$Label did not create diagnostics file" }
    Get-Content $diag
    if (-not (Select-String -Path $diag -Pattern '^status=ok$' -Quiet)) {
        throw "$Label did not report status=ok"
    }
}

function Build-Onedir {
    Remove-Item -Recurse -Force "dist\fsw-legacy\onedir", "build\fsw-legacy\onedir" -ErrorAction SilentlyContinue
    & $PythonExe -m PyInstaller --noconfirm --clean `
        --distpath "dist\fsw-legacy\onedir" `
        --workpath "build\fsw-legacy\onedir" `
        "packaging\instrument_port_bridge_fsw_legacy.spec"
    if ($LASTEXITCODE -ne 0) { throw "FSW Legacy onedir build failed" }
    Assert-FrozenDiagnostics `
        -ExePath "dist\fsw-legacy\onedir\InstrumentPortBridgeFSWLegacy\InstrumentPortBridgeFSWLegacy.exe" `
        -DiagnosticsPath "build\fsw-legacy-diagnostics-onedir.txt" `
        -Label "onedir"
}

function Build-Onefile {
    Remove-Item -Recurse -Force "dist\fsw-legacy\onefile", "build\fsw-legacy\onefile" -ErrorAction SilentlyContinue
    & $PythonExe -m PyInstaller --noconfirm --clean `
        --distpath "dist\fsw-legacy\onefile" `
        --workpath "build\fsw-legacy\onefile" `
        "packaging\instrument_port_bridge_fsw_legacy_onefile.spec"
    if ($LASTEXITCODE -ne 0) { throw "FSW Legacy onefile build failed" }
    Assert-FrozenDiagnostics `
        -ExePath "dist\fsw-legacy\onefile\InstrumentPortBridgeFSWLegacy.exe" `
        -DiagnosticsPath "build\fsw-legacy-diagnostics-onefile.txt" `
        -Label "onefile"
}

switch ($Mode) {
    "Onedir" { Build-Onedir }
    "Onefile" { Build-Onefile }
    "Both" { Build-Onedir; Build-Onefile }
}

Write-Host "FSW Legacy build completed successfully."
