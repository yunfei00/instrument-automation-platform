param(
    [ValidateSet("Both", "Onedir", "Onefile")]
    [string]$Mode = "Both",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

if (-not $SkipInstall) {
    python -m pip install --upgrade pip
    python -m pip install -r requirements-gui.txt
    python -m pip install "pyinstaller>=6.10,<7"
}

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
    # process has exited.  Start-Process -Wait is required, especially for the
    # onefile build which first extracts itself to a temporary directory.
    $quotedDiag = '"' + $diag + '"'
    $process = Start-Process `
        -FilePath $exe `
        -ArgumentList @("--diagnostics-file", $quotedDiag) `
        -Wait `
        -PassThru

    if ($process.ExitCode -ne 0) {
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

function Build-Onedir {
    Remove-Item -Recurse -Force "dist\onedir", "build\onedir" -ErrorAction SilentlyContinue
    python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath "dist\onedir" `
        --workpath "build\onedir" `
        "packaging\instrument_port_bridge.spec"
    if ($LASTEXITCODE -ne 0) { throw "onedir PyInstaller build failed" }

    Assert-FrozenDiagnostics `
        -ExePath "dist\onedir\InstrumentPortBridge\InstrumentPortBridge.exe" `
        -DiagnosticsPath "build\diagnostics-onedir.txt" `
        -Label "onedir"
}

function Build-Onefile {
    Remove-Item -Recurse -Force "dist\onefile", "build\onefile" -ErrorAction SilentlyContinue
    python -m PyInstaller `
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
