$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$cargoExecutable = Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe'
$rustupExecutable = Join-Path $env:USERPROFILE '.cargo\bin\rustup.exe'
& $rustupExecutable target add x86_64-unknown-linux-musl
if ($LASTEXITCODE -ne 0) { throw 'Linux target installation failed.' }
$compilerPath = (& $rustupExecutable which rustc).Trim()
$toolchainRoot = Split-Path -Parent (Split-Path -Parent $compilerPath)
$env:CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER = Join-Path $toolchainRoot 'lib\rustlib\x86_64-pc-windows-gnu\bin\rust-lld.exe'
& $cargoExecutable build --locked --release --target x86_64-unknown-linux-musl
if ($LASTEXITCODE -ne 0) { throw 'Linux cross-compilation failed.' }
