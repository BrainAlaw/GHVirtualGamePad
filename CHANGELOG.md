# Changes

## 0.2.0-rc.1

- Native Windows per-keyboard input through Interception and two Xbox 360 outputs through ViGEmBus.
- Real XInput two-pad diagnostic and keyboard-enumeration check without capturing physical input.
- Bounded initial report retry during Windows device enumeration; normal backend exit releases native resources.
- Separate Windows profiles and explicit receiver reselection to avoid trusting persistent driver slots.
- Windows offline installer with icon, shortcuts, optional missing-driver installation and reboot notice. Profiles/shared drivers are retained on removal.
- Linux offline Python/Qt installer with menu integration, retained versions and automated upgrades.
- Dependency notices, source/relinking information, bilingual documentation and UI preview.
- Windows physical two-guitar and clean driver-install acceptance remain required before stable release.

## Installation and publication preparation

- Added an original SVG icon and desktop application identity.
- Added a per-user Linux installer with menu integration, dry-run preview and retained versions. Profile paths remain unchanged.
- Added MIT licensing and an English project overview with accurate platform support status.
- At that development stage Windows was simulator-only; native support was added in 0.2.0-rc.1 above.

## Mapping UI fix

- Fixed QML `AbstractButton.action` shadowing the mapping row's action name. Function buttons and clear buttons now address the explicit row function ID.
- Made binding values and unassigned binding placeholders clickable as well as function names.
- Reserved space for the vertical scrollbar so it cannot intercept clear-button clicks.
- Updated the code-drawn guitar using the supplied white-body reference and added D-pad, Extra and an explicit Whammy button. Hardware switch functions are still user-assigned, not inferred from the photo.
- Made diagram controls follow the same stopped-controller editing restriction as the mapping list, with explanatory text while controllers are running.
- Added real-pointer GUI regression coverage for all 15 function names and binding fields, the additional diagram buttons, clearing, Player 2 isolation and disabled editing during playback.

Profiles and the Rust/Linux controller backend are unchanged. Close the previous app, extract the updated test archive into a new directory and launch it; existing saved profiles remain in the user configuration directory and are reused.
