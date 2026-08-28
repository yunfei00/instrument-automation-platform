param(
    [ValidateSet("Both", "Onedir", "Onefile")]
    [string]$Mode = "Both",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$BuildVenv = Join-Path $Root ".venv-port-bridge-build"
$PinnedRequirements = Join-Path $Root "packaging\requirements-windows-build.txt"

if ($SkipInstall) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
} else {
    # Do not build from the user's development environment. PySide/Qt DLL
    # mixing is a common cause of "DLL load failed while importing QtCore".
    # A fresh venv makes the local build match GitHub Actions much more closely.
    Remove-Item -Recurse -Force $BuildVenv -ErrorAction SilentlyContinue
    python -m venv $BuildVenv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create isolated build environment" }

    $PythonExe = Join-Path $BuildVenv "Scripts\python.exe"
    & $PythonExe -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip in build environment" }
    & $PythonExe -m pip install -r $PinnedRequirements
    if ($LASTEXITCODE -ne 0) { throw "Failed to install pinned Windows build dependencies" }
}

# Verify the build interpreter before touching PyInstaller output.
$buildInfo = & $PythonExe -c "import platform,struct,sys; print(sys.version.split()[0]); print(platform.python_implementation()); print(struct.calcsize('P')*8)"
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect build Python" }
if ($buildInfo[1] -ne "CPython" -or $buildInfo[2] -ne "64") {
    throw "Instrument Port Bridge Windows builds require 64-bit CPython"
}
Write-Host "Build Python: $($buildInfo[0]) / $($buildInfo[1]) / $($buildInfo[2])-bit"
& $PythonExe -c "import PySide6, pyvisa, PyInstaller; print('PySide6=' + PySide6.__version__); print('PyVISA=' + pyvisa.__version__); print('PyInstaller=' + PyInstaller.__version__)"

# Prevent unrelated Qt/Conda installations from influencing PyInstaller's DLL
# discovery or the packaged smoke test. Use only the build venv and Windows
# system directories for executable/DLL lookup.
foreach ($name in @(
    "PYTHONHOME",
    "PYTHONPATH",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV"
)) {
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}
$env:PATH = @(
    (Split-Path $PythonExe -Parent),
    "$env:SystemRoot\System32",
    "$env:SystemRoot",
    "$env:SystemRoot\System32\Wbem"
) -join ";"

function Assert-FrozenDiagnostics {
    param(
        [Parameter(Mandatory = $true)][string]$ExePath,
        [Parameter(Mandatory = $true)][string]$DiagnosticsPath,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $exe = (Resolve-Path $ExePath).Path
    $diag = Join-Path $Root $DiagnosticsPath
    Remove-Item -Force $diag -ErrorAction SilentlyContinue

    # Windowed Windows executables can return control to the shell before the
    # process has exited. Start-Process -Wait is required, especially for the
    # onefile build which first extracts itself to a temporary directory.
    $quotedDiag = '"' + $diag + '"'
    $process = Start-Process `
        -FilePath $exe `
        -ArgumentList @("--diagnostics-file", $quotedDiag) `
        -Wait `
        -PassThru

    if ($process.ExitCode -ne 0) {
        if (Test-Path $diag) { Get-Content $diag }
        throw "$Label executable diagnostics failed with exit code $($process.ExitCode)"
    }
    if (-not (Test-Path $diag)) {
        throw "$Label executable did not create diagnostics file"
    }
    if (-not (Select-String -Path $diag -Pattern '^status=ok$' -Quiet)) {
        Get-Content $diag
        throw "$Label executable did not report status=ok"
    }
    Get-Content $diag
}

function Assert-MsvcRuntimeConsistency {
    param([Parameter(Mandatory = $true)][string]$DistributionRoot)

    $runtimeNames = @(
        "MSVCP140.dll",
        "MSVCP140_1.dll",
        "MSVCP140_2.dll",
        "VCRUNTIME140.dll",
        "VCRUNTIME140_1.dll"
    )

    foreach ($runtimeName in $runtimeNames) {
        $files = @(Get-ChildItem -Path $DistributionRoot -Recurse -File | Where-Object {
            $_.Name -ieq $runtimeName
        })
        if ($files.Count -eq 0) { continue }

        $hashes = @{}
        foreach ($file in $files) {
            $hash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($file.FullName).FileVersion
            Write-Host "msvc_runtime=$runtimeName version=$version hash=$hash path=$($file.FullName)"
            $hashes[$hash] = $true
        }
        if ($hashes.Count -ne 1) {
            throw "$runtimeName is bundled from multiple incompatible runtime builds"
        }
    }

    # CPython's host runtime used to be 14.38 while Qt 6.9.3 needs 14.44.
    # The root-level VCRUNTIME is loaded very early, so it must be the same DLL
    # as Qt's app-local copy or Windows can reuse an older DLL and fail later
    # with ERROR_PROC_NOT_FOUND while importing PySide6.QtCore.
    $rootRuntime = Join-Path $DistributionRoot "_internal\VCRUNTIME140.dll"
    $qtRuntime = Join-Path $DistributionRoot "_internal\PySide6\VCRUNTIME140.dll"
    if ((Test-Path $rootRuntime) -and (Test-Path $qtRuntime)) {
        $rootHash = (Get-FileHash $rootRuntime -Algorithm SHA256).Hash
        $qtHash = (Get-FileHash $qtRuntime -Algorithm SHA256).Hash
        if ($rootHash -ne $qtHash) {
            throw "Root CPython VCRUNTIME differs from the Qt VCRUNTIME"
        }
    }
    Write-Host "msvc_runtime_consistency=ok"
}

function Build-Onedir {
    Remove-Item -Recurse -Force "dist\onedir", "build\onedir" -ErrorAction SilentlyContinue
    & $PythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath "dist\onedir" `
        --workpath "build\onedir" `
        "packaging\instrument_port_bridge.spec"
    if ($LASTEXITCODE -ne 0) { throw "onedir PyInstaller build failed" }

    $distributionRoot = "dist\onedir\InstrumentPortBridge"
    $qtCore = "$distributionRoot\_internal\PySide6\Qt6Core.dll"
    & $PythonExe "packaging\check_windows_dependencies.py" $qtCore
    if ($LASTEXITCODE -ne 0) {
        throw "Qt6Core contains a blocked system dependency; use the pinned portable Qt build"
    }
    Assert-MsvcRuntimeConsistency -DistributionRoot $distributionRoot

    Assert-FrozenDiagnostics `
        -ExePath "$distributionRoot\InstrumentPortBridge.exe" `
        -DiagnosticsPath "build\diagnostics-onedir.txt" `
        -Label "onedir"
}

function Build-Onefile {
    Remove-Item -Recurse -Force "dist\onefile", "build\onefile" -ErrorAction SilentlyContinue
    & $PythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath "dist\onefile" `
        --workpath "build\onefile" `
        "packaging\instrument_port_bridge_onefile.spec"
    if ($LASTEXITCODE -ne 0) { throw "onefile PyInstaller build failed" }

    Assert-FrozenDiagnostics `
        -ExePath "dist\onefile\InstrumentPortBridge.exe" `
        -DiagnosticsPath "build\diagnostics-onefile.txt" `
        -Label "onefile"
}

switch ($Mode) {
    "Onedir" { Build-Onedir }
    "Onefile" { Build-Onefile }
    "Both" {
        Build-Onedir
        Build-Onefile
    }
}

Write-Host "Instrument Port Bridge build completed successfully."
