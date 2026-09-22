import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import roleweaver_storage as legacy_storage  # noqa: E402
from roleweaver.config import SettingsStore, default_settings  # noqa: E402
from roleweaver.paths import RuntimePaths  # noqa: E402
from roleweaver.storage import atomic  # noqa: E402


class ConfigurationStorageContractTests(unittest.TestCase):
    def test_runtime_paths_support_source_and_frozen_launches(self):
        source_root = Path.cwd() / "source-install"
        frozen_root = Path.cwd() / "frozen-install"
        source = RuntimePaths.from_entrypoint(source_root / "nwn_ai_bot.py", frozen=False)
        frozen = RuntimePaths.from_entrypoint(
            source_root / "ignored.py",
            frozen=True,
            executable=frozen_root / "RoleWeaver.exe",
        )

        self.assertEqual(source.settings, source_root / "settings.json")
        self.assertEqual(frozen.characters, frozen_root / "Characters")
        self.assertEqual(source.campaigns, source.root / "Campaigns")

    def test_settings_merge_preserves_extensions_and_migrates(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "server_profile": "LEGACY",
                        "log_path": "/old/log.txt",
                        "extension_setting": {"enabled": True},
                    }
                ),
                encoding="utf-8",
            )
            defaults = default_settings("/default/log.txt", keyboard_method="x11")
            migrations = []

            def migrate(settings):
                migrations.append(True)
                settings["log_path"] = "/migrated/log.txt"
                return settings

            store = SettingsStore(
                path,
                defaults,
                known_profiles={"AUTO"},
                migrate=migrate,
                resolve_log_path=lambda settings, profile: settings["server_log_paths"].get(
                    profile, settings["log_path"]
                ),
            )
            loaded = store.load()

        self.assertTrue(migrations)
        self.assertEqual(loaded["extension_setting"], {"enabled": True})
        self.assertEqual(loaded["keyboard_method"], "x11")
        self.assertEqual(loaded["discovered_servers"]["LEGACY"]["log_path"], "/migrated/log.txt")

    def test_settings_are_written_atomically(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(atomic, "_frozen", False):
            path = Path(temporary) / "settings.json"
            store = SettingsStore(path, default_settings("game.log", keyboard_method="scancode"))
            store.save({"character_name": "Hero", "extension_value": 7})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["extension_value"], 7)
            self.assertFalse(list(path.parent.glob(".rw-save-*.tmp")))

    def test_legacy_storage_import_is_the_shared_implementation(self):
        self.assertIs(legacy_storage, atomic)


if __name__ == "__main__":
    unittest.main()
