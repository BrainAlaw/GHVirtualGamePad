"""Build an offline GUI bundle natively on Linux; never publish a Release."""
import io
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    if sys.platform != "linux": raise SystemExit("Build the Linux Qt bundle on Linux")
    subprocess.run(["cargo", "build", "--release", "--locked"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
        "--name", "GHVirtualGamePad", "--distpath", str(ROOT / "artifacts/frozen"),
        "--workpath", str(ROOT / "artifacts/pyinstaller-work"), "--specpath", str(ROOT / "artifacts"),
        "--add-data", str(ROOT / "gui/Main.qml") + ":gui",
        "--add-data", str(ROOT / "assets") + ":assets",
        "--add-data", str(ROOT / "tools/setup_linux.py") + ":tools",
        "--add-binary", str(ROOT / "target/release/ghvirtualgamepad") + ":bin",
        str(ROOT / "gui/app.py")], cwd=ROOT, check=True)
    destination = ROOT / "artifacts/ghvirtualgamepad-linux-x86_64-frozen-dev.tar.gz"
    with tarfile.open(destination, "w:gz") as archive:
        archive.add(ROOT / "artifacts/frozen/GHVirtualGamePad", arcname="ghvirtualgamepad/app")
        for relative in ["assets", "docs", "tools/install_linux.py", "LICENSE", "README.md", "THIRD_PARTY.md", "CHANGELOG.md"]:
            archive.add(ROOT / relative, arcname="ghvirtualgamepad/" + relative)
        launcher = b'#!/usr/bin/env bash\nset -euo pipefail\ncd -- "$(dirname -- "${BASH_SOURCE[0]}")"\nexec python3 tools/install_linux.py "$@"\n'
        info = tarfile.TarInfo("ghvirtualgamepad/install.sh"); info.mode = 0o755; info.size = len(launcher)
        archive.addfile(info, io.BytesIO(launcher))
    print(destination)


if __name__ == "__main__": build()
