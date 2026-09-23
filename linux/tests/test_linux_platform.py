import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import linux_platform as platform


class DesktopTests(unittest.TestCase):
    def test_wayland_with_xwayland_is_allowed(self):
        with patch.object(sys, 'platform', 'linux'), patch.dict(os.environ, {'DISPLAY': ':0', 'WAYLAND_DISPLAY': 'wayland-0'}, clear=True):
            with patch.object(platform.shutil, 'which', return_value='/usr/bin/wl-copy'):
                platform.require_desktop()

    def test_missing_display_is_actionable(self):
        with patch.object(sys, 'platform', 'linux'), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'No X11 display'):
                platform.require_desktop()

    def test_x11_checks_tools(self):
        with patch.object(sys, 'platform', 'linux'), patch.dict(os.environ, {'DISPLAY': ':0'}, clear=True), patch.object(platform.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'xdotool, xclip'):
                platform.require_desktop()

    def test_x11_preflight_success(self):
        with patch.object(sys, 'platform', 'linux'), patch.dict(os.environ, {'DISPLAY': ':0'}, clear=True), patch.object(platform.shutil, 'which', return_value='/usr/bin/tool'):
            platform.require_desktop()

    def test_custom_log_directory_precedes_defaults(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'NWN_USER_DIRECTORY': temp}):
            self.assertEqual(platform.nwn_log_directories()[0], Path(temp) / 'logs')

    def test_title_is_literal_and_subprocess_has_no_shell(self):
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0, '123\n', ''), subprocess.CompletedProcess([], 0, 'NWN [test]', '')])
        with patch.object(platform.subprocess, 'run', run):
            self.assertEqual(platform.find_window_handle('NWN [test]'), ('123', 'NWN [test]'))
        self.assertEqual(run.call_args_list[0].args[0][-1], r'NWN\ \[test\]')
        self.assertNotIn('shell', run.call_args.kwargs)

    def test_activation_must_select_requested_window(self):
        with patch.object(platform, 'get_foreground_window_title', side_effect=[('7', 'Editor'), ('8', 'NWN other')]), patch.object(platform, 'find_window_handle', return_value=('9', 'NWN')), patch.object(platform, '_xdotool'):
            self.assertEqual(platform.focus_nwn_window('NWN'), (False, 'NWN'))


class SendTests(unittest.TestCase):
    def setUp(self):
        self.clipboard = types.ModuleType('pyperclip')
        self.clipboard.copy = Mock()
        self.patches = [
            patch.dict(sys.modules, {'pyperclip': self.clipboard}),
            patch.object(platform, 'require_desktop'),
            patch.object(platform.time, 'sleep'),
            patch.object(platform, '_xdotool'),
            patch.object(platform, 'get_foreground_window_title', return_value=('42', 'Neverwinter Nights')),
        ]
        self.mocks = [p.start() for p in self.patches]
        self.addCleanup(lambda: [p.stop() for p in reversed(self.patches)])
        self.commands = self.mocks[3]
        self.focus = self.mocks[4]
        self.settings = {'focus_game_before_typing': False, 'max_reply_characters': 430}

    def test_draft_does_not_submit(self):
        self.assertTrue(platform.send_chat_to_nwn('Hello\n“friend”', self.settings, leave_unsent=True))
        self.clipboard.copy.assert_called_once_with('Hello "friend"')
        self.assertEqual([c.args[-1] for c in self.commands.call_args_list], ['Return', 'ctrl+v'])

    def test_x11_paste_normalizes_punctuation_but_keeps_accents(self):
        self.assertTrue(platform.send_chat_to_nwn('I’ll stay—don’t worry… François', self.settings, leave_unsent=True))
        self.clipboard.copy.assert_called_once_with("I'll stay-don't worry... François")

    def test_send_submits_once_after_paste_and_maps_legacy_method(self):
        self.assertTrue(platform.send_chat_to_nwn('Hello', self.settings, force_method='scancode'))
        self.assertEqual([c.args[-1] for c in self.commands.call_args_list], ['Return', 'ctrl+v', 'Return'])

    def test_wrong_window_never_receives_input(self):
        self.focus.return_value = ('77', 'Text editor')
        self.assertFalse(platform.send_chat_to_nwn('Hello', self.settings))
        self.commands.assert_not_called()

    def test_focus_loss_after_chat_open_aborts_before_paste(self):
        self.focus.side_effect = [('42', 'Neverwinter Nights')] * 3 + [('77', 'Text editor')]
        self.assertFalse(platform.send_chat_to_nwn('Hello', self.settings))
        self.assertEqual([c.args[-1] for c in self.commands.call_args_list], ['Return'])

    def test_focus_loss_after_paste_prevents_submit(self):
        self.focus.side_effect = [('42', 'Neverwinter Nights')] * 4 + [('77', 'Text editor')]
        self.assertFalse(platform.send_chat_to_nwn('Hello', self.settings))
        self.assertEqual([c.args[-1] for c in self.commands.call_args_list], ['Return', 'ctrl+v'])

    def test_clipboard_failure_does_not_open_chat(self):
        self.clipboard.copy.side_effect = RuntimeError('clipboard unavailable')
        self.assertFalse(platform.send_chat_to_nwn('Hello', self.settings))
        self.commands.assert_not_called()

    def test_timeout_returns_failure(self):
        self.commands.side_effect = subprocess.TimeoutExpired('xdotool', 5)
        self.assertFalse(platform.send_chat_to_nwn('Hello', self.settings))

    def test_empty_title_is_rejected(self):
        self.settings['window_title_contains'] = ''
        self.assertFalse(platform.send_chat_to_nwn('Hello', self.settings))
        self.commands.assert_not_called()


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import actual core with external providers/hotkeys stubbed. No API calls
        # or desktop access are necessary to exercise log discovery and parsing.
        modules = {name: types.ModuleType(name) for name in ['pyperclip', 'pynput', 'openai', 'google']}
        modules['pynput'].keyboard = Mock()
        modules['openai'].OpenAI = Mock()
        cls.stub = patch.dict(sys.modules, modules)
        cls.stub.start()
        cls.core = importlib.import_module('nwn_ai_bot')

    @classmethod
    def tearDownClass(cls):
        cls.stub.stop()
        sys.modules.pop('nwn_ai_bot', None)

    def test_core_imports_and_uses_linux_adapter(self):
        self.assertIs(self.core.send_chat_to_nwn, platform.send_chat_to_nwn)
        self.assertEqual(self.core.DEFAULT_SETTINGS['keyboard_method'], 'x11')
        self.assertEqual(list(self.core.SERVER_PROFILES), ['AUTO'])

    def test_native_discovery_and_configured_path(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            logs = base / 'logs'
            logs.mkdir()
            native = logs / 'nwclientLog1.txt'
            native.write_text('example', encoding='utf-8')
            custom = base / 'custom.txt'
            custom.write_text('example', encoding='utf-8')
            with patch.object(self.core, 'nwn_log_directories', return_value=[logs]):
                self.assertEqual(set(self.core.discover_nwn_log_files({'log_path': str(custom)})), {native, custom})

    def test_parser_retains_structured_dialogue(self):
        event = self.core.parse_chat_line('[abc] Example Visitor: [Talk] Hello there.', 'Example NPC', 'AUTO', 'adaptive')
        self.assertIsNotNone(event)


if __name__ == '__main__':
    unittest.main()
