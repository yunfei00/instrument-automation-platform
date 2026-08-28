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

function Build-Onedir {
    Remove-Item -Recurse -Force "dist\onedir", "build\onedir" -ErrorAction SilentlyContinue
    python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath "dist\onedir" `
        --workpath "build\onedir" `
        "packaging\instrument_port_bridge.spec"
    if ($LASTEXITCODE -ne 0) { throw "onedir PyInstaller build failed" }

    $exe = "dist\onedir\InstrumentPortBridge\InstrumentPortBridge.exe"
    $diag = "build\diagnostics-onedir.txt"
    & $exe --diagnostics-file $diag
    if ($LASTEXITCODE -ne 0) { throw "onedir executable diagnostics failed" }
    if (-not (Select-String -Path $diag -Pattern '^status=ok$' -Quiet)) {
        Get-Content $diag
        throw "onedir executable did not report status=ok"
    }
    Get-Content $diag
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

    $exe = "dist\onefile\InstrumentPortBridge.exe"
    $diag = "build\diagnostics-onefile.txt"
    & $exe --diagnostics-file $diag
    if ($LASTEXITCODE -ne 0) { throw "onefile executable diagnostics failed" }
    if (-not (Select-String -Path $diag -Pattern '^status=ok$' -Quiet)) {
        Get-Content $diag
        throw "onefile executable did not report status=ok"
    }
    Get-Content $diag
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
