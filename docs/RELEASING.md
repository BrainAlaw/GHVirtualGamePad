# Release verification

## 0.2.0-rc.2 scope

Native Linux and Windows backends are implemented. Do not describe demo tests as physical-device acceptance. Until the Windows two-guitar checklist passes, publish only a labelled **pre-release**.

### Verified locally during implementation

- Rust mapper tests and Windows output-layout test.
- Python protocol, profiles, pointer-driven QML mapping and installer safety tests.
- Windows 11: Interception enumerates keyboards without capturing input.
- Windows 11: two temporary controllers return distinct reports through real XInput; initial asynchronous enumeration is retried within a deadline.
- Windows frozen GUI smoke.
- Linux guitar operation reported working by the owner on the earlier functional build.

### Automated packaging checks

- **Check**: Rust fmt/clippy/tests and Python/Qt tests on Linux and Windows.
- **Build Linux installer**: frozen bundle; per-user install, repeated upgrade, retained prior version and GUI smoke.
- **Build Windows installer**: frozen application and Inno Setup; install, smoke, upgrade and uninstall with driver tasks explicitly disabled.

System-wide input filters are not installed on CI. Local native tests used already-installed drivers, not a fresh driver installation.

### Required before stable promotion

- Physical Windows guitars: separate capture, combinations, strum, whammy, no leaked original keys, stop/quit cleanup.
- Fresh driver install/reboot with security settings unchanged.
- Unplug/replug; Windows must stop/reselect, not trust recycled slots.
- Local host game with both players; optional Moonlight/streaming regression on each supported client platform.
- Linux permissions setup and two-player regression on the release bundle.

## Publishing

Run both installer workflows against the same commit after **Check** succeeds. Download artifacts, calculate SHA-256, and attach Linux tarball, Windows setup EXE and `SHA256SUMS.txt` to `v0.2.0-rc.2` at that exact commit. Do not substitute binaries from another commit.

Driver hashes/URLs: `tools/prepare_windows.py`. Notices and source/relinking instructions: `THIRD_PARTY.md`. Windows includes matching Interception library source and upstream terms.

Installers are not code-signed. Do not imply SmartScreen reputation/security certification or recommend disabling security controls.
