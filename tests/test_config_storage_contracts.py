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
from roleweaver.config import (  # noqa: E402
    SettingsStore,
    default_settings,
    restore_guardrail_defaults,
)
from roleweaver.config.models import LEGACY_GUARDRAIL_ACTIONS  # noqa: E402
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

    def test_legacy_guardrail_defaults_migrate_to_pg_profile_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "guardrail_default_policies": LEGACY_GUARDRAIL_ACTIONS,
                        "guardrail_replacement_text": (
                            "Let us keep to matters of this world. What do you need?"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            store = SettingsStore(
                path,
                default_settings("game.log", keyboard_method="scancode"),
            )

            loaded = store.load()

        self.assertEqual(loaded["guardrail_policy_version"], 2)
        self.assertEqual(loaded["guardrail_default_policies"]["toxicity"], "replace")
        self.assertEqual(loaded["guardrail_purpose_policies"]["summary"]["toxicity"], "warn")
        self.assertEqual(
            loaded["guardrail_replacement_text"],
            "*They steer the conversation toward less troubling matters.*",
        )

    def test_guardrail_migration_preserves_custom_policy_choices(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "guardrail_default_policies": {"toxicity": "block"},
                        "guardrail_replacement_text": "My custom safe reply.",
                    }
                ),
                encoding="utf-8",
            )
            store = SettingsStore(
                path,
                default_settings("game.log", keyboard_method="scancode"),
            )

            loaded = store.load()

        self.assertEqual(loaded["guardrail_default_policies"]["toxicity"], "block")
        self.assertEqual(loaded["guardrail_replacement_text"], "My custom safe reply.")

    def test_restore_guardrail_defaults_preserves_pricing_and_usage_settings(self):
        settings = {
            "guardrail_default_policies": {"toxicity": "off"},
            "guardrail_purpose_policies": {"reply": {"toxicity": "block"}},
            "guardrail_custom_terms": "custom term",
            "guardrail_custom_regex": "custom.*expression",
            "guardrail_replacement_text": "Custom replacement",
            "guardrail_retry_output_once": False,
            "guardrail_input_max_characters": 100,
            "guardrail_output_max_characters": 200,
            "usage_input_cost_per_million": 1.25,
            "usage_output_cost_per_million": 4.5,
            "unrelated_extension": "preserved",
        }

        restored = restore_guardrail_defaults(settings)

        self.assertIs(restored, settings)
        self.assertEqual(restored["guardrail_default_policies"]["toxicity"], "replace")
        self.assertEqual(restored["guardrail_purpose_policies"]["summary"]["toxicity"], "warn")
        self.assertEqual(restored["guardrail_custom_terms"], "")
        self.assertEqual(restored["guardrail_custom_regex"], "")
        self.assertTrue(restored["guardrail_retry_output_once"])
        self.assertEqual(restored["guardrail_input_max_characters"], 50000)
        self.assertEqual(restored["guardrail_output_max_characters"], 10000)
        self.assertEqual(restored["usage_input_cost_per_million"], 1.25)
        self.assertEqual(restored["usage_output_cost_per_million"], 4.5)
        self.assertEqual(restored["unrelated_extension"], "preserved")


if __name__ == "__main__":
    unittest.main()
