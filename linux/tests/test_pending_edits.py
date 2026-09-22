import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

import roleweaver_storage as storage
from roleweaver_pending import SummaryJournal
from roleweaver_drafts import DraftStore, DraftRecovery
import roleweaver_backup as backups


class PendingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.frozen = patch.object(storage, "_frozen", False)
        self.frozen.start()
        self.addCleanup(self.frozen.stop)
        modules = {name: types.ModuleType(name) for name in ("openai", "pynput", "pyautogui", "pyperclip")}
        modules["openai"].OpenAI = Mock()
        modules["pynput"].keyboard = Mock()
        source = Path(__file__).resolve().parents[1] / "nwn_ai_bot.py"
        spec = importlib.util.spec_from_file_location("pending_test_core", source)
        self.core = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(self.core)
        for name, value in vars(self.core).copy().items():
            if isinstance(value, Path) and value.is_relative_to(source.parent):
                setattr(self.core, name, self.root / value.relative_to(source.parent))
        self.settings = dict(self.core.DEFAULT_SETTINGS, character_name="Hero", server_profile="AUTO")
        self.response = {"summary": "Alice offered help.", "memories": {"Alice": "Offered help"},
            "interaction_events": {"Alice": [{"summary": "Offered help", "importance": 6}]}}

    def bot(self, client=None):
        client = client or Mock(generate=Mock(return_value=json.dumps(self.response)))
        return self.core.NWNAIBot(self.settings, "Hero", client)

    def queue(self, bot, text="Hello"):
        bot.summary_journal.append({"speaker": "Alice", "channel": "Talk", "message": text, "self": False, "_mode": "IC"})
        bot.summary_event_buffer = bot.summary_journal.events()

    def test_relationship_name_filter_supports_accented_names_and_curly_apostrophes(self):
        self.assertTrue(self.core.is_likely_relationship_character("Élodie D’Arcy"))
        self.assertFalse(self.core.is_likely_relationship_character("the people in the city"))

    def test_queue_survives_restart_and_commits(self):
        first = self.bot()
        self.queue(first)
        second = self.bot()
        self.assertEqual(len(second.summary_event_buffer), 1)
        second.flush_memory_summary()
        self.assertEqual(second.summary_journal.events(), [])
        third = self.bot()
        self.assertEqual(third.running_summary, "Alice offered help.")
        self.assertTrue(third.memory_data.get("_last_summary_batch"))

    def test_provider_failure_retains_pending_events(self):
        bot = self.bot(Mock(generate=Mock(side_effect=RuntimeError("offline"))))
        self.queue(bot)
        bot.flush_memory_summary()
        self.assertEqual(len(self.bot().summary_event_buffer), 1)
        self.assertFalse(bot.summary_in_progress)

    def test_cached_response_is_reused_after_application_failure(self):
        bot = self.bot()
        self.queue(bot)
        with patch.object(self.core.NWNAIBot, "_apply_summary_response", side_effect=RuntimeError("interrupted")):
            bot.flush_memory_summary()
        self.assertFalse(bot.memory_data.get("_last_summary_batch"))
        client = Mock(generate=Mock(side_effect=AssertionError("must reuse cached response")))
        resumed = self.bot(client)
        resumed.flush_memory_summary()
        client.generate.assert_not_called()
        self.assertEqual(resumed.summary_journal.events(), [])

    def test_crash_after_commit_before_ack_does_not_apply_twice(self):
        bot = self.bot()
        self.queue(bot)
        with patch.object(bot.summary_journal, "acknowledge", side_effect=OSError("crash before ack")):
            bot.flush_memory_summary()
        persisted = json.loads(self.core._memory_paths(self.settings)[1].read_text())
        resumed = self.bot()
        resumed.flush_memory_summary()
        resumed.client.generate.assert_not_called()
        after = json.loads(self.core._memory_paths(self.settings)[1].read_text())
        self.assertEqual(persisted, after)
        self.assertEqual(resumed.summary_journal.events(), [])

    def test_memory_save_failure_retains_response_and_original_memory(self):
        bot = self.bot()
        self.core.save_persistent_memory(bot.settings, bot.memory_data, "original")
        self.queue(bot)
        with patch.object(self.core, "save_persistent_memory", side_effect=OSError("disk full")):
            bot.flush_memory_summary()
        self.assertEqual(bot.running_summary, "original")
        self.assertEqual(len(bot.summary_journal.events()), 1)
        self.assertIsNotNone(bot.summary_journal.begin()["response"])

    def test_live_edits_and_new_events_survive_request(self):
        bot = self.bot()
        self.queue(bot)
        def respond(*args):
            bot.memory_data["manual_test"] = "keep"
            self.queue(bot, "new event while waiting")
            return json.dumps(self.response)
        bot.client.generate.side_effect = respond
        bot.flush_memory_summary()
        self.assertEqual(bot.memory_data["manual_test"], "keep")
        self.assertEqual(len(bot.summary_journal.events()), 1)
        self.assertEqual(bot.summary_journal.events()[0]["message"], "new event while waiting")

    def test_summary_cache_file_failure_does_not_lose_commit(self):
        bot = self.bot()
        self.queue(bot)
        original = storage.atomic_write_text
        def fail_cache(path, *args, **kwargs):
            if Path(path).name == "running_summary.txt":
                raise OSError("cache unavailable")
            return original(path, *args, **kwargs)
        with patch.object(storage, "atomic_write_text", side_effect=fail_cache):
            bot.flush_memory_summary()
        self.assertEqual(self.bot().running_summary, "Alice offered help.")
        self.assertEqual(bot.summary_journal.events(), [])

    def test_invalid_response_keeps_events(self):
        bot = self.bot(Mock(generate=Mock(return_value="{}")))
        self.queue(bot)
        bot.flush_memory_summary()
        self.assertEqual(len(bot.summary_journal.events()), 1)
        self.assertIsNone(bot.summary_journal.begin()["response"])

    def test_concurrent_summary_request_is_not_duplicated(self):
        bot = self.bot()
        self.queue(bot)
        entered, release = threading.Event(), threading.Event()
        def respond(*args):
            entered.set()
            release.wait(5)
            return json.dumps(self.response)
        bot.client.generate.side_effect = respond
        worker = threading.Thread(target=bot.flush_memory_summary)
        worker.start()
        try:
            self.assertTrue(entered.wait(5))
            bot.flush_memory_summary()
        finally:
            release.set()
            worker.join(5)
        self.assertEqual(bot.client.generate.call_count, 1)

    def test_draft_round_trip_includes_empty_edit(self):
        store = DraftStore(self.root)
        store.save("field", "some unsaved text", {"character_name": "Hero"})
        store.save("field", "", {"character_name": "Hero"})
        self.assertEqual(DraftStore(self.root).records()[0][1]["text"], "")
        store.save("different-character", "other", {"character_name": "Other"})
        self.assertEqual(len(store.records()), 2)

    def test_autorecovery_preserves_newer_drafts_and_queue(self):
        store = DraftStore(self.root)
        path = store.save("field", "older", {})
        journal = SummaryJournal(self.root / "RoleWeaver_Data" / "AUTO" / "Hero" / "pending_summaries.json")
        journal.append({"message": "older"})
        archive = backups.create_backup(self.root, self.root / "copy.zip")
        store.save("field", "newer", {})
        journal.append({"message": "newer"})
        backups.restore_backup(self.root, archive, preserve_recovery_work=True)
        self.assertEqual(json.loads(path.read_text())["text"], "newer")
        self.assertEqual(len(journal.events()), 2)

    def test_api_field_excluded_even_when_key_is_visible(self):
        recovery = DraftRecovery.__new__(DraftRecovery)
        key = Mock()
        recovery.app = Mock(api_entry=key)
        recovery.viewer = None
        self.assertFalse(recovery.eligible(key))
        masked = Mock()
        masked.winfo_class.return_value = "TEntry"
        masked.cget.side_effect = lambda name: "*" if name == "show" else "normal"
        self.assertFalse(recovery.eligible(masked))

    def test_draft_capture_is_bounded_during_continuous_typing(self):
        app = Mock(settings={"server_profile": "AUTO", "character_name": "Hero", "api_key": "never store"})
        app.root.after.return_value = "timer"
        recovery = DraftRecovery(app, self.root)
        widget = Mock()
        widget.winfo_class.return_value = "Text"
        widget.cget.return_value = "normal"
        widget.winfo_toplevel.return_value.title.return_value = "Character Editor"
        widget.master.winfo_children.return_value = []
        widget.get.return_value = ""
        recovery.track(widget, "Character Name")
        recovery.capture(widget, "<FocusIn>")
        widget.get.return_value = "first"
        recovery.capture(widget, "<KeyRelease>")
        widget.get.return_value = "latest"
        recovery.capture(widget, "<KeyRelease>")
        app.root.after.assert_called_once()
        recovery.flush()
        records = recovery.store.records()
        self.assertEqual(records[0][1]["text"], "latest")
        self.assertNotIn("never store", json.dumps(records[0][1]))

    def test_failed_draft_save_stays_pending_for_retry(self):
        app = Mock(settings={})
        recovery = DraftRecovery(app, self.root)
        recovery.pending["field"] = ("unsaved", {})
        with patch.object(recovery.store, "save", side_effect=OSError("disk full")):
            recovery.flush()
        self.assertIn("field", recovery.pending)
        recovery.flush()
        self.assertEqual(recovery.pending, {})
        self.assertEqual(recovery.store.records()[0][1]["text"], "unsaved")

    def test_same_character_uses_one_summary_lock(self):
        first = self.bot()
        second = self.bot()
        self.assertIs(first._summary_lock, second._summary_lock)

    def test_live_ic_event_is_journaled_before_summary_threshold(self):
        bot = self.bot()
        bot.add_chat_event({"speaker": "Alice", "message": "Hello", "channel": "Talk", "self": False})
        bot.add_chat_event({"speaker": "Alice", "message": "((out of character))", "channel": "Talk", "self": False, "_mode": "OOC"})
        self.assertEqual(len(self.bot().summary_event_buffer), 1)
        bot.client.generate.assert_not_called()

    def test_partial_application_never_leaks_into_live_memory(self):
        bot = self.bot()
        self.queue(bot)
        def interrupted(view, events, parsed):
            view.memory_data["partial"] = "must not escape"
            raise OSError("interrupted while applying")
        with patch.object(self.core.NWNAIBot, "_apply_summary_response", interrupted):
            bot.flush_memory_summary()
        self.assertNotIn("partial", bot.memory_data)
        self.assertNotIn("partial", self.bot().memory_data)
        self.assertEqual(len(bot.summary_journal.events()), 1)


if __name__ == "__main__":
    unittest.main()
