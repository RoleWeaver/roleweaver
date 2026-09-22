"""Fresh-folder updates preserve personal data and reject unsafe archives."""

import io
import os
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from roleweaver.update_install import prepare_fresh_install  # noqa: E402
from roleweaver.updates import UpdateError  # noqa: E402


def _tar_file(archive, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o755 if name.endswith(".sh") else 0o644
    archive.addfile(info, io.BytesIO(data))


class FreshInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.current = self.root / "current"
        self.current.mkdir()
        (self.current / "settings.json").write_text('{"theme": "custom"}')
        (self.current / "Characters").mkdir()
        (self.current / "Characters" / "hero.txt").write_text("My character")
        self.parent = self.root / "new-copies"
        self.parent.mkdir()

    def test_linux_update_migrates_data_without_touching_old_copy(self):
        archive = self.root / "release.tar.gz"
        prefix = "RoleWeaver-v1.2.4-Linux/"
        with tarfile.open(archive, "w:gz") as tar:
            _tar_file(tar, prefix + "VERSION", b"1.2.4\n")
            _tar_file(tar, prefix + "start-role-weaver.sh", b"#!/bin/sh\n")
            _tar_file(tar, prefix + "install-linux.sh", b"#!/bin/sh\n")
            _tar_file(tar, prefix + "Characters/new-example.txt", b"new example")

        new = prepare_fresh_install(archive, self.current, self.parent, "1.2.4", "linux")

        self.assertEqual((new / "settings.json").read_text(), '{"theme": "custom"}')
        self.assertEqual((new / "Characters" / "hero.txt").read_text(), "My character")
        self.assertEqual((new / "Characters" / "new-example.txt").read_bytes(), b"new example")
        self.assertEqual((self.current / "Characters" / "hero.txt").read_text(), "My character")
        if os.name != "nt":
            self.assertTrue((new / "start-role-weaver.sh").stat().st_mode & 0o100)
        with self.assertRaises(UpdateError):
            prepare_fresh_install(archive, self.current, self.parent, "1.2.4", "linux")

    def test_windows_portable_update_migrates_data(self):
        archive = self.root / "portable.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("VERSION", "1.2.4\n")
            zipped.writestr("RoleWeaver.exe", b"exe")
            zipped.writestr("Characters/new-example.txt", "new example")

        new = prepare_fresh_install(archive, self.current, self.parent, "1.2.4", "win32")

        self.assertEqual((new / "settings.json").read_text(), '{"theme": "custom"}')
        self.assertEqual((new / "Characters" / "hero.txt").read_text(), "My character")
        self.assertTrue((new / "RoleWeaver.exe").is_file())

    def test_unsafe_archive_does_not_publish_folder_or_escape_parent(self):
        archive = self.root / "unsafe.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("../escape.txt", "danger")
            zipped.writestr("VERSION", "1.2.4\n")
            zipped.writestr("RoleWeaver.exe", b"exe")

        with self.assertRaises(UpdateError):
            prepare_fresh_install(archive, self.current, self.parent, "1.2.4", "win32")

        self.assertFalse((self.parent / "RoleWeaver-Portable-v1.2.4").exists())
        self.assertFalse((self.root / "escape.txt").exists())

    def test_mismatched_version_does_not_publish_folder(self):
        archive = self.root / "wrong-version.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("VERSION", "1.2.3\n")
            zipped.writestr("RoleWeaver.exe", b"exe")

        with self.assertRaises(UpdateError):
            prepare_fresh_install(archive, self.current, self.parent, "1.2.4", "win32")

        self.assertFalse((self.parent / "RoleWeaver-Portable-v1.2.4").exists())
