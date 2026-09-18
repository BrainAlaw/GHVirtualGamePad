"""Install narrowly scoped udev access for one chosen receiver and uinput.

Invoke through pkexec from the GUI. This helper never evaluates shell commands.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

MARKER = "# Managed by GHVirtualGamePad\n"


def install(vendor, product, port):
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("Run this Linux setup helper through pkexec")
    if not re.fullmatch(r"[0-9a-f]{4}", vendor) or not re.fullmatch(r"[0-9a-f]{4}", product) or not re.fullmatch(r"[0-9]+-[0-9]+(?:\.[0-9]+)*", port):
        raise ValueError("Invalid USB identity")
    usb = Path("/sys/bus/usb/devices") / port
    if (usb / "idVendor").read_text().strip() != vendor or (usb / "idProduct").read_text().strip() != product:
        raise ValueError("The receiver has changed or disconnected; rescan devices")
    target = Path(f"/etc/udev/rules.d/70-ghvirtualgamepad-{vendor}-{product}-{port}.rules")
    if target.is_symlink() or (target.exists() and not target.read_text().startswith(MARKER)):
        raise RuntimeError("Refusing to replace an unmanaged rule")
    module_file = Path("/etc/modules-load.d/ghvirtualgamepad.conf")
    if module_file.is_symlink() or (module_file.exists() and module_file.read_text() != "uinput\n"):
        raise RuntimeError("Refusing to replace an unmanaged modules-load configuration")
    rules = MARKER + (
        f'SUBSYSTEM=="input", KERNEL=="event*", ATTRS{{idVendor}}=="{vendor}", ATTRS{{idProduct}}=="{product}", KERNELS=="{port}", TAG+="uaccess"\n'
        'SUBSYSTEM=="misc", KERNEL=="uinput", TAG+="uaccess"\n'
    )
    subprocess.run(["/usr/bin/modprobe", "uinput"], check=True)
    fd, temporary = tempfile.mkstemp(prefix=".ghvp-", dir=target.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(rules)
            stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    module_file.write_text("uinput\n")
    subprocess.run(["/usr/bin/udevadm", "control", "--reload-rules"], check=True)
    subprocess.run(["/usr/bin/udevadm", "trigger", "--action=change", "--subsystem-match=input"], check=True)
    subprocess.run(["/usr/bin/udevadm", "trigger", "--action=change", "/sys/class/misc/uinput"], check=True)
    subprocess.run(["/usr/bin/udevadm", "settle", "--timeout=10"], check=True)
    print("Device access configured. Reconnect the receiver if access is still denied.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("vendor"); parser.add_argument("product"); parser.add_argument("port")
    args = parser.parse_args()
    try: install(args.vendor, args.product, args.port)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr); sys.exit(1)
