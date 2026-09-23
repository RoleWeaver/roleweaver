import ast
import copy
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_pending_edits as fixtures
from roleweaver_drafts import DraftRecovery


class ClientFixTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PendingTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.core = self.fixture.root, self.fixture.core
        self.core.DEFAULT_NWN_LOG_DIR = self.root / "logs"
        self.core.DEFAULT_NWN_LOG_PATH = str(self.root / "logs" / "nwclientLog1.txt")
        self.core.DEFAULT_SETTINGS["log_path"] = self.core.DEFAULT_NWN_LOG_PATH
        self.core.DEFAULT_SETTINGS["server_log_paths"] = {"AUTO": self.core.DEFAULT_NWN_LOG_PATH}
        # Linux's discovery function also scans native directories.
        if hasattr(self.core, "nwn_log_directories"):
            self.core.nwn_log_directories = lambda: [self.core.DEFAULT_NWN_LOG_DIR]
        self.source = (Path(__file__).resolve().parents[1] / "nwn_ai_gui.py").read_text(encoding="utf-8")

    def gui_method(self, name):
        app = next(n for n in ast.parse(self.source).body if isinstance(n, ast.ClassDef) and n.name == "NWNAIApp")
        method = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == name)
        scope = {"core": self.core, "traceback": __import__("traceback")}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "gui", "exec"), scope)
        return scope[name]

    def logs(self):
        directory = self.core.DEFAULT_NWN_LOG_DIR
        directory.mkdir(parents=True, exist_ok=True)
        old, live = directory / "nwclientLog1.txt", directory / "nwclientLog2.txt"
        old.write_text("old\n")
        live.write_text("current\n")
        os.utime(old, (10, 10))
        os.utime(live, (20, 20))
        return old, live

    def test_string_widget_and_unregistered_editors_are_ignored(self):
        app = Mock(settings={})
        recovery = DraftRecovery(app, self.root)
        recovery.capture(".!combobox.popdown.f.l", "<FocusOut>")
        recovery.capture(Mock(), "<KeyRelease>")
        app._append_log.assert_not_called()
        self.assertEqual(recovery.pending, {})
        app.root.bind_all.assert_not_called()

    def test_only_requested_fields_are_registered(self):
        registrations = [n for n in ast.walk(ast.parse(self.source)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "track"]
        self.assertEqual(len(registrations), 5)
        self.assertNotIn("edit_recovery.offer", self.source)
        self.assertIn('self.edit_recovery.track(self.guidance_text, "Guidance")', self.source)
        self.assertIn('self.edit_recovery.track(self.ai_draft_text, "AI Draft")', self.source)
        self.assertIn('self.edit_recovery.track(self.translated_draft_text, "Game-language Draft")', self.source)

    def test_editable_translation_drafts_replace_response_seed_workflow(self):
        self.assertNotIn("Response Seed (optional)", self.source)
        self.assertIn('text="Draft in your language"', self.source)
        self.assertIn('text="Draft in game language"', self.source)
        self.assertIn('text="Language Settings"', self.source)

    def test_reply_generation_requests_the_configured_user_language(self):
        bot = self.fixture.bot()
        bot.settings["user_language"] = "French"
        event = {
            "speaker": "Alice",
            "channel": "Talk",
            "message": "Is something wrong?",
            "self": False,
            "_mode": "IC",
        }
        bot.context.append(event)
        bot.last_external_event = event
        bot.request_ai = Mock(
            return_value=SimpleNamespace(
                text="I noticed you arrived late.",
                duration_seconds=0.1,
                model="test-model",
            )
        )

        self.assertEqual(bot.generate_reply(), "I noticed you arrived late.")
        instructions = bot.request_ai.call_args.args[0]
        self.assertIn("Write the draft in French", instructions)

    def test_translation_workflow_filters_self_chat_and_publishes_editable_drafts(self):
        bot = self.fixture.bot()
        bot.settings.update(user_language="English", game_language="German")
        bot.context.extend([
            {"_context_id": 1, "speaker": "Hero", "channel": "Talk", "message": "Mine", "self": True},
            {"_context_id": 2, "speaker": "Alice", "channel": "Talk", "message": "Hallo", "self": False},
        ])
        incoming = SimpleNamespace(id="2", speaker="Alice", channel="Talk", translated_text="Hello", detected_source_language=SimpleNamespace(name="German"))
        outgoing = SimpleNamespace(translated_text="Guten Abend")
        bot.translation_service = Mock()
        bot.translation_service.translate.side_effect = [SimpleNamespace(messages=(incoming,)), SimpleNamespace(message=Mock(return_value=outgoing))]
        bot.translate_recent_chat(); bot.translate_draft("Good evening")
        first_request = bot.translation_service.translate.call_args_list[0].args[0]
        self.assertEqual([message.id for message in first_request.messages], ["2"])
        self.assertEqual(bot.translated_chat[0]["text"], "Hello")
        self.assertEqual(bot.translated_draft, "Guten Abend")
        self.assertEqual(bot.translated_draft_source, "Good evening")

    def test_editor_revision_uses_current_seed_and_target_language(self):
        bot = self.fixture.bot()
        bot.settings.update(user_language="French", game_language="German")
        bot.request_ai = Mock(return_value=SimpleNamespace(
            text="Neue Fassung", duration_seconds=0.1, model="test-model"
        ))
        self.assertEqual(bot.revise_editor_draft({
            "language": "game", "seed": "Mein bearbeiteter Satz",
            "user_source": "Ma phrase", "mode": "regenerate",
        }), "Neue Fassung")
        instructions, prompt = bot.request_ai.call_args.args[:2]
        self.assertIn("Write the draft in German", instructions)
        self.assertIn("Mein bearbeiteter Satz", prompt)
        self.assertEqual(bot.translated_draft_source, "Ma phrase")
        self.assertEqual(bot.translated_draft, "Neue Fassung")
        self.assertEqual(bot.last_draft_version, 0)

        bot.request_ai.return_value.text = "Nouvelle réponse"
        self.assertEqual(bot.revise_editor_draft({
            "language": "user", "seed": "Ma phrase modifiée", "mode": "shorter",
        }), "Nouvelle réponse")
        instructions, prompt = bot.request_ai.call_args.args[:2]
        self.assertIn("Write the draft in French", instructions)
        self.assertIn("Ma phrase modifiée", prompt)
        self.assertIn("noticeably shorter", prompt)
        self.assertEqual(bot.last_draft, "Nouvelle réponse")

    def test_backtranslation_keeps_edited_game_draft_authoritative(self):
        bot = self.fixture.bot()
        bot.settings.update(user_language="English", game_language="German")
        bot.translation_service = Mock()
        bot.translation_service.translate.return_value.message.return_value.translated_text = "My edited line"
        self.assertEqual(bot.translate_game_draft("Mein bearbeiteter Satz"), "My edited line")
        request = bot.translation_service.translate.call_args.args[0]
        self.assertEqual(request.source_language, "German")
        self.assertEqual(request.target_language, "English")
        self.assertEqual(bot.translated_draft, "Mein bearbeiteter Satz")
        self.assertEqual(bot.translated_draft_source, "My edited line")
        self.assertEqual(bot.last_draft, "My edited line")

    def test_editor_buttons_queue_visible_text(self):
        app = Mock()
        app.ai_draft_text.get.return_value = " My revised line "
        app.translated_draft_text.get.return_value = " Mein Satz "
        self.gui_method("_request_draft_variant")(app, "shorter")
        app.bot.action_queue.put.assert_called_with(("revise_editor_draft", {
            "language": "user", "seed": "My revised line", "mode": "shorter",
        }))
        self.gui_method("refine_game_draft")(app)
        app.bot.action_queue.put.assert_called_with(("revise_editor_draft", {
            "language": "game", "seed": "Mein Satz", "mode": "regenerate",
            "user_source": "My revised line",
        }))
        self.gui_method("translate_game_draft")(app)
        app.bot.action_queue.put.assert_called_with(("translate_game_draft", "Mein Satz"))

    def test_candidate_selection_waits_for_explicit_translation(self):
        app = Mock()
        app.candidate_var.get.return_value = "Candidate 2"
        app.bot.candidate_replies = ["First line", "Chosen line"]
        self.gui_method("_select_candidate")(app)
        app._replace_draft_text.assert_called_once_with(app.ai_draft_text, "Chosen line")
        app.bot.action_queue.put.assert_not_called()
        self.assertIn("Translate", app.bot.translation_status)

    def test_generated_replacement_is_one_undo_step(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"A desktop display is required: {exc}")
        root.withdraw()
        self.addCleanup(root.destroy)
        editor = tk.Text(root, undo=True)
        editor.insert("1.0", "My original wording")
        self.gui_method("_replace_draft_text")(editor, "Generated wording")
        editor.edit_undo()
        self.assertEqual(editor.get("1.0", "end").strip(), "My original wording")

    def test_clear_all_removes_recovery_only_and_cancels_pending(self):
        recovery = DraftRecovery(Mock(settings={}), self.root)
        recovery.store.save("one", "old", {})
        recovery.pending["two"] = ("pending", {})
        recovery.timer = "scheduled"
        original = self.root / "Characters" / "hero.txt"
        original.parent.mkdir()
        original.write_text("saved profile")
        recovery.clear_all()
        recovery.flush()
        self.assertEqual(recovery.store.records(), [])
        self.assertEqual(original.read_text(), "saved profile")
        recovery.root.after_cancel.assert_called_with("scheduled")

    def test_copy_works_even_if_list_selection_is_lost(self):
        recovery = DraftRecovery(Mock(settings={}), self.root)
        recovery.store.save("one", "full recovered text", {"label": "Guidance"})
        listing, detail, win = Mock(), Mock(), Mock()
        win.winfo_screenwidth.return_value = 1024
        win.winfo_screenheight.return_value = 768
        listing.curselection.return_value = ()
        detail.tag_ranges.return_value = ("sel.first", "sel.last")
        detail.get.return_value = "selected recovered text"
        with patch("tkinter.Toplevel", return_value=win), patch("tkinter.Listbox", return_value=listing) as listbox, patch("tkinter.Text", return_value=detail) as text, patch("tkinter.ttk.Label"), patch("tkinter.ttk.Scrollbar"), patch("tkinter.ttk.Frame"), patch("tkinter.ttk.Button") as button:
            recovery.show()
            callback = next(c.kwargs["command"] for c in button.call_args_list if c.kwargs.get("text") == "Copy text")
            callback()
            self.assertFalse(listbox.call_args.kwargs["exportselection"])
            self.assertFalse(text.call_args.kwargs["exportselection"])
        recovery.root.clipboard_append.assert_called_once_with("selected recovered text")

    def test_server_first_and_exit_uses_normal_close(self):
        server = self.source.index('self._settings_nav_buttons["Server / Log"] =')
        character = self.source.index('self._settings_nav_buttons["Character"] =')
        self.assertLess(server, character)
        self.assertIn('text="Exit Program", command=self.on_close', self.source)

    def test_auto_prefers_newest_over_cached_default(self):
        old, live = self.logs()
        settings = copy.deepcopy(self.core.DEFAULT_SETTINGS)
        settings["server_log_paths"]["AUTO"] = str(old)
        settings["log_path"] = str(old)
        self.assertEqual(self.core.get_server_log_path(settings, "AUTO"), str(live))
        settings["server_log_paths"]["NAMED"] = str(old)
        self.assertEqual(self.core.get_server_log_path(settings, "NAMED"), str(old))

    def test_world_scan_does_not_replace_newest_with_older_log(self):
        old, live = self.logs()
        settings = copy.deepcopy(self.core.DEFAULT_SETTINGS)
        with patch.object(self.core, "detect_world_from_log", side_effect=lambda p: {"id": "WORLD", "log_path": str(p)}):
            self.core.refresh_discovered_servers(settings)
        self.assertEqual(settings["server_log_paths"]["WORLD"], str(live))

    def test_auto_start_binds_live_log_and_receives_appended_chat(self):
        old, live = self.logs()
        settings = copy.deepcopy(self.core.DEFAULT_SETTINGS)
        settings["log_path"] = str(old)
        settings["server_log_paths"]["AUTO"] = str(old)
        self.core.save_settings(settings)
        app = Mock(settings=settings)
        app._selected_server_profile.return_value = "AUTO"
        app.log_path_var.get.return_value = str(old)
        with patch.object(self.core, "detect_world_from_log", side_effect=lambda p: {"id": "WORLD", "display_name": "World", "log_path": str(p), "parser_profile": "adaptive"}):
            profile, selected = self.gui_method("_apply_server_settings")(app)
        self.assertEqual((profile, selected), ("WORLD", str(live)))
        self.assertEqual(app.settings["log_path"], str(live))
        bot = Mock(settings=dict(app.settings, character_name="Hero", poll_interval_seconds=0.01), stop_event=threading.Event())
        bot.should_suppress_duplicate_self.return_value = False
        received, opened = threading.Event(), threading.Event()
        bot.add_chat_event.side_effect = lambda event: (received.set(), bot.stop_event.set())
        app.output_queue = queue.Queue()
        original_open = self.core.LogFollower._open_at_end
        def open_and_signal(follower):
            original_open(follower)
            opened.set()
        with patch.object(self.core.LogFollower, "_open_at_end", open_and_signal):
            worker = threading.Thread(target=self.gui_method("_log_loop"), args=(app, bot))
            worker.start()
            try:
                self.assertTrue(opened.wait(3))
                with live.open("a") as stream:
                    stream.write("Alice: [Talk] Incoming live message\n")
                self.assertTrue(received.wait(3))
            finally:
                bot.stop_event.set()
                worker.join(3)
        self.assertEqual(bot.add_chat_event.call_args.args[0]["message"], "Incoming live message")
        self.assertEqual(app.output_queue.get_nowait(), ("BOT_LOOP_STOPPED", bot))

    def test_world_is_resolved_before_character_load(self):
        start = self.source[self.source.index("    def start_bot(self):"):self.source.index("    def _log_loop(")]
        self.assertLess(start.index("self._apply_server_settings()"), start.index("self._load_selected_character_profile("))

    def test_linux_default_migrates_other_user_without_overwriting_custom(self):
        if not hasattr(self.core, "migrate_default_log_paths"):
            self.skipTest("Linux migration only")
        import linux_platform
        with patch.object(linux_platform.Path, "home", return_value=self.root), patch.dict(os.environ, {}, clear=True):
            settings = {"log_path": "/home/olduser/.local/share/Neverwinter Nights/logs/nwclientLog1.txt", "server_log_paths": {"CUSTOM": "/srv/nwn/private.txt", "AUTO": r"C:\Users\Someone\Documents\Neverwinter Nights\logs\nwclientLog1.txt"}}
            linux_platform.migrate_default_log_paths(settings)
            expected = str(self.root / ".local/share/Neverwinter Nights/logs/nwclientLog1.txt")
            self.assertEqual(settings["log_path"], expected)
            self.assertEqual(settings["server_log_paths"]["AUTO"], expected)
            self.assertEqual(settings["server_log_paths"]["CUSTOM"], "/srv/nwn/private.txt")
            legacy = {"log_path": "/srv/nwn/private.txt"}
            linux_platform.migrate_default_log_paths(legacy)
            self.assertNotIn("server_log_paths", legacy)
            self.assertEqual(legacy["log_path"], "/srv/nwn/private.txt")
