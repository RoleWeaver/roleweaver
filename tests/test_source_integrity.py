"""Protect both desktop clients from source-encoding and mirrored-logic drift."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_source_integrity import check_source_integrity  # noqa: E402


class SourceIntegrityTests(unittest.TestCase):
    def test_executable_source_is_utf8_and_mirrored_logic_matches(self):
        self.assertEqual(check_source_integrity(ROOT), [])

    def test_guard_detects_damaged_encoding_and_logic_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "linux").mkdir()
            (root / "nwn_ai_bot.py").write_text(
                "def shared():\n    return 1\n", encoding="utf-8"
            )
            (root / "linux" / "nwn_ai_bot.py").write_text(
                "def shared():\n    return 2\n", encoding="utf-8"
            )
            (root / "linux" / "extra.py").write_text(
                "value = 'Ã¿'\n", encoding="utf-8"
            )

            findings = check_source_integrity(root)

        self.assertTrue(any("Mirrored function differs: shared" in item for item in findings))
        self.assertTrue(any("possible mojibake" in item for item in findings))
