import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mac_platform

from roleweaver.games import game_directories
from roleweaver.paths import RuntimePaths
from roleweaver.updates import asset_name


class MacPlatformTests(unittest.TestCase):
    def test_mac_log_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = game_directories("nwn_ee", home=root, platform="darwin", environ={})
            self.assertEqual(paths[0], root / "Documents/Neverwinter Nights/logs")
            self.assertEqual(paths[1], root / "Library/Application Support/Neverwinter Nights/logs")

    def test_clipboard_copy_is_not_a_send(self):
        with patch.object(mac_platform, "copy_draft") as copy:
            self.assertFalse(mac_platform.send_chat_to_nwn("Hello", {"max_reply_characters": 430}))
            copy.assert_called_once_with("Hello")

    def test_user_data_outside_app_bundle(self):
        with patch.object(sys, "platform", "darwin"):
            paths = RuntimePaths.from_entrypoint(
                "/Applications/RoleWeaver.app/Contents/MacOS/RoleWeaver", frozen=True
            )
        self.assertEqual(paths.root, Path.home() / "Library/Application Support/RoleWeaver")

    def test_architecture_specific_download(self):
        with patch("roleweaver.updates.system_platform.machine", return_value="arm64"):
            self.assertEqual(asset_name("1.3.1", "darwin"), "RoleWeaver-v1.3.1-macOS-arm64.zip")


if __name__ == "__main__":
    unittest.main()
