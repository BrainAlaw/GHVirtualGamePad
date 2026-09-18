<p align="center"><img src="assets/ghvirtualgamepad.svg" width="128" alt="GHVirtualGamePad icon"></p>

# GHVirtualGamePad

Turn two USB keyboard-mode guitars into two independent virtual gamepads.

Designed for DOYO guitars, Guitar Hero World Tour: Definitive Edition and Moonlight on Linux. Each player selects a separate receiver, teaches the app their controls, and starts a virtual controller. No hardcoded keyboard layout is required.

## Platform status

| Platform | Status |
| --- | --- |
| Linux / CachyOS | Hardware functionality reported working by the owner; automated core and GUI tests pass. |
| Windows | GUI and simulator only. Physical keyboard capture and virtual Xbox output are **not implemented yet**. |
| Public binary release | Pending full Windows support and installer validation. |

The hardware report is not a certification of every distribution, receiver or streaming configuration. The Linux output is an evdev/uinput gamepad with an Xbox-compatible layout, not an emulation of the Xbox USB protocol. The streaming host determines the controller type exposed to the game.

## Features

- Separate Player 1 and Player 2 devices, mappings and states.
- Live USB receiver list, grouping a receiver's input interfaces.
- Click-to-bind guitar diagram and complete mapping list.
- Five frets, strum, D-pad, Start, Select, Extra and whammy.
- Digital whammy converted to a smooth axis with configurable rise and return timing.
- Exclusive Linux capture while running, preventing duplicate keyboard input.
- Neutral state on disconnection and reconnect at the same USB port.
- Saved profiles, live feedback and diagnostic snapshots without keystroke history.

The operating system must see separate devices. Software cannot separate two guitars if one receiver merges both into identical, indistinguishable keyboard events.

## Install on Linux

Extract the development Linux x86_64 archive and run **without sudo**:

```bash
bash install.sh
```

Then open **GHVirtualGamePad** from the application menu. The installer adds the icon and shortcut, installs into your user data directory, and retains previous versions. Saved profiles are unchanged. `bash install.sh --dry-run` previews the destination without installing.

The current development bundle needs Python 3.10–3.14 and internet access during installation to download Qt into its private environment. Rust is not required. A separate frozen-bundle build is being prepared to include Python and Qt; it must be built and tested on Linux before distribution.

Portable use remains available with `bash launch.sh`. Installation is a convenience, not a requirement for saving profiles or playing. There is no expiry or online activation.

### First use

1. Put the guitar in keyboard mode and select its receiver for Player 1.
2. If access is denied, click **Enable device access** and authorize the udev configuration through polkit.
3. Click a fret, function name or binding field, then press and release its physical control. Unused functions can stay unassigned.
4. Map whammy as a button. **Press (ms)** is its travel time to full deflection; **Return (ms)** is its return time.
5. Repeat for Player 2 with the other receiver. One player also works alone.
6. Click **Save profiles**, release all buttons, then **Start controllers**.
7. Start Moonlight and map the controllers in the host game.

Stop controllers before editing mappings. Closing the program releases captured devices. Ctrl+Esc stops them while the window has focus; it is not a global Wayland shortcut. Do not select your everyday keyboard or a receiver shared with your mouse. Capture applies to the selected receiver's interfaces.

## Profiles and upgrades

Profiles live outside the application folder in Qt's user configuration location. **Save profiles** displays the exact path. On Linux this is normally `$XDG_CONFIG_HOME/GHVirtualGamePad/GHVirtualGamePad`, defaulting to `~/.config/GHVirtualGamePad/GHVirtualGamePad`.

Back up `profiles.json` before upgrading. Simulation uses `demo-profiles.json`. The installer never deletes either file. Keep the working portable archive as a fallback. Moving a receiver to another USB port requires reselection and may require access setup again.

## Controller layout

| Function | Virtual output |
| --- | --- |
| Green / Red / Yellow / Blue / Orange | A / B / Y / X / LB |
| Strum up/down | D-pad up/down |
| D-pad | D-pad |
| Start / Select / Extra | Start / Back / RB |
| Digital whammy | Right stick Y: neutral → positive full scale → neutral |

## Development

Rust implements mapping, simulation and Linux evdev/uinput. Qt Quick/QML provides the GUI with a thin PySide6 shell. The GUI talks to its unprivileged Rust child over private pipes. There is no network listener or persistent root daemon.

Windows simulator: `./run.ps1`. Linux from source: `bash run.sh`.

```text
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo build --locked
python -m unittest discover -s tests -v
python gui/app.py --demo --smoke-test
```

Python commands need the environment from `requirements.txt`. See [Polish technical documentation](docs/README.pl.md), [changes](CHANGELOG.md), [release gates](docs/RELEASING.md) and [dependency notices](THIRD_PARTY.md).

## License

Original code and icon: [MIT](LICENSE). Dependencies retain their own licenses. Not affiliated with DOYO, Microsoft, Xbox, Guitar Hero or Moonlight.
