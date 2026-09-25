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

    def test_auto_send_opens_pastes_and_submits(self):
        settings = {"window_title_contains": "Neverwinter Nights", "focus_game_before_typing": True}
        with (
            patch.object(mac_platform, "require_desktop"),
            patch.object(mac_platform, "copy_draft") as copy,
            patch.object(
                mac_platform, "focus_nwn_window", return_value=(True, "Neverwinter Nights")
            ),
            patch.object(
                mac_platform,
                "get_foreground_window_title",
                return_value=("42", "Neverwinter Nights"),
            ),
            patch.object(mac_platform, "_osascript") as script,
            patch.object(mac_platform.time, "sleep"),
        ):
            self.assertTrue(mac_platform.send_chat_to_nwn("Hello", settings))
        copy.assert_called_once_with("Hello")
        self.assertEqual(
            [call.args[0] for call in script.call_args_list],
            [mac_platform._RETURN_SCRIPT, mac_platform._PASTE_SCRIPT, mac_platform._RETURN_SCRIPT],
        )

    def test_draft_pastes_without_submitting(self):
        settings = {
            "window_title_contains": "Neverwinter Nights",
            "focus_game_before_typing": False,
        }
        with (
            patch.object(mac_platform, "require_desktop"),
            patch.object(mac_platform, "copy_draft"),
            patch.object(
                mac_platform,
                "get_foreground_window_title",
                return_value=("42", "Neverwinter Nights"),
            ),
            patch.object(mac_platform, "_osascript") as script,
            patch.object(mac_platform.time, "sleep"),
        ):
            self.assertTrue(mac_platform.send_chat_to_nwn("Hello", settings, leave_unsent=True))
        self.assertEqual(
            [call.args[0] for call in script.call_args_list],
            [mac_platform._RETURN_SCRIPT, mac_platform._PASTE_SCRIPT],
        )

    def test_focus_loss_stops_before_submit(self):
        settings = {
            "window_title_contains": "Neverwinter Nights",
            "focus_game_before_typing": False,
        }
        front = [("42", "Neverwinter Nights")] * 3 + [("99", "TextEdit")]
        with (
            patch.object(mac_platform, "require_desktop"),
            patch.object(mac_platform, "copy_draft"),
            patch.object(mac_platform, "get_foreground_window_title", side_effect=front),
            patch.object(mac_platform, "_osascript") as script,
            patch.object(mac_platform.time, "sleep"),
        ):
            self.assertFalse(mac_platform.send_chat_to_nwn("Hello", settings))
        self.assertEqual(
            [call.args[0] for call in script.call_args_list],
            [mac_platform._RETURN_SCRIPT, mac_platform._PASTE_SCRIPT],
        )

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
