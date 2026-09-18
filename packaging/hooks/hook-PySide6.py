"""Use the standard Qt runtime collector without the unused Mesa software-GL DLL."""
from PyInstaller.utils.hooks.qt import pyside6_library_info, ensure_single_qt_bindings_package

ensure_single_qt_bindings_package("PySide6")
hiddenimports = ["shiboken6", "inspect", "PySide6.support.deprecated"]
binaries = [item for item in pyside6_library_info.collect_extra_binaries()
            if "opengl32sw" not in item[0].lower()]
