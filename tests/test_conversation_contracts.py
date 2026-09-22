import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from roleweaver.conversation import (  # noqa: E402
    ChatEvent,
    LogFollower,
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

    def test_log_follower_buffers_partial_lines_during_bursts(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "client.log"
            path.write_text("", encoding="utf-8")
            follower = LogFollower(path, poll_interval=0.005)
            stop = threading.Event()
            received = []

            def collect():
                for line in follower.lines(stop):
                    received.append(line)
                    if len(received) == 2:
                        stop.set()

            worker = threading.Thread(target=collect)
            worker.start()
            deadline = time.time() + 2
            while follower.file is None and time.time() < deadline:
                time.sleep(0.005)
            with path.open("a", encoding="utf-8") as stream:
                stream.write("Alice: [Talk] first")
                stream.flush()
                time.sleep(0.03)
                self.assertEqual(received, [])
                stream.write(" message\nBob: [Talk] second message\n")
                stream.flush()
            worker.join(2)
            stop.set()
            worker.join(1)

        self.assertEqual(
            received,
            ["Alice: [Talk] first message", "Bob: [Talk] second message"],
        )


if __name__ == "__main__":
    unittest.main()
