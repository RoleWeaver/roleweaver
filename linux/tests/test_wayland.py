import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import linux_platform as platform


class WaylandTests(unittest.TestCase):
    def test_copy_uses_stdin_not_shell(self):
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'}), patch.object(platform.shutil, 'which', return_value='/usr/bin/wl-copy'), patch.object(platform.subprocess, 'run') as run:
            platform.copy_draft('$(not-a-command)\nhello')
            self.assertEqual(run.call_args.kwargs['input'], '$(not-a-command)\nhello')
            self.assertNotIn('shell', run.call_args.kwargs)

    def test_copy_never_claims_sent_and_never_injects_keys(self):
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'}), patch.dict(sys.modules, {'pyperclip': types.ModuleType('pyperclip')}), patch.object(platform, 'copy_draft') as copy, patch.object(platform, '_xdotool') as x:
            self.assertFalse(platform.send_chat_to_nwn('Hello', {}))
            copy.assert_called_once_with('Hello')
            x.assert_not_called()

    def test_missing_clipboard_tool_is_actionable(self):
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'}), patch.object(platform.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'wl-clipboard'):
                platform.copy_draft('Hello')

    def test_core_wayland_does_not_import_pynput_or_enable_auto(self):
        import importlib
        providers = {name: types.ModuleType(name) for name in ['openai', 'google', 'pyperclip']}
        providers['openai'].OpenAI = Mock()
        providers['pynput'] = None
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'}), patch.dict(sys.modules, providers):
            core = importlib.import_module('nwn_ai_bot')
            try:
                bot = core.NWNAIBot.__new__(core.NWNAIBot)
                bot.auto_reply = True
                self.assertIsNone(bot.hotkey_listener())
                bot.toggle_auto()
                self.assertFalse(bot.auto_reply)
                bot.generate_reply = Mock(return_value='Hello')
                bot._publish_draft = Mock()
                bot.prepare_correction_candidate = Mock()
                bot.context = []
                with patch.object(core, 'copy_draft') as copy:
                    bot.generate_and_send('manual')
                    copy.assert_called_once_with('Hello')
                    self.assertEqual(bot.context, [])
                    bot.generate_reply.reset_mock()
                    bot.generate_and_send('auto')
                    bot.generate_reply.assert_not_called()
            finally:
                sys.modules.pop('nwn_ai_bot', None)


if __name__ == '__main__':
    unittest.main()
