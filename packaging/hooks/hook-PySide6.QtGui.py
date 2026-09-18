"""Avoid unrelated PDF/image add-ons and the GPL-only virtual keyboard plugin."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)


def required(item):
    source = item[0].replace("\\", "/")
    name = Path(source).name.lower()
    if "qtvirtualkeyboard" in name:
        return False
    if "/imageformats/" in source:
        return name.startswith(("qsvg", "libqsvg", "qico", "libqico"))
    return True


binaries = [item for item in binaries if required(item)]
