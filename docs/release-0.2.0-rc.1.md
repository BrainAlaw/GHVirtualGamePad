# GHVirtualGamePad 0.2.0-rc.1

Two keyboard-mode guitars, two independent gamepads — with native Linux and Windows backends.

## Downloads

- **Linux / CachyOS x86_64:** extract the `.tar.gz`, enter `ghvirtualgamepad`, run `bash install.sh` without sudo. Or run `app/GHVirtualGamePad` directly. System Python 3.10+ is needed by the installer; the application runtime is bundled. Requires glibc 2.39+ and desktop graphics libraries.
- **Windows x64:** run the `-setup.exe`. Includes Python/Qt, an app icon, shortcuts and optional installation of missing ViGEmBus/Interception drivers. Save work and reboot after driver installation. No compiler or Python installation required.
- **SHA256SUMS.txt:** checksums for the two installers. The application installer is not Authenticode-signed.

## Included

- Separate device selection and profiles for both players.
- Interactive guitar diagram and complete clickable binding list.
- Digital whammy converted to a smooth right-stick axis.
- Exclusive selected-keyboard capture while controllers run.
- Persistent mappings and desktop integration.
- English README, Polish instructions, dependency notices and corresponding-source links.

## Verification and release-candidate status

Linux guitar operation was reported working by the owner. Automated checks cover mapping, profiles, protocol and GUI; installer workflows check installation/upgrade, and Windows application uninstall without driver removal.

Windows has a real backend, not just a demo. Keyboard enumeration and two distinct virtual gamepad reports were checked through native XInput on Windows 11. **Physical two-guitar gameplay, suppression and a clean driver installation/reboot still require acceptance testing.** This is intentionally a pre-release, not stable certification.

## Important Windows notes

- ViGEmBus is retired upstream. Interception is a legacy system-wide keyboard/mouse filter. Compatibility depends on Windows policy and security settings; never disable Secure Boot, Memory Integrity or signature enforcement to make it load.
- The project's original code/icon are MIT. Interception's upstream binary terms are for **non-commercial use**; commercial use needs a separate upstream license.
- Reselect the guitar receivers on each launch and after reconnecting: Windows driver slots are not stable USB identities. Mappings remain saved. Windows multi-slot receiver aggregation is not implemented.
- Never select your everyday keyboard or a shared keyboard/mouse receiver. Preview passes keys through; active controller mode captures them.
- Uninstall leaves shared drivers and profiles untouched. Close normally; force-killing the process may leave a virtual controller until restart.

## Existing test-build users

Click **Save profiles**, back up the displayed config folder, close the old app, and install. Profiles live outside the application folder; Linux installation preserves them and keeps prior installed versions. The old test build does not expire. Linux and Windows use different physical input codes, so teach Windows bindings separately.

Start controllers before connecting Moonlight. Map the resulting A/B/Y/X/LB frets, D-pad strum and Right Y whammy in the host game.

**Następny test:** dwie fizyczne gitary na Windowsie — progi jednocześnie, strum, whammy, brak wpisywania klawiszy podczas gry oraz stop/ponowny start. To ostatni etap przed oznaczeniem wersji jako stabilnej.
