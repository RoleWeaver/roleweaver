"""macOS game-window and keyboard adapter for Role Weaver."""

import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from roleweaver.game_text import normalize_game_punctuation

_send_lock = threading.Lock()

_WINDOWS_SCRIPT = r"""
tell application "System Events"
    set rows to {}
    repeat with p in application processes
        try
            set processName to name of p as text
            set processId to unix id of p as text
            set windowName to ""
            try
                set windowName to name of front window of p as text
            end try
            set end of rows to processId & tab & processName & tab & windowName
        end try
    end repeat
    set AppleScript's text item delimiters to linefeed
    return rows as text
end tell
"""

_FRONT_SCRIPT = r"""
tell application "System Events"
    set p to first application process whose frontmost is true
    set processName to name of p as text
    set processId to unix id of p as text
    set windowName to ""
    try
        set windowName to name of front window of p as text
    end try
    return processId & tab & processName & tab & windowName
end tell
"""

_FOCUS_SCRIPT = r"""
on run argv
    set targetId to (item 1 of argv) as integer
    tell application "System Events"
        set frontmost of (first application process whose unix id is targetId) to true
    end tell
end run
"""

_RETURN_SCRIPT = 'tell application "System Events" to key code 36'
_PASTE_SCRIPT = 'tell application "System Events" to keystroke "v" using command down'


def is_wayland():
    """Compatibility flag consumed by the shared Linux-derived client."""
    return False


def require_desktop():
    if sys.platform != "darwin":
        raise RuntimeError("The macOS client requires macOS.")


def nwn_log_directories():
    home = Path.home()
    paths = []
    if os.environ.get("NWN_USER_DIRECTORY"):
        paths.append(Path(os.environ["NWN_USER_DIRECTORY"]).expanduser() / "logs")
    paths.extend(
        [
            home / "Documents/Neverwinter Nights/logs",
            home / "Library/Application Support/Neverwinter Nights/logs",
        ]
    )
    return list(dict.fromkeys(paths))


def migrate_default_log_paths(settings):
    default = str(nwn_log_directories()[0] / "nwclientLog1.txt")

    def local_path(raw):
        if not raw or Path(raw).expanduser().is_file():
            return raw
        normalized = str(raw).replace("\\", "/").lower()
        known_default = re.match(
            r"^(?:[a-z]:/users/[^/]+/documents|"
            r"/home/[^/]+/(?:\.local/share|documents)|"
            r"/users/[^/]+/documents)/neverwinter nights/logs/nwclientlog1\.txt$",
            normalized,
        )
        return default if known_default else raw

    settings["log_path"] = local_path(settings.get("log_path")) or default
    if "server_log_paths" in settings:
        settings["server_log_paths"] = {
            key: local_path(value)
            for key, value in (settings.get("server_log_paths") or {}).items()
        }
    for profile in (settings.get("discovered_servers") or {}).values():
        if isinstance(profile, dict) and profile.get("log_path"):
            profile["log_path"] = local_path(profile["log_path"])
    return settings


def copy_draft(text):
    normalized = normalize_game_punctuation(str(text))
    subprocess.run(
        ["pbcopy"],
        input=normalized,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=5,
    )
    print("[DRAFT] Copied to clipboard. Open NWN chat, press Command+V, review, then Enter.")


def _osascript(script, *args):
    result = subprocess.run(
        ["osascript", "-e", script, *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=8,
    )
    if result.returncode:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        raise RuntimeError(
            f"macOS desktop control failed: {detail}. Allow RoleWeaver in "
            "System Settings > Privacy & Security > Accessibility and Automation."
        )
    return result.stdout.strip()


def _parse_process(row):
    parts = row.split("\t", 2)
    if len(parts) != 3 or not parts[0].isdigit():
        return None, None, None
    return parts[0], parts[1], parts[2]


def _matches(name, window, target):
    target = target.casefold()
    return bool(target and (target in name.casefold() or target in window.casefold()))


def get_foreground_window_title():
    process_id, process_name, window_name = _parse_process(_osascript(_FRONT_SCRIPT))
    return process_id, " ".join(part for part in (process_name, window_name) if part)


def find_window_handle(title_contains):
    target = str(title_contains or "").strip()
    if not target:
        return None, None
    for row in _osascript(_WINDOWS_SCRIPT).splitlines():
        process_id, process_name, window_name = _parse_process(row)
        if process_id and _matches(process_name, window_name, target):
            return process_id, " ".join(part for part in (process_name, window_name) if part)
    return None, None


def focus_nwn_window(title_contains):
    target = str(title_contains or "").strip()
    if not target:
        return False, None
    process_id, title = get_foreground_window_title()
    if process_id and target.casefold() in (title or "").casefold():
        return True, title
    process_id, title = find_window_handle(target)
    if not process_id:
        return False, None
    _osascript(_FOCUS_SCRIPT, process_id)
    active_id, active_title = get_foreground_window_title()
    return active_id == process_id and target.casefold() in (active_title or "").casefold(), title


def manual_focus_countdown(seconds=5):
    for remaining in range(seconds, 0, -1):
        print(f"[MANUAL] Click the NWN window now: {remaining}...")
        time.sleep(1)
    result = get_foreground_window_title()
    print(f"[MANUAL] Foreground: {result[1]!r}")
    return result


def _check_focus(process_id, target):
    active_id, active_title = get_foreground_window_title()
    if active_id != process_id or target.casefold() not in (active_title or "").casefold():
        raise RuntimeError(
            "NWN lost focus; input stopped. Check the game chat field before retrying."
        )


def send_chat_to_nwn(text, settings, leave_unsent=False, force_method=None):
    text = " ".join(str(text).split())
    text = normalize_game_punctuation(text)
    text = text[: int(settings.get("max_reply_characters", 430))].strip()
    if not text:
        return False
    target = str(settings.get("window_title_contains", "Neverwinter Nights")).strip()
    if not target:
        print("[SEND] Set a nonempty NWN window title in settings.")
        return False
    with _send_lock:
        try:
            require_desktop()
            # Confirm clipboard access before opening the game's chat field.
            copy_draft(text)
            if settings.get("focus_game_before_typing", True):
                ok, _ = focus_nwn_window(target)
                if not ok:
                    raise RuntimeError("Could not focus NWN. Click the game and use Keyboard Test.")
            process_id, title = get_foreground_window_title()
            if not process_id or target.casefold() not in (title or "").casefold():
                raise RuntimeError("NWN is not the foreground window.")
            time.sleep(float(settings.get("focus_delay_seconds", 0.60)))
            _check_focus(process_id, target)
            _osascript(_RETURN_SCRIPT)
            time.sleep(float(settings.get("chat_open_delay_seconds", 0.45)))
            _check_focus(process_id, target)
            _osascript(_PASTE_SCRIPT)
            time.sleep(float(settings.get("before_send_delay_seconds", 0.35)))
            if leave_unsent:
                print(
                    "[DRAFT] Paste requested. Review the NWN chat field and press Enter or Escape."
                )
                return True
            _check_focus(process_id, target)
            _osascript(_RETURN_SCRIPT)
            print("[SEND] Chat input delivered to NWN. Verify receipt in the game log.")
            return True
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f"[SEND ERROR] {exc}")
            return False
