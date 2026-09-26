"""Release discovery and checksum-verified update staging."""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from roleweaver import __version__, updates  # noqa: E402


class UpdateTests(unittest.TestCase):
    def test_release_version_files_match_package(self):
        self.assertEqual((ROOT / "VERSION").read_text().strip(), __version__)
        self.assertEqual((ROOT / "linux" / "VERSION").read_text().strip(), __version__)

    def test_versions_and_asset_names(self):
        self.assertTrue(updates.is_newer("1.2.4", "1.2.3"))
        self.assertTrue(updates.is_newer("1.3.1", "1.3.0"))
        self.assertTrue(updates.is_newer("1.3.2", "1.3.1"))
        self.assertFalse(updates.is_newer("1.2.3", "1.2.3"))
        self.assertEqual(updates.asset_name("1.2.4", "win32"), "RoleWeaver-Setup-v1.2.4.exe")
        self.assertEqual(
            updates.asset_name("1.2.4", "win32", portable=True),
            "RoleWeaver-Portable-v1.2.4.zip",
        )
        self.assertEqual(updates.asset_name("1.2.4", "linux"), "RoleWeaver-v1.2.4-Linux.tar.gz")
        with self.assertRaises(updates.UpdateError):
            updates.is_newer("1.2.4-alpha", "1.2.3")

    def test_v130_clients_can_find_v131_platform_downloads(self):
        version = "1.3.1"
        assets = {
            name: f"https://github.com/RoleWeaver/roleweaver/releases/download/v{version}/{name}"
            for name in (
                updates.asset_name(version, "win32"),
                updates.asset_name(version, "win32", portable=True),
                updates.asset_name(version, "linux"),
                "SHA256SUMS.txt",
                "SHA256SUMS-Linux.txt",
            )
        }
        release = updates.Release(
            version,
            f"https://github.com/RoleWeaver/roleweaver/releases/tag/v{version}",
            "",
            assets,
        )
        self.assertTrue(updates.is_newer(release.version, "1.3.0"))
        self.assertTrue(updates.can_download(release, "win32"))
        self.assertTrue(updates.can_download(release, "win32", portable=True))
        self.assertTrue(updates.can_download(release, "linux"))

    def test_release_check_accepts_stable_github_assets_only(self):
        payload = {
            "tag_name": "v1.2.4",
            "html_url": "https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.4",
            "draft": False,
            "prerelease": False,
            "body": "Release notes",
            "assets": [
                {
                    "name": "SHA256SUMS.txt",
                    "browser_download_url": "https://github.com/RoleWeaver/roleweaver/releases/download/v1.2.4/SHA256SUMS.txt",
                }
            ],
        }
        with patch.object(updates, "_request", return_value=json.dumps(payload).encode()):
            release = updates.check_latest()
            self.assertEqual(release.version, "1.2.4")
            self.assertFalse(updates.can_download(release, "win32"))
        payload["assets"][0]["browser_download_url"] = "http://example.com/file"
        with patch.object(updates, "_request", return_value=json.dumps(payload).encode()):
            with self.assertRaises(updates.UpdateError):
                updates.check_latest()

    def test_stage_rejects_corrupt_download_without_replacing_existing_file(self):
        filename = updates.asset_name("1.2.4", "linux")
        release = updates.Release(
            "1.2.4",
            "https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.4",
            "",
            {
                filename: "https://github.com/RoleWeaver/roleweaver/releases/download/v1.2.4/archive",
                "SHA256SUMS-Linux.txt": "https://github.com/RoleWeaver/roleweaver/releases/download/v1.2.4/checksums",
            },
        )
        expected = hashlib.sha256(b"correct").hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            target = destination / filename
            target.write_bytes(b"old file")
            with (
                patch.object(
                    updates, "_request", return_value=f"{expected}  {filename}\n".encode()
                ),
                patch.object(
                    updates.urllib.request, "urlopen", return_value=io.BytesIO(b"incorrect")
                ),
            ):
                with self.assertRaises(updates.UpdateError):
                    updates.stage_release(release, "linux", destination)
            self.assertEqual(target.read_bytes(), b"old file")
            self.assertEqual(list(destination.glob("*.part")), [])

    def test_stage_accepts_matching_checksum(self):
        filename = updates.asset_name("1.2.4", "win32")
        data = b"installer"
        release = updates.Release(
            "1.2.4",
            "https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.4",
            "",
            {
                filename: "https://github.com/RoleWeaver/roleweaver/releases/download/v1.2.4/setup",
                "SHA256SUMS.txt": "https://github.com/RoleWeaver/roleweaver/releases/download/v1.2.4/checksums",
            },
        )
        checksum = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch.object(
                    updates, "_request", return_value=f"{checksum}  {filename}\n".encode()
                ),
                patch.object(updates.urllib.request, "urlopen", return_value=io.BytesIO(data)),
            ):
                path = updates.stage_release(release, "win32", Path(temporary))
            self.assertEqual(path.read_bytes(), data)
