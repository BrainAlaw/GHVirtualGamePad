"""Collect installed distribution and locked Rust dependency license notices."""
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def collect(destination):
    destination.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(subprocess.check_output(["cargo", "metadata", "--locked", "--format-version", "1"], cwd=ROOT))
    inventory = []
    rust_version = subprocess.check_output(["rustc", "--version"], text=True).strip()
    inventory.append({"name": "Rust toolchain", "version": rust_version})
    inventory.append({"name": "Python", "version": platform.python_version()})
    rust_root = Path(subprocess.check_output(["rustc", "--print", "sysroot"], text=True).strip())
    rust_notices = rust_root / "share/doc/rust/licenses"
    if rust_notices.is_dir():
        shutil.copytree(rust_notices, destination / "rust-toolchain", dirs_exist_ok=True)
    else:
        for name in ("MIT.txt", "Apache-2.0.txt"):
            url = f'https://raw.githubusercontent.com/rust-lang/rust/{rust_version.split()[1]}/LICENSES/{name}'
            target = destination / "rust-toolchain" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(url, timeout=60) as response:
                target.write_bytes(response.read())
    # Wheels can contain only the commercial-license placeholder. Collect the actual
    # open-source terms and embedded third-party notices from the matching Qt sources.
    for repository in ("qtbase", "qtdeclarative", "qtsvg", "pyside-setup"):
        source = ROOT / "artifacts/source-cache" / f"{repository}-6.10.2.zip"
        source.parent.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            url = f"https://codeload.github.com/qt/{repository}/zip/refs/tags/v6.10.2"
            if repository == "pyside-setup":
                url = "https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.2-src/pyside-setup-everywhere-src-6.10.2.zip"
            with urllib.request.urlopen(url, timeout=180) as response, source.open("wb") as output:
                shutil.copyfileobj(response, output)
        with zipfile.ZipFile(source) as archive:
            for member in archive.namelist():
                relative = Path(*Path(member).parts[1:])
                if ".." in relative.parts or member.endswith("/"):
                    continue
                if any(part.lower() == "licenses" for part in relative.parts) or relative.name.lower().startswith(("license", "copying", "copyright", "notice", "qt_attribution")):
                    target = destination / "qt-source-notices" / repository / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(member))
    for package in metadata["packages"]:
        if package["name"] == "ghvirtualgamepad":
            continue
        inventory.append({key: package.get(key) for key in ("name", "version", "license", "repository")})
        folder = Path(package["manifest_path"]).parent
        for source in folder.iterdir():
            if source.is_file() and source.name.lower().startswith(("license", "copying", "notice", "copyright")):
                target = destination / "rust" / f'{package["name"]}-{package["version"]}' / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    for name in ("PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "PyInstaller"):
        distribution = importlib.metadata.distribution(name)
        inventory.append({"name": name, "version": distribution.version})
        for relative in distribution.files or []:
            if any(part.lower() in ("licenses", "license") for part in relative.parts) or relative.name.lower().startswith(("license", "copying", "notice")):
                source = Path(distribution.locate_file(relative))
                if source.is_file():
                    target = destination / "python" / name / Path(*[part for part in relative.parts if part not in ("..", ".")])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    for source in (Path(sys.base_prefix) / "LICENSE.txt", Path(sys.base_prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "LICENSE.txt"):
        if source.is_file():
            shutil.copy2(source, destination / "Python-LICENSE.txt")
    if not (destination / "Python-LICENSE.txt").exists():
        url = f"https://raw.githubusercontent.com/python/cpython/v{platform.python_version()}/LICENSE"
        with urllib.request.urlopen(url, timeout=60) as response:
            (destination / "Python-LICENSE.txt").write_bytes(response.read())
    (destination / "inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    shutil.copy2(ROOT / "THIRD_PARTY.md", destination / "README.md")


if __name__ == "__main__":
    collect(ROOT / "artifacts/notices")
