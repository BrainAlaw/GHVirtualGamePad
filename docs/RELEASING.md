# Release verification

## 0.2.0 stable scope

Native Linux and Windows backends are implemented. The owner confirmed physical two-guitar gameplay on Windows after rc.2, including the GHWT:DE Extra compatibility mode. Stable status records that acceptance; it does not imply universal driver compatibility.

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

### Completed stable acceptance and remaining compatibility coverage

- Physical Windows two-guitar gameplay and GHWT:DE compatibility were owner-confirmed after rc.2.
- Linux permissions and two-player gameplay were owner-confirmed during development.
- Automated workflows cover mapping, GUI, installation, upgrade, Windows uninstall and two independent XInput outputs.
- Clean driver installation/reboot and varied Windows security policies remain compatibility coverage, not a blocker for stable 0.2.0.
- Optional Moonlight/streaming and receiver hotplug behavior should continue to be included in regression reports.

## Publishing

Run both installer workflows against the same commit after **Check** succeeds. Download artifacts, calculate SHA-256, and attach Linux tarball, Windows setup EXE and `SHA256SUMS.txt` to `v0.2.0` at that exact commit. Do not substitute binaries from another commit.

Driver hashes/URLs: `tools/prepare_windows.py`. Notices and source/relinking instructions: `THIRD_PARTY.md`. Windows includes matching Interception library source and upstream terms.

Installers are not code-signed. Do not imply SmartScreen reputation/security certification or recommend disabling security controls.
