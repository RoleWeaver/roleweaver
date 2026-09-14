"""Linux/X11 desktop adapter for the Role Weaver 1.2.2 client."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

_send_lock = threading.Lock()


def is_wayland():
    return bool(os.environ.get('WAYLAND_DISPLAY') or os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland')


def copy_draft(text):
    if is_wayland():
        if not shutil.which('wl-copy'):
            raise RuntimeError('Install wl-clipboard: sudo apt install wl-clipboard')
        # Send text through stdin, never as shell commands. wl-copy forks to own
        # the selection; DEVNULL avoids waiting on inherited output pipes.
        subprocess.run(['wl-copy', '--type', 'text/plain;charset=utf-8'],
                       input=text, text=True, encoding='utf-8', check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    else:
        import pyperclip
        pyperclip.copy(text)
    print('[DRAFT] Copied to clipboard. Open NWN chat, press Ctrl+V, review, then Enter to send.')


def nwn_log_directories():
    home = Path.home()
    paths = []
    override = os.environ.get('NWN_USER_DIRECTORY')
    if override:
        paths.append(Path(override).expanduser() / 'logs')
    paths.extend([
        home / '.local/share/Neverwinter Nights/logs',
        home / '.var/app/com.valvesoftware.Steam/.local/share/Neverwinter Nights/logs',
        home / 'Documents/Neverwinter Nights/logs',
    ])
    return list(dict.fromkeys(paths))


def migrate_default_log_paths(settings):
    """Replace nonexistent defaults copied from another user's installation.

    Existing files and explicit custom paths are retained.
    """
    default = str(nwn_log_directories()[0] / 'nwclientLog1.txt')
    def local_path(raw):
        if not raw or Path(raw).expanduser().is_file():
            return raw
        normalized = str(raw).replace('\\', '/').lower()
        old_default = re.match(
            r'^(?:[a-z]:/users/[^/]+/documents|/home/[^/]+/\.local/share|/home/[^/]+/documents)/neverwinter nights/logs/nwclientlog1\.txt$',
            normalized)
        return default if old_default else raw
    settings['log_path'] = local_path(settings.get('log_path')) or default
    if 'server_log_paths' in settings:
        settings['server_log_paths'] = {k: local_path(v) for k, v in (settings.get('server_log_paths') or {}).items()}
    for profile in (settings.get('discovered_servers') or {}).values():
        if isinstance(profile, dict) and profile.get('log_path'):
            profile['log_path'] = local_path(profile['log_path'])
    return settings


def require_desktop():
    if not sys.platform.startswith('linux'):
        raise RuntimeError('Use this package on Linux. Use the existing Windows distribution on Windows.')
    if not os.environ.get('DISPLAY'):
        raise RuntimeError('No X11 display found. On Ubuntu Wayland, install/enable Xwayland for the Tk interface, then launch from your desktop terminal.')
    required = ('wl-copy',) if is_wayland() else ('xdotool', 'xclip')
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        raise RuntimeError('Missing desktop packages: ' + ', '.join(missing) + '. See INSTALL_LINUX.md.')


def _xdotool(*args, allow_empty=False):
    result = subprocess.run(
        ['xdotool', *map(str, args)], capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=5, check=False,
    )
    if result.returncode:
        if allow_empty and result.returncode == 1 and not result.stderr.strip():
            return ''
        raise RuntimeError('X11 window/input operation failed: ' + (result.stderr.strip() or str(result.returncode)))
    return result.stdout.strip()


def get_foreground_window_title():
    if is_wayland():
        return None, None
    window = _xdotool('getactivewindow')
    if not window.isdigit():
        return None, None
    return window, _xdotool('getwindowname', window)


def find_window_handle(title_contains):
    target = (title_contains or '').strip()
    if not target:
        return None, None
    windows = _xdotool('search', '--onlyvisible', '--name', re.escape(target), allow_empty=True)
    for window in windows.splitlines():
        if window.isdigit():
            title = _xdotool('getwindowname', window)
            if target.casefold() in title.casefold():
                return window, title
    return None, None


def focus_nwn_window(title_contains):
    target = (title_contains or '').strip().casefold()
    if not target:
        return False, None
    window, title = get_foreground_window_title()
    if window and title and target in title.casefold():
        return True, title
    window, title = find_window_handle(title_contains)
    if not window:
        return False, None
    _xdotool('windowactivate', '--sync', window)
    active, active_title = get_foreground_window_title()
    return active == window and bool(active_title and target in active_title.casefold()), title


def manual_focus_countdown(seconds=5):
    if is_wayland():
        return None, None
    for remaining in range(seconds, 0, -1):
        print(f'[MANUAL] Click the NWN window now: {remaining}...')
        time.sleep(1)
    window, title = get_foreground_window_title()
    print(f'[MANUAL] Foreground: {title!r}')
    return window, title


def _check_focus(window, target):
    active, title = get_foreground_window_title()
    if active != window or not title or target.casefold() not in title.casefold():
        raise RuntimeError('NWN lost focus; input stopped. Check the game chat field before retrying.')


def send_chat_to_nwn(text, settings, leave_unsent=False, force_method=None):
    # Translate old saved keyboard_method values to the sole Linux backend.
    # Calls from the existing UI keep their original signature.
    import pyperclip
    text = ' '.join(str(text).split())
    text = text.translate(str.maketrans({'‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-', '…': '...', '\u00a0': ' '}))
    text = text[:int(settings.get('max_reply_characters', 430))].strip()
    if not text:
        return False
    if is_wayland():
        try:
            copy_draft(text)
        except Exception as exc:
            print(f'[CLIPBOARD ERROR] {exc}')
        # Copying is not evidence that the character spoke or the game received it.
        return False
    target = str(settings.get('window_title_contains', 'Neverwinter Nights')).strip()
    if not target:
        print('[SEND] Set a nonempty NWN window title in settings.json.')
        return False
    with _send_lock:
        try:
            require_desktop()
            if settings.get('focus_game_before_typing', True):
                ok, _ = focus_nwn_window(target)
                if not ok:
                    raise RuntimeError('Could not focus NWN. Click the game and use Keyboard Test.')
            window, _ = get_foreground_window_title()
            _check_focus(window, target)
            # Keep the draft on the clipboard, including on input failure.
            # Confirm clipboard access before opening the game's chat field.
            pyperclip.copy(text)
            time.sleep(float(settings.get('focus_delay_seconds', 0.60)))
            _check_focus(window, target)
            _xdotool('key', '--clearmodifiers', 'Return')
            time.sleep(float(settings.get('chat_open_delay_seconds', 0.45)))
            _check_focus(window, target)
            _xdotool('key', '--clearmodifiers', 'ctrl+v')
            time.sleep(float(settings.get('before_send_delay_seconds', 0.35)))
            if leave_unsent:
                print('[DRAFT] Paste requested. Check the NWN chat field; press Enter to send or Escape to cancel. Draft remains on the clipboard.')
                return True
            _check_focus(window, target)
            _xdotool('key', '--clearmodifiers', 'Return')
            print('[SEND] Chat input delivered via X11. Verify receipt in the game.')
            return True
        except Exception as exc:
            print(f'[SEND ERROR] {type(exc).__name__}: {exc}')
            return False
