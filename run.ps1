param([switch]$SmokeTest, [switch]$Demo)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$cargoCommand = Get-Command cargo -ErrorAction SilentlyContinue
if ($cargoCommand) { $cargoExecutable = $cargoCommand.Source }
else { $cargoExecutable = Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe' }
if (-not (Test-Path -LiteralPath $cargoExecutable)) { throw 'Install Rust from https://rustup.rs, then run this launcher again.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& '.venv\Scripts\python.exe' -m pip install -r requirements.txt --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw 'Qt dependency installation failed.' }
& $cargoExecutable build --locked
if ($LASTEXITCODE -ne 0) { throw 'Rust build failed.' }
if (-not ($Demo -or $SmokeTest)) {
    & '.venv\Scripts\python.exe' tools/prepare_windows.py
    if ($LASTEXITCODE -ne 0) { throw 'Driver client preparation failed. No system drivers were installed.' }
    New-Item -ItemType Directory -Force -Path 'target\debug\drivers' | Out-Null
    Copy-Item -LiteralPath 'artifacts\windows-dependencies\interception.dll' -Destination 'target\debug\drivers\interception.dll'
}
$launchArgs = @('gui/app.py')
if ($Demo -or $SmokeTest) { $launchArgs += '--demo' }
if ($SmokeTest) { $launchArgs += '--smoke-test' }
& '.venv\Scripts\python.exe' @launchArgs
exit $LASTEXITCODE
