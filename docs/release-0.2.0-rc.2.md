# GHVirtualGamePad 0.2.0-rc.2

This release candidate adds the requested **GHWT:DE Extra fix** and includes all functionality from 0.2.0-rc.1.

## New in rc.2

- A per-player checkbox appears directly beside the **Extra** binding.
- Normally Extra outputs RB. With **GHWT:DE fix** enabled, Extra / guitar tilt outputs **D-pad Left only**, allowing GHWT:DE to bind it through the D-pad.
- Hover the information symbol for an explanation in the app.
- The option is saved independently for both players.
- Existing profiles remain compatible and load with the fix disabled.
- Documentation now treats local play as the default. Moonlight, VDI and other streaming software are optional.

## Downloads

- **Linux / CachyOS x86_64:** extract the `.tar.gz`, enter `ghvirtualgamepad`, run `bash install.sh` without sudo, or launch `app/GHVirtualGamePad` directly.
- **Windows x64:** run the setup EXE. It contains the app runtime and offers installation of missing ViGEmBus/Interception dependencies.
- **SHA256SUMS.txt:** verify both downloads. The Windows application installer is not Authenticode-signed.

## Release-candidate status

Automated tests cover the normal Extra → RB route, the compatibility Extra → D-pad Left route, profile migration, per-player GUI persistence, mapping logic and both installer paths. Linux guitar operation has been reported working. Windows keyboard enumeration and two independent XInput reports have been verified, but full physical two-guitar gameplay and fresh driver installation still require acceptance testing.

Windows users must not disable Secure Boot, Memory Integrity or signature enforcement. ViGEmBus is retired, and Interception is a legacy system-wide input filter whose upstream binary terms are for non-commercial use. Receivers must be selected on each Windows launch; mappings and the compatibility checkbox remain saved.
