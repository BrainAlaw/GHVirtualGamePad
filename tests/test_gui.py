import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "offscreen")
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gui"))
from app import Bridge, ACTIONS
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtCore import Qt, QPointF
from PySide6.QtTest import QTest

APPLICATION = QGuiApplication.instance() or QGuiApplication([])
QQuickStyle.setStyle("Fusion")


class Gui(unittest.TestCase):
    def find_item(self, window, name):
        pending = [window.contentItem()]
        while pending:
            item = pending.pop()
            if item.objectName() == name: return item
            pending.extend(item.childItems())
        return None

    def click(self, window, name):
        item = self.find_item(window, name)
        self.assertIsNotNone(item, name)
        if name.startswith(("mapping-", "binding-", "clear-", "ghwtde-extra-fix")):
            scroll = self.find_item(window, "mappingScroll")
            viewport = scroll.property("contentItem")
            center = item.mapToScene(QPointF(item.width()/2, item.height()/2))
            top = viewport.mapToScene(QPointF(0, 0)).y()
            offset = viewport.property("contentY") + center.y() - top - viewport.height()/2
            limit = max(0, viewport.property("contentHeight") - viewport.height())
            viewport.setProperty("contentY", max(0, min(limit, offset)))
            QTest.qWait(20)
        point = item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
        APPLICATION.processEvents()

    def wait(self, predicate):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            APPLICATION.processEvents()
            if predicate(): return
            time.sleep(0.01)
        self.fail("GUI condition timed out")

    def test_mapping_save_reload_and_qml(self):
        executable = ROOT / "target" / "debug" / ("ghvirtualgamepad.exe" if sys.platform == "win32" else "ghvirtualgamepad")
        with tempfile.TemporaryDirectory() as folder:
            bridge = Bridge(True, executable, folder)
            engine = QQmlApplicationEngine()
            warnings = []
            engine.warnings.connect(lambda messages: warnings.extend(str(m) for m in messages))
            engine.rootContext().setContextProperty("bridge", bridge)
            engine.load(str(ROOT / "gui" / "Main.qml"))
            try:
                self.assertTrue(engine.rootObjects())
                self.wait(lambda: len(bridge.devices_data) == 3)
                bridge.selectDevice(1)
                self.wait(lambda: bridge.selected[0] == "demo-1")
                window = engine.rootObjects()[0]
                # Real pointer input catches QML name shadowing that direct slot calls miss.
                for action in ACTIONS:
                    for prefix in ("mapping-", "binding-"):
                        self.click(window, prefix + action)
                        self.assertEqual(bridge.learning, action, prefix + action)
                        bridge.cancelLearn()
                for action in ("up", "down", "left", "right", "extra", "start", "select", "whammy"):
                    self.click(window, "guitar-" + action)
                    self.assertEqual(bridge.learning, action)
                    bridge.cancelLearn()
                self.click(window, "mapping-green")
                bridge.demoKey(Qt.Key_A, True)
                self.wait(lambda: "green" in bridge.profiles[0]["bindings"])
                bridge.demoKey(Qt.Key_A, False)
                self.click(window, "clear-green")
                self.assertNotIn("green", bridge.profiles[0]["bindings"])
                bridge.demoDefaults()
                self.click(window, "ghwtde-extra-fix")
                self.wait(lambda: bridge.profiles[0]["ghwtde_extra_fix"])
                first_profile = json.loads(json.dumps(bridge.profiles[0]))
                bridge.setPlayer(1)
                bridge.selectDevice(2)
                self.wait(lambda: bridge.selected[1] == "demo-2")
                self.click(window, "binding-extra")
                self.assertEqual(bridge.learning, "extra")
                bridge.demoKey(Qt.Key_A, True)
                self.wait(lambda: "extra" in bridge.profiles[1]["bindings"])
                bridge.demoKey(Qt.Key_A, False)
                self.assertEqual(bridge.profiles[0], first_profile)
                bridge.toggle()
                self.wait(lambda: bridge.running)
                self.click(window, "mapping-extra")
                self.click(window, "guitar-extra")
                self.assertEqual(bridge.learning, "")
                bridge.stop()
                self.wait(lambda: not bridge.running)
                bridge.setPlayer(0)
                bridge.demoKey(Qt.Key_Space, True)
                self.wait(lambda: bridge.states[0]["whammy"] > 0.1)
                bridge.releaseDemoKeys()
                self.wait(lambda: bridge.states[0]["whammy"] == 0)
                bridge.save()
                data = json.loads(bridge.profile_path.read_text())
                self.assertEqual(data["profiles"][0]["bindings"]["green"]["code"], 30)
                self.assertTrue(data["profiles"][0]["ghwtde_extra_fix"])
                bridge.exportReport()
                report = json.loads((Path(folder) / "diagnostics.json").read_text())
                self.assertNotIn("recent", report)
                screenshot = ROOT / "artifacts" / "gui-preview.png"
                screenshot.parent.mkdir(exist_ok=True)
                self.assertTrue(engine.rootObjects()[0].grabWindow().save(str(screenshot)))
                self.assertEqual(warnings, [])
            finally:
                engine.rootObjects()[0].close()
                bridge.shutdown()
                del engine
            restored = Bridge(True, executable, folder)
            try:
                self.assertEqual(restored.profiles[0]["bindings"]["green"]["code"], 30)
                self.assertTrue(restored.profiles[0]["ghwtde_extra_fix"])
                self.wait(lambda: restored.selected[0] == "demo-1")
            finally: restored.shutdown()


if __name__ == "__main__": unittest.main()
