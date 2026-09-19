# GHVirtualGamePad 0.2.0

The first stable release turns separate USB keyboard-mode guitars into independent virtual controllers on Linux and Windows. Local play is the default; Moonlight, VDI and other streaming software are optional.

## Highlights

- Two independent players with separate devices, mappings, live state and saved profiles.
- Interactive guitar diagram and complete clickable binding list.
- Five frets, strum, D-pad, Start, Select, Extra and digital-to-analog whammy.
- Optional per-player **GHWT:DE Extra fix**: Extra / guitar tilt outputs D-pad Left instead of RB.
- Exclusive capture of selected guitar keyboards while controllers run.
- Linux evdev/uinput output and Windows XInput Xbox 360 output.
- Offline application runtimes, icons, desktop integration and installers for both platforms.

## Verification

- The owner confirmed physical two-guitar gameplay on both Linux and Windows, including the GHWT:DE compatibility option.
- Automated Linux and Windows suites cover mapping, profile migration, protocol behavior and pointer-driven GUI interaction.
- Installer workflows verify Linux installation/upgrade and Windows installation/upgrade/uninstall without silently installing system drivers on CI.
- Native Windows diagnostics verified two distinct virtual controller reports through XInput.

This status does not guarantee every receiver or Windows security policy. ViGEmBus is retired and Interception is a legacy system-wide input filter. Never disable Secure Boot, Memory Integrity or signature enforcement to force a blocked driver to load. Interception's upstream binary redistribution terms are for non-commercial use.

## Downloads

- `ghvirtualgamepad-0.2.0-linux-x86_64.tar.gz`: extract, enter `ghvirtualgamepad`, run `bash install.sh` without sudo, or launch `app/GHVirtualGamePad` directly.
- `GHVirtualGamePad-0.2.0-windows-x64-setup.exe`: application runtime, icon, shortcuts and optional missing-driver setup.
- `SHA256SUMS.txt`: checksums for both installers. The Windows application installer is not Authenticode-signed.

Existing rc profiles remain compatible. The GHWT:DE option is saved per player and defaults to disabled for older profiles. Windows receiver slots must still be selected each session because Interception slot numbers are not persistent USB identities.
