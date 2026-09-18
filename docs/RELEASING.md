# Release gates

The owner requests full Windows functionality before the first public binary release. Do not publish the simulator as a working Windows mapper. Repository publication and development CI artifacts are not a product release.

## Required before release

- Linux: installer/upgrade, both guitars, capture/release, reconnect, Moonlight and game tests.
- Windows: separate physical keyboards, suppression of their original keys, two virtual Xbox controllers, whammy, hotplug and fail-safe cleanup. Native Windows backend features are not currently delivered.
- Validate signed Windows driver dependencies and redistribution rights. Disabling Secure Boot, memory integrity or driver signature enforcement is not an acceptable normal installation step.
- Include dependency license texts and applicable source/relinking information for bundled Qt. MIT covers our code, not every dependency.
- Validate platform installers, icons, profile preservation and rollback on clean systems.
- Supply versioned release notes, SHA-256 checksums and accurate support statements.

## GitHub

Target: `BrainAlaw/GHVirtualGamePad`, public, MIT (owner approved).

Authenticate CLI interactively; do not store tokens here or in chat. Source may be published before binaries with the platform status table intact.

## Linux installation

`tools/package_linux.py` includes the cross-compiled Rust backend, source GUI and per-user installer. Initial installation downloads Qt. This is the current development bundle.

The installer retains version directories and switches a stable `current` symlink after dependency installation and a GUI smoke check. It never deletes profiles or udev rules. Retained versions can be started directly from their release directory. Automated removal is not enabled.

`tools/build_frozen.py` and the manual **Build Linux installer** workflow prepare a native Linux directory bundle with Python and Qt, test installation and upgrade, and upload a development artifact. They do not publish a Release. Binary redistribution notices and hardware acceptance gates remain applicable.

## Windows dependency findings

- Raw Input distinguishes physical keyboards, but `RIDEV_NOLEGACY` only affects the registering application's messages: https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-rawinputdevice
- HidHide does not hide keyboard/mouse input: https://docs.nefarius.at/projects/HidHide/FAQ/
- ViGEmBus provides Xbox output but is retired: https://docs.nefarius.at/projects/ViGEm/End-of-Life/
- VirtualPad is commercial: https://docs.nefarius.at/projects/VirtualPad/
- OpenInputBridge has MIT sources for Windows 11; upstream says WHQL-signed binaries are paid: https://github.com/Applet-LLC/OpenInputBridge

These findings do not establish a validated Windows stack. There are no purchased redistribution rights or signing arrangements for this project.
