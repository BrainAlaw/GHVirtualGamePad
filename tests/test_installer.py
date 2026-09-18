from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from install_linux import install, desktop_quote, APP_ID


class Installer(unittest.TestCase):
    def payload(self, root):
        for name in ["assets/ghvirtualgamepad.svg", "LICENSE", "app/GHVirtualGamePad"]:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.touch()

    def test_dry_run_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.payload(root / "source")
            result = install(root / "source", root / "data", dry_run=True)
            self.assertTrue(result["frozen"])
            self.assertFalse((root / "data").exists())

    def test_unmanaged_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.payload(root / "source")
            target = root / "data/ghvirtualgamepad"; target.mkdir(parents=True)
            (target / "keep.txt").write_text("user data")
            with self.assertRaises(RuntimeError): install(root / "source", root / "data", dry_run=True)
            self.assertEqual((target / "keep.txt").read_text(), "user data")

    def test_unmanaged_shortcut_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.payload(root / "source")
            shortcut = root / "data/applications" / f"{APP_ID}.desktop"
            shortcut.parent.mkdir(parents=True); shortcut.write_text("existing shortcut")
            with self.assertRaises(RuntimeError): install(root / "source", root / "data", dry_run=True)
            self.assertEqual(shortcut.read_text(), "existing shortcut")

    def test_exec_quoting(self):
        self.assertEqual(desktop_quote("/path with spaces/app"), '"/path with spaces/app"')
        self.assertIn("%%", desktop_quote("/path%/app"))
        with self.assertRaises(ValueError): desktop_quote("/path\nExec=unrelated")


if __name__ == "__main__": unittest.main()
