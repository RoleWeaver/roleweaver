"""Exercise the Updates tab with a disposable, simulated future release."""

import hashlib
import io
import json
import sys
import tarfile
import tempfile
import tkinter as tk
import unittest
import zipfile
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from roleweaver import __version__, update_ui, updates  # noqa: E402


def _future_version():
    major, minor, _ = (int(part) for part in __version__.split("."))
    return f"{major}.{minor + 1}.0"


def _archive(platform, version):
    stream = io.BytesIO()
    if platform == "win32":
        with zipfile.ZipFile(stream, "w") as zipped:
            zipped.writestr("VERSION", version + "\n")
            zipped.writestr("RoleWeaver.exe", b"disposable fixture")
            zipped.writestr("Characters/example.txt", "New example")
    else:
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            prefix = f"RoleWeaver-v{version}-Linux/"
            for name, data in (
                ("VERSION", (version + "\n").encode()),
                ("start-role-weaver.sh", b"#!/bin/sh\n"),
                ("install-linux.sh", b"#!/bin/sh\n"),
                ("Characters/example.txt", b"New example"),
            ):
                entry = tarfile.TarInfo(prefix + name)
                entry.size = len(data)
                entry.mode = 0o755 if name.endswith(".sh") else 0o644
                archive.addfile(entry, io.BytesIO(data))
    return stream.getvalue()


class UpdateRehearsalTests(unittest.TestCase):
    def _exercise(self, platform, *, corrupt=False, installed=False, allow_install=False):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"A desktop display is required: {exc}")
        root.withdraw()
        self.addCleanup(root.destroy)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            current = base / "current"
            current.mkdir()
            (current / "settings.json").write_text('{"language": "French"}')
            (current / "Characters").mkdir()
            (current / "Characters" / "hero.txt").write_text("Original hero")
            destination = base / "new-copies"
            destination.mkdir()
            version = _future_version()
            filename = updates.asset_name(
                version, platform, portable=(platform == "win32" and not installed)
            )
            checksum_name = "SHA256SUMS.txt" if platform == "win32" else "SHA256SUMS-Linux.txt"
            file_url = f"https://github.com/RoleWeaver/roleweaver/releases/download/v{version}/{filename}"
            checksum_url = f"https://github.com/RoleWeaver/roleweaver/releases/download/v{version}/{checksum_name}"
            content = b"disposable installer fixture" if installed else _archive(platform, version)
            expected_hash = hashlib.sha256(b"different" if corrupt else content).hexdigest()
            metadata = {
                "tag_name": f"v{version}",
                "html_url": f"https://github.com/RoleWeaver/roleweaver/releases/tag/v{version}",
                "draft": False,
                "prerelease": False,
                "body": "Disposable rehearsal release",
                "assets": [
                    {"name": filename, "browser_download_url": file_url},
                    {"name": checksum_name, "browser_download_url": checksum_url},
                ],
            }

            def fake_request(url, *, limit):
                if url == updates.RELEASE_API:
                    return json.dumps(metadata).encode()
                if url == checksum_url:
                    return f"{expected_hash}  {filename}\n".encode()
                raise AssertionError(f"Unexpected update URL: {url}")

            panel = update_ui.UpdatePanel(
                ttk.Frame(root), root, platform=platform, installed=installed,
                data_root=current, prepare_install=lambda: allow_install,
                prepare_data=lambda: True,
            )

            def immediate_work(kind, action):
                panel.busy = True
                try:
                    panel.events.put((kind, action(), None))
                except Exception as exc:
                    panel.events.put((kind, None, exc))

            panel._work = immediate_work
            with (
                patch.object(updates, "_request", side_effect=fake_request),
                patch.object(
                    updates.urllib.request, "urlopen",
                    side_effect=lambda *_args, **_kw: io.BytesIO(content),
                ),
                patch.object(Path, "home", return_value=base),
                patch.object(update_ui.messagebox, "askyesno", return_value=True),
                patch.object(update_ui.messagebox, "showinfo"),
                patch.object(update_ui.filedialog, "askdirectory", return_value=str(destination)),
                patch.object(sys, "frozen", True, create=True),
                patch.object(update_ui.subprocess, "Popen") as launch,
            ):
                panel.check()
                panel._poll()
                self.assertIn("available", panel.status.cget("text"))
                panel.download()
                panel._poll()
                if corrupt:
                    self.assertIn("checksum", panel.status.cget("text"))
                    self.assertIsNone(panel.staged_archive)
                    self.assertEqual(list((base / "Downloads").rglob("*.part")), [])
                    return
                self.assertEqual(panel.staged_archive.read_bytes(), content)
                if installed:
                    self.assertEqual(launch.called, allow_install)
                    if allow_install:
                        launch.assert_called_once_with(
                            [str(panel.staged_archive), "/CLOSEAPPLICATIONS"]
                        )
                    return
                panel.prepare()
                panel._poll()

            folder = (
                f"RoleWeaver-Portable-v{version}"
                if platform == "win32"
                else f"RoleWeaver-v{version}-Linux"
            )
            new = destination / folder
            self.assertTrue(new.is_dir())
            self.assertEqual((new / "settings.json").read_text(), '{"language": "French"}')
            self.assertEqual((new / "Characters" / "hero.txt").read_text(), "Original hero")
            self.assertEqual((current / "Characters" / "hero.txt").read_text(), "Original hero")

    def test_portable_windows_full_rehearsal(self):
        self._exercise("win32")

    def test_linux_full_rehearsal(self):
        self._exercise("linux")

    def test_corrupt_download_is_not_prepared(self):
        self._exercise("linux", corrupt=True)

    def test_installed_windows_download_does_not_launch_without_close_approval(self):
        self._exercise("win32", installed=True)

    def test_installed_windows_launches_verified_installer_after_close_approval(self):
        self._exercise("win32", installed=True, allow_install=True)
