"""Build a native Windows onedir application; driver installation is an end-user choice."""
from pathlib import Path
import shutil
import subprocess
import sys

from collect_notices import collect
from prepare_windows import prepare, DESTINATION

ROOT = Path(__file__).resolve().parents[1]


def build():
    if sys.platform != "win32":
        raise SystemExit("Build Windows packages on Windows")
    prepare()
    subprocess.run(["cargo", "build", "--release", "--locked"], cwd=ROOT, check=True)
    from PySide6.QtGui import QGuiApplication, QIcon
    application = QGuiApplication([])
    icon = ROOT / "artifacts/ghvirtualgamepad.ico"
    if not QIcon(str(ROOT / "assets/ghvirtualgamepad.svg")).pixmap(256, 256).save(str(icon), "ICO"):
        raise RuntimeError("Cannot create application icon")
    del application
    collect(ROOT / "artifacts/notices")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
        "--name", "GHVirtualGamePad", "--icon", str(icon),
        "--distpath", str(ROOT / "artifacts/windows"), "--workpath", str(ROOT / "artifacts/windows-work"),
        "--specpath", str(ROOT / "artifacts"),
        "--additional-hooks-dir", str(ROOT / "packaging/hooks"),
        "--add-data", str(ROOT / "gui/Main.qml") + ";gui",
        "--add-data", str(ROOT / "assets") + ";assets",
        "--add-data", str(ROOT / "artifacts/notices") + ";notices",
        "--add-binary", str(ROOT / "target/release/ghvirtualgamepad.exe") + ";bin",
        "--add-binary", str(DESTINATION / "interception.dll") + ";bin/drivers",
        str(ROOT / "gui/app.py")], cwd=ROOT, check=True)
    bundle = ROOT / "artifacts/windows/GHVirtualGamePad"
    for relative in ("LICENSE", "README.md", "THIRD_PARTY.md", "CHANGELOG.md"):
        shutil.copy2(ROOT / relative, bundle / relative)
    shutil.copytree(DESTINATION / "licenses", bundle / "_internal/notices/Interception", dirs_exist_ok=True)
    shutil.copy2(DESTINATION / "Interception-v1.0.1-source.zip", bundle / "_internal/notices/Interception")
    subprocess.run([str(bundle / "GHVirtualGamePad.exe"), "--demo", "--smoke-test"], check=True, timeout=60)
    print(bundle)


if __name__ == "__main__":
    build()
