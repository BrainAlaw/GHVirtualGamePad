"""Fetch hash-pinned official driver payloads; never install drivers during a build."""
import hashlib
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "artifacts/windows-dependencies"
PAYLOADS = {
    "Interception.zip": (
        "https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip",
        "ad038963d6413055765128b0b931f6e765147c9916dba79e65d872b261f9af10"),
    "ViGEmBus.exe": (
        "https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe",
        "89220a7865076b342892f98865f3499fb7c4cfd673159e89d352c360fd014c6a"),
}


def fetch_verified(url, digest, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise RuntimeError(f"Download checksum mismatch: {destination.name}")
        destination.write_bytes(payload)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"Cached checksum mismatch: {destination.name}")


def prepare():
    for name, (url, digest) in PAYLOADS.items():
        fetch_verified(url, digest, DESTINATION / name)
    with zipfile.ZipFile(DESTINATION / "Interception.zip") as archive:
        for member, target in [
            ("Interception/library/x64/interception.dll", "interception.dll"),
            ("Interception/command line installer/install-interception.exe", "install-interception.exe"),
        ]:
            (DESTINATION / target).write_bytes(archive.read(member))
        for member in archive.namelist():
            if "/licenses/" in member and not member.endswith("/"):
                target = DESTINATION / "licenses" / Path(member).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
    # Exact tagged source matching the client DLL, including its build scripts.
    source = DESTINATION / "Interception-v1.0.1-source.zip"
    if not source.exists():
        url = "https://api.github.com/repos/oblitum/Interception/zipball/513556e660893ca294b2e287143abb40a9170bb3"
        with urllib.request.urlopen(url, timeout=120) as response, source.open("wb") as output:
            shutil.copyfileobj(response, output)
    notice = DESTINATION / "licenses/ViGEmBus-BSD-3-Clause.txt"
    with urllib.request.urlopen("https://raw.githubusercontent.com/nefarius/ViGEmBus/v1.22.0/LICENSE", timeout=60) as response:
        notice.write_bytes(response.read())
    print(DESTINATION)


if __name__ == "__main__":
    prepare()
