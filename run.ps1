param([switch]$SmokeTest)
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
$launchArgs = @('gui/app.py', '--demo')
if ($SmokeTest) { $launchArgs += '--smoke-test' }
& '.venv\Scripts\python.exe' @launchArgs
exit $LASTEXITCODE
