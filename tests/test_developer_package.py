"""The source release must be complete without bundling personal data."""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_developer_package import REQUIRED, check_developer_package  # noqa: E402


class DeveloperPackageTests(unittest.TestCase):
    def test_complete_archive_passes_and_private_data_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "RoleWeaver-Developer-v1.2.4.zip"
            prefix = archive.stem + "/"
            with zipfile.ZipFile(archive, "w") as source:
                for name in REQUIRED:
                    source.writestr(prefix + name, "sample")
            self.assertEqual(check_developer_package(archive), [])
            with zipfile.ZipFile(archive, "a") as source:
                source.writestr(prefix + "settings.json", "{}")
            self.assertTrue(
                any("private data" in finding for finding in check_developer_package(archive))
            )

    def test_missing_required_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "RoleWeaver-Developer-v1.2.4.zip"
            with zipfile.ZipFile(archive, "w") as source:
                source.writestr(archive.stem + "/README.md", "sample")
            findings = check_developer_package(archive)
            self.assertTrue(
                any("Missing developer package file" in finding for finding in findings)
            )
