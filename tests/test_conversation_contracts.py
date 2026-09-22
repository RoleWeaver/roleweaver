import sys
import unittest
from pathlib import Path
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from roleweaver.conversation import (  # noqa: E402
    ChatEvent,
    clean_nwn_text,
    detect_log_format,
    parse_chat_line,
)


class ConversationContractTests(unittest.TestCase):
    def test_structured_chat_uses_normalized_contract(self):
        event = parse_chat_line(
            '[speaker-1] <cÿÿÿ>Alice</c>: [Talk] <cÿÿÿ>"Hello."</c>',
            "Bob",
            "WORLD_Test",
        )

        self.assertEqual(
            event,
            {
                "speaker_id": "speaker-1",
                "speaker": "Alice",
                "channel": "Talk",
                "message": '"Hello."',
                "self": False,
                "server_profile": "WORLD_Test",
            },
        )

    def test_chat_event_documents_extension_fields(self):
        fields = get_type_hints(ChatEvent)

        self.assertIn("recipient", fields)
        self.assertIn("speaker_id", fields)
        self.assertFalse(ChatEvent.__total__)

    def test_format_detection_prefers_structured_copy(self):
        text = "\n".join(
            (
                "[CHAT WINDOW TEXT] Alice: Hello.",
                "[speaker-1] Alice: [Talk] Hello.",
            )
        )

        self.assertEqual(detect_log_format(text), "structured")

    def test_clean_text_is_safe_for_none_and_control_characters(self):
        self.assertEqual(clean_nwn_text(None), "")
        self.assertEqual(clean_nwn_text("<cabc>Hello</c>\x00"), "Hello")


if __name__ == "__main__":
    unittest.main()
