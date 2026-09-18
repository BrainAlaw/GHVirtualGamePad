"""Render a demo screenshot without personal paths or hardware IDs."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gui"))
from app import Bridge
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

QQuickStyle.setStyle("Fusion")
application = QGuiApplication([])
with tempfile.TemporaryDirectory(prefix="ghvp-screenshot-") as config:
    binary = ROOT / "target/debug" / ("ghvirtualgamepad.exe" if sys.platform == "win32" else "ghvirtualgamepad")
    bridge = Bridge(True, binary, Path(config))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(str(ROOT / "gui/Main.qml"))
    def setup():
        for player in range(2):
            bridge.setPlayer(player)
            bridge.selectDevice(player + 1)
            bridge.demoDefaults()
        bridge.setPlayer(0)
        bridge.error("Ready to play. Independent mappings for Player 1 and Player 2.")
    def capture():
        if not engine.rootObjects()[0].grabWindow().save(str(ROOT / "docs/screenshot.png")):
            raise RuntimeError("Screenshot failed")
        application.quit()
    QTimer.singleShot(500, setup)
    QTimer.singleShot(1000, capture)
    application.aboutToQuit.connect(bridge.shutdown)
    application.exec()
