"""Opt-in native Windows check. Does not select, capture or inject keyboard input.

Close games first: the virtual-pad probe briefly moves an axis on two temporary pads.
"""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import threading
import time


def check(executable):
    subprocess.run([str(executable), "--probe-gamepads"], check=True, timeout=30)
    process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    events = queue.Queue()
    def read():
        for line in process.stdout:
            events.put(json.loads(line))
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            event = events.get(timeout=max(0.01, deadline - time.monotonic()))
            if event["type"] == "error":
                raise RuntimeError(event["message"])
            if event["type"] == "devices":
                if not event["devices"]:
                    raise RuntimeError("No keyboard slots found; check Interception and reboot")
                print(f'Native keyboard enumeration: {len(event["devices"])} slots. No input was captured.')
                return
        raise RuntimeError("Timed out enumerating keyboards")
    finally:
        if process.poll() is None:
            process.stdin.write('{"op":"quit"}\n')
            process.stdin.flush()
            process.wait(timeout=15)
        reader.join(timeout=1)
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", type=Path)
    check(parser.parse_args().backend.resolve())
