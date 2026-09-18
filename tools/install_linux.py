"""Per-user installation with retained versions and an atomic current pointer.

No root required. Profiles and udev rules are deliberately outside this installer.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

APP_ID = "io.github.BrainAlaw.GHVirtualGamePad"
MARKER = ".ghvirtualgamepad-install.json"


def desktop_quote(value):
    value = str(value)
    if any(c in value for c in "\n\r\0"):
        raise ValueError("Invalid desktop entry path")
    # Desktop string escaping precedes Exec argument unquoting (no shell is used).
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return '"' + escaped.replace("\\", "\\\\").replace("%", "%%") + '"'


def write_atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".ghvp-", dir=path.parent)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(value)
        stream.flush(); os.fsync(stream.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def install(source, data_home, dry_run=False):
    source = source.resolve()
    data_home = data_home.expanduser().resolve()
    destination = data_home / "ghvirtualgamepad"
    desktop = data_home / "applications" / f"{APP_ID}.desktop"
    current = destination / "current"
    if destination.exists() and not (destination / MARKER).is_file():
        raise RuntimeError("Installation directory is unmanaged; refusing to overwrite it")
    if desktop.exists() and "X-GHVirtualGamePad-Managed=true" not in desktop.read_text():
        raise RuntimeError("Desktop shortcut is unmanaged; refusing to overwrite it")
    if current.exists() and not current.is_symlink():
        raise RuntimeError("Current installation pointer is not a symlink")
    if source == destination or destination in source.parents:
        raise RuntimeError("Run the installer from a separate extracted archive")
    frozen = (source / "app" / "GHVirtualGamePad").is_file()
    required = ["assets/ghvirtualgamepad.svg", "LICENSE"]
    required += ["app/GHVirtualGamePad"] if frozen else ["gui/app.py", "gui/Main.qml", "bin/ghvirtualgamepad", "tools/setup_linux.py", "requirements.txt"]
    for relative in required:
        if not (source / relative).is_file(): raise RuntimeError(f"Missing installer payload: {relative}")
    if dry_run:
        return {"destination": str(destination), "shortcut": str(desktop), "frozen": frozen}
    releases = destination / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    write_atomic(destination / MARKER, json.dumps({"app_id": APP_ID, "version": 1}))
    release = Path(tempfile.mkdtemp(prefix="build-", dir=releases))
    # Retain old and failed versions rather than recursively deleting user paths.
    for relative in ["app"] if frozen else ["gui", "bin", "tools", "requirements.txt"]:
        item = source / relative
        if item.is_dir(): shutil.copytree(item, release / relative, ignore=shutil.ignore_patterns("__pycache__"))
        else: shutil.copy2(item, release / relative)
    for relative in ["assets", "LICENSE", "README.md", "THIRD_PARTY.md", "CHANGELOG.md"]:
        item = source / relative
        if item.is_dir(): shutil.copytree(item, release / relative)
        elif item.is_file(): shutil.copy2(item, release / relative)
    if frozen:
        executable = release / "app" / "GHVirtualGamePad"
        command = [executable]
    else:
        subprocess.run([sys.executable, "-m", "venv", str(release / ".venv")], check=True)
        executable = release / ".venv" / "bin" / "python"
        subprocess.run([str(executable), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(release / "requirements.txt")], check=True)
        (release / "bin" / "ghvirtualgamepad").chmod(0o755)
        command = [executable, release / "gui" / "app.py"]
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run([str(p) for p in command] + ["--demo", "--smoke-test"], env=environment, check=True, timeout=30)
    pointer = destination / (".current-" + release.name)
    pointer.symlink_to(release, target_is_directory=True)
    os.replace(pointer, current)
    # Point to current, keeping launchers stable across upgrades.
    command = [current / "app" / "GHVirtualGamePad"] if frozen else [current / ".venv" / "bin" / "python", current / "gui" / "app.py"]
    icon = current / "assets" / "ghvirtualgamepad.svg"
    entry = "\n".join(["[Desktop Entry]", "Type=Application", "Name=GHVirtualGamePad",
        "Comment=Map separate USB keyboards and guitars to virtual gamepads",
        "Exec=" + " ".join(desktop_quote(p) for p in command),
        "Icon=" + str(icon).replace("\\", "\\\\"), "Terminal=false", "Categories=Game;Utility;",
        "StartupNotify=true", "X-GHVirtualGamePad-Managed=true", ""])
    write_atomic(desktop, entry)
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(desktop.parent)], check=False)
    return {"destination": str(destination), "shortcut": str(desktop), "frozen": frozen}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if sys.platform != "linux": raise RuntimeError("This installer is for Linux only")
        if os.geteuid() == 0: raise RuntimeError("Run this per-user installer without sudo")
        data_home = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        print(json.dumps(install(args.source, data_home, args.dry_run), indent=2))
        print("Installation checked." if args.dry_run else "Installed. Open GHVirtualGamePad from the application menu. Saved profiles are unchanged.")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Installation failed: {error}. Previous versions and profiles have been retained.", file=sys.stderr)
        sys.exit(1)
