# Third-party notices and corresponding source

MIT covers GHVirtualGamePad's original code and icon only. Binary bundles include `notices` inside PyInstaller's `_internal` directory, with license texts and a dependency inventory. No third-party name implies endorsement.

## Qt / PySide6 / Shiboken6 6.10.2

The application uses the LGPLv3 options of Qt/PySide6 and dynamically loads their unmodified shared libraries. LGPLv3 and GPLv3 texts are included from upstream wheels. No commercial Qt license is claimed.

Corresponding unmodified source, upstream notices and build instructions:

- Qt 6.10.2 sources: https://download.qt.io/archive/qt/6.10/6.10.2/single/
- Qt submodules: https://download.qt.io/archive/qt/6.10/6.10.2/submodules/
- PySide/Shiboken 6.10.2: https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.2-src/
- Licensing: https://doc.qt.io/qt-6/licensing.html and https://doc.qt.io/qtforpython-6/licenses.html

This is a directory bundle, not a sealed single executable. You may replace compatible Qt/PySide6/Shiboken libraries under `_internal` with modified versions and reverse-engineer/debug the combination as permitted by LGPL. Rebuild using `requirements.txt` and `tools/build_frozen.py` or `tools/build_windows.py` for modified bindings. Application source is available in this repository/release source archive. No EULA restricts these rights.

## Python and PyInstaller

Python uses its PSF license and included component notices. PyInstaller uses GPLv2-or-later with a special exception allowing generated applications to use their chosen license. Build scripts collect installed package notices and Python's license.

Python source: https://www.python.org/downloads/source/
PyInstaller source/exception: https://github.com/pyinstaller/pyinstaller/tree/v6.16.0

## Rust dependencies

`Cargo.lock` fixes versions. Bundled inventory lists names, licenses and source repositories. License/copyright files are copied from exact Cargo packages. Rust standard library terms: https://github.com/rust-lang/rust/tree/master/LICENSES. Cargo package sources: https://crates.io/ by package and version.

## Windows dependencies

- **Interception 1.0.1**, Francisco Lopes: https://github.com/oblitum/Interception/tree/v1.0.1. We communicate solely through the official dynamic client API. Installer/client binaries are unmodified. Upstream license texts and matching tagged library source/build scripts are under `notices/Interception`. The DLL at `bin/drivers/interception.dll` is replaceable with an API-compatible build. Upstream binary redistribution terms are **non-commercial**; commercial use requires contacting the author. MIT does not override this restriction.
- **ViGEmBus 1.22.0**: unmodified installer from https://github.com/nefarius/ViGEmBus/releases/tag/v1.22.0, with upstream BSD-3-Clause terms and component licenses. Source: https://github.com/nefarius/ViGEmBus/tree/v1.22.0. Retired upstream.
- **vigem-client 0.1.4**, MIT, pure-Rust client: https://github.com/CasualX/vigem-client. License included with Rust notices.

Driver payload SHA-256 hashes are pinned in `tools/prepare_windows.py`. Builds never execute driver installers. Installing system drivers is an explicit end-user task requiring elevation; uninstalling the application leaves shared drivers intact.

## Other bundled libraries

Qt contains third-party software described in its source/wheel notices. Windows runtimes retain Microsoft redistribution terms. Linux frozen builds use system glibc, not bundled glibc. Optional legacy musl development packages use musl under MIT: https://git.musl-libc.org/cgit/musl/tree/COPYRIGHT.
