import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import roleweaver_games as games
import test_pending_edits as fixtures


class GameTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PendingTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.core = self.fixture.core

    def parse(self, line, game="nwn2"):
        return self.core.parse_chat_line(line, "Eldrin Dustwalker", "AUTO", "channel_first", game)

    def test_mixed_nwn2_chat_and_direction(self):
        lines = [
            ("Eldrin Dustwalker: [Talk] Hello.", "Eldrin Dustwalker", "Talk", True),
            ("[Party] Viconia: Hello.", "Viconia", "Party", False),
            ("[Whisper] To Viconia: Stay quiet.", "Eldrin Dustwalker", "Whisper", True),
            ("[Whisper] From Viconia: Certainly.", "Viconia", "Whisper", False),
            ("[DM] DM_Faith: [Broadcast] Event begins.", "DM_Faith", "Dm", False),
            ("[2026-09-14 12:34:56] [Tell] From Viconia: Hello.", "Viconia", "Tell", False),
            ("Viconia [Shout]: Hello.", "Viconia", "Shout", False),
        ]
        for game in ("nwn2", "nwn2_ee", "nwn2_ce"):
            for line, speaker, channel, own in lines:
                with self.subTest(game=game, line=line):
                    event = self.parse(line, game)
                    self.assertEqual((event["speaker"], event["channel"], event["self"]),
                                     (speaker, channel, own))
        self.assertEqual(self.parse("[Tell] To Viconia: Hello.")["recipient"], "Viconia")

    def test_ignore_system_combat_commands(self):
        for line in (
            "[Server] Welcome to Example.", "[SCRIPT] [DEBUG] Running encounter script.",
            "Eldrin Dustwalker: fires a server-side command: '/dice 1d20'",
            "Eldrin Dustwalker attacks Mercenary : *hit* : (17 + 14 = 31)",
            "Mercenary : Will vs. DC: 18 : *success*", "Connecting to server: Example",
        ):
            self.assertIsNone(self.parse(line), line)

    def test_windows_defaults_and_profile_round_trip(self):
        opts = dict(home=Path("C:/Users/Test"), environ={}, platform="win32")
        self.assertIn("Documents", games.default_game_log("nwn_ee", **opts))
        self.assertIn("Program Files (x86)", games.default_game_log("nwn_diamond", **opts))
        self.assertIn("AppData", games.default_game_log("nwn2", **opts))
        initial = dict(self.fixture.settings, log_path="/custom/original.txt",
                       server_log_paths={"AUTO": "/custom/original.txt"})
        original = copy.deepcopy(initial)
        switched = games.switch_game(initial, "nwn2")
        self.assertEqual(switched["window_title_contains"], "Neverwinter Nights 2")
        self.assertEqual(switched["discovered_servers"], {})
        restored = games.switch_game(switched, "nwn_ee")
        self.assertEqual(restored["log_path"], original["log_path"])
        self.assertEqual(initial, original)

    def test_linux_prefix_and_extender_nested_chat(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            prefix = home / "prefix"
            logs = prefix / "drive_c/users/steamuser/Documents/Neverwinter Nights 2/Logs"
            chat = logs / "Hero/chat/2026.txt"
            combat = logs / "Hero/combat/2026.txt"
            for path in (chat, combat):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("[Talk] Hero: Hello.")
            roots = games.game_directories("nwn2_ce", home=home,
                    environ={"WINEPREFIX": str(prefix)}, platform="linux")
            self.assertIn(logs, roots)
            with patch.object(games, "game_directories", return_value=roots):
                found = games.discover_game_logs({"game_version": "nwn2_ce"})
            self.assertIn(chat, found)
            self.assertNotIn(combat, found)

    def test_nwn_original_retains_existing_parser(self):
        for game in ("nwn", "nwn_diamond", "nwn_ee"):
            event = self.parse("[Talk] Eldrin Dustwalker: Hello.", game)
            self.assertTrue(event["self"])

    def test_ee_temp_directory_and_64bit_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            opts = dict(home=home, environ={}, platform="win32")
            roots = games.game_directories("nwn2_ee", **opts)
            ee = home / "AppData/Local/Temp/NWN2 EE"
            self.assertEqual(roots[0], ee)
            ee.mkdir(parents=True)
            log = ee / "nwn2client64Log1.txt"
            log.write_text("[Talk] Hero: Hi.")
            with patch.object(games, "game_directories", return_value=roots):
                self.assertEqual(games.discover_game_logs({"game_version": "nwn2_ee"}), [log])
            linux_roots = games.game_directories("nwn2_ee", home=home, environ={}, platform="linux")
            self.assertTrue(any(p.as_posix().endswith("AppData/Local/Temp/NWN2 EE") for p in linux_roots))

    def test_settings_persist_selected_game(self):
        settings = games.switch_game(self.fixture.settings, "nwn2")
        self.core.save_settings(settings)
        with patch.object(self.core, "discover_nwn_log_files", return_value=[]):
            loaded = self.core.load_settings()
        self.assertEqual(loaded["game_version"], "nwn2")
        self.assertEqual(loaded["window_title_contains"], "Neverwinter Nights 2")


if __name__ == "__main__":
    unittest.main()
