# Changes

## Installation and publication preparation

- Added an original SVG icon and desktop application identity.
- Added a per-user Linux installer with menu integration, dry-run preview and retained versions. Profile paths remain unchanged.
- Added MIT licensing and an English project overview with accurate platform support status.
- Full native Windows support remains a prerequisite for the public binary release; Windows currently runs only the simulator.

## Mapping UI fix

- Fixed QML `AbstractButton.action` shadowing the mapping row's action name. Function buttons and clear buttons now address the explicit row function ID.
- Made binding values and unassigned binding placeholders clickable as well as function names.
- Reserved space for the vertical scrollbar so it cannot intercept clear-button clicks.
- Updated the code-drawn guitar using the supplied white-body reference and added D-pad, Extra and an explicit Whammy button. Hardware switch functions are still user-assigned, not inferred from the photo.
- Made diagram controls follow the same stopped-controller editing restriction as the mapping list, with explanatory text while controllers are running.
- Added real-pointer GUI regression coverage for all 15 function names and binding fields, the additional diagram buttons, clearing, Player 2 isolation and disabled editing during playback.

Profiles and the Rust/Linux controller backend are unchanged. Close the previous app, extract the updated test archive into a new directory and launch it; existing saved profiles remain in the user configuration directory and are reused.
