"""Contract tests for the platform-neutral bilingual draft workflow."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from roleweaver.drafting import DraftWorkflowMixin


class DraftHost(DraftWorkflowMixin):
    def __init__(self):
        self.settings = {
            "user_language": "English",
            "game_language": "German",
        }
        self.translation_service = Mock()
        self.translation_service.translate.side_effect = lambda request: SimpleNamespace(
            message=lambda _identifier: SimpleNamespace(
                translated_text="Guten Tag" if request.target_language == "German" else "Good day"
            )
        )
        self.generate_reply = Mock(return_value="Good day")
        self.last_draft = ""
        self.last_draft_version = 0
        self.translated_draft = ""
        self.translated_draft_source = ""
        self.translated_draft_language = ""
        self.translated_draft_version = 0
        self.translation_status = "Ready"

    def _protected_translation_terms(self):
        return ("Waterdeep",)


class DraftWorkflowTests(unittest.TestCase):
    def test_forward_and_back_translation_preserve_editor_ownership(self):
        host = DraftHost()
        self.assertEqual(host.translate_draft(" Good day "), "Guten Tag")
        request = host.translation_service.translate.call_args.args[0]
        self.assertEqual((request.source_language, request.target_language), ("English", "German"))
        self.assertEqual(request.protected_terms, ("Waterdeep",))
        self.assertEqual(host.translated_draft_source, "Good day")
        self.assertEqual(host.translated_draft_version, 1)

        self.assertEqual(host.translate_game_draft("Guten Tag"), "Good day")
        request = host.translation_service.translate.call_args.args[0]
        self.assertEqual((request.source_language, request.target_language), ("German", "English"))
        self.assertEqual(host.translated_draft, "Guten Tag")
        self.assertEqual(host.translated_draft_source, "Good day")
        self.assertEqual(host.last_draft, "Good day")
        self.assertEqual(host.last_draft_version, 1)

    def test_revision_uses_selected_editor_language_and_seed(self):
        host = DraftHost()
        host.generate_reply.return_value = "Neuer Satz"
        self.assertEqual(host.revise_editor_draft({
            "language": "game", "seed": "Mein Satz", "user_source": "My sentence",
        }), "Neuer Satz")
        request = host.generate_reply.call_args.kwargs
        self.assertEqual(request["language"], "German")
        self.assertIn("Mein Satz", request["draft_instruction"])
        self.assertEqual(host.translated_draft_source, "My sentence")
        self.assertEqual(host.translated_draft_version, 1)
        self.assertEqual(host.last_draft_version, 0)

        host.generate_reply.return_value = "My shorter sentence"
        host.revise_editor_draft({"language": "user", "seed": "My sentence", "mode": "shorter"})
        request = host.generate_reply.call_args.kwargs
        self.assertEqual(request["language"], "English")
        self.assertIn("noticeably shorter", request["draft_instruction"])
        self.assertEqual(host.last_draft, "My shorter sentence")

    def test_empty_game_draft_and_failed_translation_do_not_replace_text(self):
        host = DraftHost()
        host.translated_draft = "Previous game text"
        self.assertIsNone(host.revise_editor_draft({"language": "game", "seed": ""}))
        host.generate_reply.assert_not_called()
        host.translation_service.translate.side_effect = RuntimeError("offline")
        self.assertEqual(host.translate_draft("New user text"), "")
        self.assertEqual(host.translated_draft, "Previous game text")
        self.assertEqual(host.translated_draft_version, 0)

    def test_f9_sequence_generates_and_translates_once(self):
        host = DraftHost()
        self.assertEqual(host.generate_translation_draft(), "Good day")
        host.generate_reply.assert_called_once_with()
        host.translation_service.translate.assert_called_once()
        self.assertEqual(host.last_draft, "Good day")
        self.assertEqual(host.translated_draft, "Guten Tag")
