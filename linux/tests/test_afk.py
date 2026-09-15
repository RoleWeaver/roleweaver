import threading
import unittest
from unittest.mock import Mock, patch
from roleweaver_afk import AFKMixin


class Bot(AFKMixin):
    def __init__(self):
        self.stop_event = threading.Event()
        self.paused = False
        self.auto_reply = True
        self.pending_auto_token = 0
        self.settings = {"character_name": "Hero Smith", "max_reply_characters": 240}
        self.character_prompt = "A sleepy scholar"
        self.request_lock = threading.Lock()
        self.client = Mock(generate=Mock(return_value="*Dozes quietly.*"))
        self.send_afk = Mock(return_value=True)
        self.afk_available = lambda: True
        self.init_afk()


class AFKTests(unittest.TestCase):
    def test_initial_check_interval_cooldown_and_quiet(self):
        b = Bot()
        with patch("roleweaver_afk.time.monotonic", return_value=0) as clock:
            b.toggle_afk()
            self.assertFalse(b.auto_reply)
            b.check_afk()
            self.assertEqual(b.send_afk.call_count, 1)
            b.observe_afk({"channel": "Talk", "message": "Hero, awake?"})
            clock.return_value = 29
            b.check_afk()
            self.assertEqual(b._afk_next_check, 30)
            clock.return_value = 30
            b.check_afk()
            self.assertEqual(b.send_afk.call_count, 1)
            clock.return_value = 180
            b.check_afk()
            self.assertEqual(b.send_afk.call_count, 2)
            clock.return_value = 400
            b.check_afk()
            self.assertEqual(b.send_afk.call_count, 2)
            b.toggle_afk()
            self.assertTrue(b.auto_reply)

    def test_address_detection(self):
        for event, expected in [
            ({"channel": "Talk", "message": "Hero, hello"}, True),
            ({"channel": "Talk", "message": "heroic deeds"}, False),
            ({"channel": "Talk", "message": "Hello everyone"}, False),
            ({"channel": "Tell", "message": "Hello"}, True),
            ({"channel": "Tell", "message": "Hello", "self": True}, False),
            ({"channel": "Talk", "message": "Hero", "_mode": "OOC"}, False),
        ]:
            b = Bot()
            b.toggle_afk()
            b._afk_pending = False
            b.observe_afk(event)
            self.assertEqual(b._afk_pending, expected)

    def test_cancel_during_generation_and_reactivation(self):
        b = Bot()
        b.toggle_afk()
        def generate(*args):
            b.toggle_afk()
            b.toggle_afk()
            return "*Old emote*"
        b.client.generate.side_effect = generate
        b.check_afk()
        b.send_afk.assert_not_called()

    def test_stop_and_pause_cancel_inflight(self):
        for cancel in (lambda b: b.stop_event.set(), lambda b: setattr(b, "paused", True)):
            b = Bot()
            b.toggle_afk()
            b.client.generate.side_effect = lambda *args: (cancel(b), "*Dozes*")[1]
            b.check_afk()
            b.send_afk.assert_not_called()

    def test_failure_backoff_and_unavailable(self):
        b = Bot()
        with patch("roleweaver_afk.time.monotonic", return_value=10):
            b.toggle_afk()
            b.client.generate.side_effect = RuntimeError("offline")
            b.check_afk()
            b.check_afk()
            self.assertEqual(b.client.generate.call_count, 1)
        b.toggle_afk()
        b.afk_available = lambda: False
        b.toggle_afk()
        self.assertFalse(b.afk)



class AFKIntegrationTests(unittest.TestCase):
    def test_bot_blocks_normal_send_while_afk_and_cancels_on_toggle(self):
        import test_pending_edits as fixtures
        fixture = fixtures.PendingTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        b = fixture.bot()
        b.afk_available = lambda: True
        b.toggle_afk()
        b.generate_reply = Mock(return_value="Hello")
        with patch.object(fixture.core, "send_chat_to_nwn") as send:
            b.generate_and_send("auto")
            b.generate_reply.assert_not_called()
            b.toggle_afk()
            b.generate_reply.side_effect = lambda: (b.toggle_afk(), "Hello")[1]
            b.generate_and_send("manual")
            send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
