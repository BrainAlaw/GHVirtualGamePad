import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gui"))
from app import atomic_json, validate_config, default_profile


class Profiles(unittest.TestCase):
    def test_roundtrip_and_reject_bad_range(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "profile.json"
            data = {"version": 1, "profiles": [default_profile(), default_profile()], "selected": ["", ""]}
            atomic_json(path, data)
            self.assertEqual(validate_config(json.loads(path.read_text())), data)
            data["profiles"][0]["rise_ms"] = 0
            with self.assertRaises(ValueError): validate_config(data)


class Protocol(unittest.TestCase):
    def setUp(self):
        executable = ROOT / "target" / "debug" / ("ghvirtualgamepad.exe" if sys.platform == "win32" else "ghvirtualgamepad")
        self.process = subprocess.Popen([str(executable), "--demo"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.events = queue.Queue()
        self.reader = threading.Thread(target=self.read, daemon=True)
        self.reader.start()
        self.wait(lambda e: e["type"] == "hello")

    def read(self):
        for line in self.process.stdout: self.events.put(json.loads(line))

    def send(self, **command):
        self.process.stdin.write(json.dumps(command) + "\n"); self.process.stdin.flush()

    def wait(self, predicate, timeout=3):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try: event = self.events.get(timeout=max(0.001, end-time.monotonic()))
            except queue.Empty: break
            if predicate(event): return event
        self.fail("Timed out waiting for protocol response")

    def tearDown(self):
        if self.process.poll() is None:
            self.send(op="quit")
            self.process.wait(timeout=3)
        self.reader.join(timeout=1)
        self.process.stdin.close(); self.process.stdout.close(); self.process.stderr.close()

    def test_two_devices_whammy_and_stop(self):
        for p in range(2):
            self.send(op="select", player=p, device=f"demo-{p+1}")
            profile = default_profile()
            profile["bindings"] = {a: {"source": "keyboard", "kind": 1, "code": code, "rest": 0, "full": 1} for a,code in [("green",30),("whammy",57)]}
            self.send(op="profile", player=p, profile=profile)
        self.send(op="start")
        self.wait(lambda e: e["type"] == "status" and e["running"])
        self.send(op="inject", player=0, source="keyboard", kind=1, code=30, value=1)
        self.send(op="inject", player=1, source="keyboard", kind=1, code=57, value=1)
        event = self.wait(lambda e: e["type"] == "state" and e["players"][0]["buttons"].get("green") and e["players"][1]["whammy"] > 0.1)
        self.assertFalse(event["players"][1]["buttons"].get("green", False))
        self.assertEqual(event["players"][0]["whammy"], 0)
        self.send(op="inject", player=1, source="keyboard", kind=1, code=57, value=0)
        self.wait(lambda e: e["type"] == "state" and e["players"][1]["whammy"] == 0)
        self.send(op="stop")
        self.wait(lambda e: e["type"] == "status" and not e["running"])
        event = self.wait(lambda e: e["type"] == "state")
        self.assertEqual(event["players"][0]["buttons"], {})

    def test_duplicate_and_bad_profile_rejected(self):
        self.send(op="select", player=0, device="demo-1")
        self.send(op="select", player=1, device="demo-1")
        self.wait(lambda e: e["type"] == "error" and "other player" in e["message"])
        profile = default_profile(); profile["return_ms"] = 0
        self.send(op="profile", player=0, profile=profile)
        self.wait(lambda e: e["type"] == "error" and "Whammy" in e["message"])

    def test_eof_exits_backend(self):
        self.process.stdin.close()
        self.assertEqual(self.process.wait(timeout=3), 0)


if __name__ == "__main__": unittest.main()
