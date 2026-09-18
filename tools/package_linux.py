"""Create a Linux test bundle with a prebuilt Rust backend, no build tools required."""
import io
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = '''#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import PySide6; assert PySide6.__version__ == "6.10.2"' 2>/dev/null; then
    .venv/bin/python -m pip install -r requirements.txt --disable-pip-version-check
fi
exec .venv/bin/python gui/app.py "$@"
'''


def package():
    binary = ROOT / "target/x86_64-unknown-linux-musl/release/ghvirtualgamepad"
    if not binary.exists(): raise SystemExit("Build the Linux musl release first")
    destination = ROOT / "artifacts/ghvirtualgamepad-linux-x86_64.tar.gz"
    destination.parent.mkdir(exist_ok=True)
    prefix = "ghvirtualgamepad"
    with tarfile.open(destination, "w:gz") as archive:
        def normalize(info):
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            return info
        for relative in ["gui/app.py", "gui/Main.qml", "assets/ghvirtualgamepad.svg", "tools/setup_linux.py", "tools/install_linux.py", "requirements.txt", "README.md", "CHANGELOG.md", "THIRD_PARTY.md", "LICENSE"]:
            archive.add(ROOT / relative, arcname=f"{prefix}/{relative}", filter=normalize)
        archive.add(ROOT / "docs", arcname=f"{prefix}/docs", filter=lambda info: info if info.isdir() else normalize(info))
        def add_bytes(name, data, mode):
            info = tarfile.TarInfo(f"{prefix}/{name}")
            info.size = len(data); info.mode = mode
            archive.addfile(info, io.BytesIO(data))
        add_bytes("bin/ghvirtualgamepad", binary.read_bytes(), 0o755)
        add_bytes("launch.sh", LAUNCHER.encode(), 0o755)
        add_bytes("install.sh", b'#!/usr/bin/env bash\nset -euo pipefail\ncd -- "$(dirname -- "${BASH_SOURCE[0]}")"\nexec python3 tools/install_linux.py "$@"\n', 0o755)
    print(destination)


if __name__ == "__main__": package()
