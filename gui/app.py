"""Qt/QML shell. Device access, mapping and controller state live in Rust."""
import argparse
import json
import os
from pathlib import Path
import sys

from PySide6.QtCore import QObject, Property, QProcess, QSaveFile, QIODevice, QStandardPaths, QTimer, Signal, Slot, Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle

ROOT = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
ACTIONS = ["green", "red", "yellow", "blue", "orange", "strum_up", "strum_down", "start", "select", "up", "down", "left", "right", "extra", "whammy"]
DEMO_KEYS = {Qt.Key_A: 30, Qt.Key_S: 31, Qt.Key_D: 32, Qt.Key_F: 33, Qt.Key_G: 34, Qt.Key_Up: 103, Qt.Key_Down: 108, Qt.Key_Return: 28, Qt.Key_Backspace: 14, Qt.Key_Left: 105, Qt.Key_Right: 106, Qt.Key_Space: 57}


def default_profile():
    return {"bindings": {}, "rise_ms": 250.0, "return_ms": 180.0}


def validate_config(data):
    if data.get("version") != 1 or len(data.get("profiles", [])) != 2 or len(data.get("selected", [])) != 2:
        raise ValueError("Unsupported profile file")
    for profile in data["profiles"]:
        for key in ("rise_ms", "return_ms"):
            if not isinstance(profile[key], (int, float)) or not 10 <= profile[key] <= 10000:
                raise ValueError("Invalid whammy timing")
        if not isinstance(profile["bindings"], dict):
            raise ValueError("Invalid bindings")
        for action, binding in profile["bindings"].items():
            if action not in ACTIONS or binding["kind"] not in (1, 3) or not isinstance(binding["source"], str):
                raise ValueError("Invalid binding")
            if not all(isinstance(binding[k], int) for k in ("code", "rest", "full")):
                raise ValueError("Invalid binding values")
            if not 0 <= binding["code"] <= 65535 or binding["rest"] == binding["full"]:
                raise ValueError("Invalid binding range")
    if not all(isinstance(item, str) for item in data["selected"]):
        raise ValueError("Invalid device selection")
    return data


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    output = QSaveFile(str(path))
    if not output.open(QIODevice.WriteOnly):
        raise OSError(output.errorString())
    payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    if output.write(payload) != len(payload) or not output.commit():
        raise OSError(output.errorString())


class Bridge(QObject):
    changed = Signal()
    stateChanged = Signal()

    def __init__(self, demo, executable, config_dir=None):
        super().__init__()
        self.demo = demo
        self.devices_data = [{"id": "", "label": "Select an input device…", "sources": []}]
        self.selected = ["", ""]
        self.choices = ["", ""]
        self.remembered = ["", ""]
        self.profiles = [default_profile(), default_profile()]
        self.states = [{"buttons": {}, "whammy": 0}, {"buttons": {}, "whammy": 0}]
        self.active = 0
        self.running = False
        self.learning = ""
        self.message = "Starting backend…"
        self.recent = []
        self.connected = [False, False]
        self.buffer = b""
        self.held = {}
        self.setup_process = None
        self.config_dir = Path(config_dir) if config_dir else Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))
        self.profile_path = self.config_dir / ("demo-profiles.json" if demo else "profiles.json")
        self.load_error = None
        try:
            if self.profile_path.exists():
                data = validate_config(json.loads(self.profile_path.read_text(encoding="utf-8")))
                self.profiles = data["profiles"]
                self.remembered = data["selected"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.load_error = f"Cannot load saved profile: {error}. Original file was preserved."
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.errorOccurred.connect(lambda _: self.error(self.process.errorString()))
        self.process.finished.connect(self.finished)
        self.process.start(str(executable), ["--demo"] if demo else [])
        self.learn_timer = QTimer(self)
        self.learn_timer.setSingleShot(True)
        self.learn_timer.timeout.connect(self.cancelLearn)

    @Property(bool, constant=True)
    def demoMode(self): return self.demo
    @Property("QVariantList", notify=changed)
    def devices(self): return self.devices_data
    @Property(int, notify=changed)
    def player(self): return self.active
    @Property(bool, notify=changed)
    def isRunning(self): return self.running
    @Property(str, notify=changed)
    def status(self): return self.message
    @Property(str, notify=changed)
    def learningAction(self): return self.learning
    @Property("QVariantMap", notify=changed)
    def bindings(self): return self.profiles[self.active]["bindings"]
    @Property("QVariantMap", notify=stateChanged)
    def pad(self): return self.states[self.active]
    @Property("QVariantList", notify=changed)
    def assignments(self): return self.selected
    @Property("QVariantList", notify=changed)
    def deviceChoices(self): return self.choices
    @Property(float, notify=changed)
    def riseMs(self): return self.profiles[self.active]["rise_ms"]
    @Property(float, notify=changed)
    def returnMs(self): return self.profiles[self.active]["return_ms"]

    def error(self, message):
        self.message = message
        self.changed.emit()

    def send(self, op, **kwargs):
        if self.process.state() != QProcess.Running:
            self.error("Backend is unavailable. Build it with cargo build first.")
            return
        self.process.write((json.dumps({"op": op, **kwargs}) + "\n").encode())

    def sync_profile(self, player):
        self.send("profile", player=player, profile=self.profiles[player])

    @Slot()
    def read_output(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                self.handle(json.loads(line))
            except (ValueError, KeyError, TypeError) as error:
                self.error(f"Invalid backend response: {error}")

    def handle(self, event):
        kind = event["type"]
        if kind == "hello":
            for player in range(2): self.sync_profile(player)
            self.message = self.load_error or ("Simulation · no system gamepads are created" if self.demo else "Choose a receiver, then click a control to map it")
        elif kind == "devices":
            self.devices_data = [{"id": "", "label": "Select an input device…", "sources": []}] + event["devices"]
            available = {d["id"] for d in event["devices"]}
            for p in range(2):
                if self.remembered[p] and self.remembered[p] in available and not self.selected[p]:
                    self.choices[p] = self.remembered[p]
                    self.send("select", player=p, device=self.remembered[p])
                    self.remembered[p] = ""
        elif kind == "status":
            self.running = event["running"]
            self.selected = event["selected"]
        elif kind == "state":
            self.states = event["players"]
            self.stateChanged.emit()
            return
        elif kind == "error": self.message = event["message"]
        elif kind == "connection":
            self.connected[event["player"]] = event["connected"]
            self.message = f"Player {event['player']+1}: {'reconnected' if event['connected'] else 'disconnected; waiting for the same USB port'}"
        elif kind == "input":
            # Never retain arbitrary keyboard events outside an explicit mapping session.
            if self.learning and event["player"] == self.active:
                if (event["kind"] == 1 and event["value"] == 1) or (event["kind"] == 3 and event["value"] != 0):
                    rest = 0
                    full = event["value"] if event["kind"] == 3 else 1
                    if event["kind"] == 3 and self.learning == "whammy":
                        self.message = "Whammy is configured as a digital input: press its button."
                    else:
                        self.profiles[self.active]["bindings"][self.learning] = {"source": event["source"], "kind": event["kind"], "code": event["code"], "rest": rest, "full": full}
                        self.message = f"Mapped {self.learning}: {event['source']} / {event['code']}"
                        self.learning = ""
                        self.learn_timer.stop()
                        self.sync_profile(self.active)
        self.changed.emit()

    @Slot()
    def read_error(self):
        message = bytes(self.process.readAllStandardError()).decode(errors="replace").strip()
        if message: self.error(message[-1000:])

    @Slot()
    def finished(self):
        self.running = False
        self.states = [{"buttons": {}, "whammy": 0}, {"buttons": {}, "whammy": 0}]
        self.error("Backend stopped; input devices have been released.")
        self.stateChanged.emit()

    @Slot(int)
    def setPlayer(self, player):
        if player not in (0, 1): return
        self.releaseDemoKeys()
        self.cancelLearn()
        self.active = player
        self.changed.emit(); self.stateChanged.emit()

    @Slot(int)
    def selectDevice(self, index):
        if self.running or not 0 <= index < len(self.devices_data): return
        self.releaseDemoKeys()
        self.cancelLearn()
        self.choices[self.active] = self.devices_data[index]["id"]
        self.changed.emit()
        self.send("select", player=self.active, device=self.devices_data[index]["id"])

    @Slot(str)
    def learn(self, action):
        if self.running or action not in ACTIONS: return
        if not self.selected[self.active] or self.choices[self.active] != self.selected[self.active]:
            self.error("Select a device for this player first."); return
        self.learning = action
        self.message = f"Press the physical control for {action} (15 seconds)…"
        self.learn_timer.start(15000)
        self.changed.emit()

    @Slot()
    def cancelLearn(self):
        self.learning = ""
        self.learn_timer.stop()
        self.changed.emit()

    @Slot(str)
    def clearBinding(self, action):
        if self.running: return
        self.profiles[self.active]["bindings"].pop(action, None)
        self.sync_profile(self.active); self.changed.emit()

    @Slot(float, float)
    def setTiming(self, rise, fall):
        if self.running: return
        self.profiles[self.active]["rise_ms"] = max(10, min(10000, rise))
        self.profiles[self.active]["return_ms"] = max(10, min(10000, fall))
        self.sync_profile(self.active); self.changed.emit()

    @Slot()
    def toggle(self):
        self.cancelLearn()
        if not self.running and self.choices != self.selected:
            self.error("Resolve the device selection error before starting controllers.")
            return
        self.send("stop" if self.running else "start")

    @Slot()
    def stop(self): self.send("stop")

    @Slot()
    def save(self):
        try:
            atomic_json(self.profile_path, {"version": 1, "profiles": self.profiles, "selected": self.selected})
            self.error(f"Saved: {self.profile_path}")
        except OSError as error: self.error(str(error))

    @Slot()
    def exportReport(self):
        try:
            # No raw keystrokes, USB serials, absolute device paths or user names.
            report = {"version": 1, "demo": self.demo, "running": self.running, "device_count": len(self.devices_data)-1,
                      "players": [{"selected": bool(self.selected[p]), "bindings": self.profiles[p], "state": self.states[p]} for p in range(2)]}
            path = self.config_dir / "diagnostics.json"
            atomic_json(path, report)
            self.error(f"Diagnostic snapshot saved: {path}")
        except OSError as error: self.error(str(error))

    @Slot(int, bool)
    def demoKey(self, key, pressed):
        if self.demo and key in DEMO_KEYS:
            if pressed:
                if not self.selected[self.active]: return
                self.held[key] = self.active
                player = self.active
            else:
                player = self.held.pop(key, None)
                if player is None: return
            self.send("inject", player=player, source="keyboard", kind=1, code=DEMO_KEYS[key], value=int(pressed))

    @Slot()
    def releaseDemoKeys(self):
        for key, player in list(self.held.items()):
            self.send("inject", player=player, source="keyboard", kind=1, code=DEMO_KEYS[key], value=0)
        self.held.clear()

    @Slot(int)
    def setupDevice(self, index):
        if self.demo or self.running or not 0 < index < len(self.devices_data): return
        if self.setup_process is not None: return
        identity = self.devices_data[index]["id"]
        usb_id, port = identity.rsplit("@", 1)
        vendor, product = usb_id.split(":")[:2]
        self.setup_target = (self.active, identity)
        self.setup_process = QProcess(self)
        self.setup_process.finished.connect(self.setupFinished)
        self.setup_process.errorOccurred.connect(self.setupError)
        self.setup_process.start("/usr/bin/pkexec", ["/usr/bin/python3", str(ROOT / "tools" / "setup_linux.py"), vendor, product, port])
        self.error("Authorize access to this USB receiver and virtual gamepad creation.")

    @Slot(QProcess.ProcessError)
    def setupError(self, error):
        self.error("Cannot launch pkexec. Install polkit and enable its authentication agent.")
        if error == QProcess.FailedToStart and self.setup_process is not None:
            self.setup_process.deleteLater()
            self.setup_process = None

    @Slot(int, QProcess.ExitStatus)
    def setupFinished(self, code, _status):
        process = self.setup_process
        output = bytes(process.readAllStandardOutput() if code == 0 else process.readAllStandardError()).decode(errors="replace").strip()
        self.error(output or ("Setup completed. Select the receiver again." if code == 0 else "Setup was cancelled or failed."))
        process.deleteLater(); self.setup_process = None
        self.send("scan")
        if code == 0:
            player, identity = self.setup_target
            self.send("select", player=player, device=identity)

    @Slot()
    def demoDefaults(self):
        if not self.demo or self.running: return
        codes = [30,31,32,33,34,103,108,28,14,103,108,105,106,57,57]
        self.profiles[self.active]["bindings"] = {action: {"source": "keyboard", "kind": 1, "code": code, "rest": 0, "full": 1} for action,code in zip(ACTIONS,codes)}
        self.sync_profile(self.active); self.changed.emit()

    def shutdown(self):
        if self.process.state() != QProcess.NotRunning:
            self.send("quit")
            if not self.process.waitForFinished(2000):
                self.process.kill(); self.process.waitForFinished(1000)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--backend", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--config-dir", type=Path)
    args = parser.parse_args()
    QQuickStyle.setStyle("Fusion")
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("GHVirtualGamePad")
    app.setApplicationName("GHVirtualGamePad")
    app.setDesktopFileName("io.github.BrainAlaw.GHVirtualGamePad")
    app.setWindowIcon(QIcon(str(ROOT / "assets" / "ghvirtualgamepad.svg")))
    binary_name = "ghvirtualgamepad.exe" if sys.platform == "win32" else "ghvirtualgamepad"
    bundled = ROOT / "bin" / binary_name
    executable = args.backend or (bundled if bundled.exists() else ROOT / "target" / "debug" / binary_name)
    demo = args.demo or sys.platform != "linux"
    bridge = Bridge(demo, executable, args.config_dir)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(str(ROOT / "gui" / "Main.qml"))
    if not engine.rootObjects():
        bridge.shutdown(); return 1
    app.aboutToQuit.connect(bridge.shutdown)
    if args.smoke_test: QTimer.singleShot(1500, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
