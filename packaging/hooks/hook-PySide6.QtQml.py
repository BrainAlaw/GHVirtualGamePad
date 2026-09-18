"""Ship only the QML modules used by this UI, not unrelated Qt add-ons."""
from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries = [item for item in binaries if "/qmltooling/" not in item[0].replace("\\", "/")]
qml_binaries, qml_datas = pyside6_library_info.collect_qtqml_files()


def required(item):
    destination = item[1].replace("\\", "/")
    relative = destination.split("/qml/", 1)[-1]
    if relative in ("QtQml", "QtQuick"):
        return True
    return any(relative == module or relative.startswith(module + "/") for module in (
        "QtQml/Models", "QtQml/WorkerScript", "QtQuick/Controls", "QtQuick/Templates",
        "QtQuick/Layouts", "QtQuick/Window", "QtQuick/NativeStyle", "QtQuick/Effects",
    ))


binaries += [item for item in qml_binaries if required(item)]
datas += [item for item in qml_datas if required(item)]
