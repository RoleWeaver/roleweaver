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

    def test_log_follower_preserves_spanish_cp1252_chat(self):
        source = (
            "Oh, ¿un marinero adinerado con mi propio barco? "
            "Un hombre puede soñar. Debería irme. ¡Fue un placer conocerte!"
        )

        self.assertEqual(LogFollower._decode_line(source.encode("cp1252")), source)
        self.assertEqual(LogFollower._decode_line(source.encode("utf-8")), source)

    def test_log_follower_decodes_configured_european_languages(self):
        examples = (
            ("German", "Grüße aus der Stadt!", "cp1252"),
            ("French", "À bientôt, mon ami !", "cp1252"),
            ("Italian", "Perché sei qui?", "cp1252"),
            ("Dutch", "Fijne avond, één drankje?", "cp1252"),
            ("Polish", "Zażółć gęślą jaźń.", "cp1250"),
            ("Russian", "Привет, как дела?", "cp1251"),
        )
        for language, source, legacy_encoding in examples:
            with self.subTest(language=language):
                self.assertEqual(
                    LogFollower._decode_line(
                        source.encode(legacy_encoding), game_language=language
                    ),
                    source,
                )
                self.assertEqual(
                    LogFollower._decode_line(source.encode("utf-8"), game_language=language),
                    source,
                )

    def test_log_follower_uses_current_game_language_for_new_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "client.log"
            path.write_bytes(b"")
            selected = {"language": "Polish"}
            follower = LogFollower(
                path, poll_interval=0.005,
                game_language=lambda: selected["language"],
            )
            stop = threading.Event()
            received = []

            def collect():
                for line in follower.lines(stop):
                    received.append(line)
                    if len(received) == 2:
                        stop.set()

            worker = threading.Thread(target=collect)
            worker.start()
            try:
                deadline = time.time() + 2
                while follower.file is None and time.time() < deadline:
                    time.sleep(0.005)
                with path.open("ab") as stream:
                    stream.write("Zażółć.\n".encode("cp1250"))
                    stream.flush()
                    while not received and time.time() < deadline:
                        time.sleep(0.005)
                    self.assertEqual(received, ["Zażółć."])
                    selected["language"] = "Russian"
                    stream.write("Привет.\n".encode("cp1251"))
                    stream.flush()
                worker.join(2)
                self.assertEqual(received, ["Zażółć.", "Привет."])
            finally:
                stop.set()
                worker.join(1)


if __name__ == "__main__":
    unittest.main()
