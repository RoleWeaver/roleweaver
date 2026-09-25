"""macOS desktop adapter. Game input is an explicit clipboard handoff."""

import os
import re
import subprocess
import sys
from pathlib import Path

from roleweaver.game_text import normalize_game_punctuation


def is_wayland():
    """Compatibility flag for the client's manual-input mode."""
    return True


def require_desktop():
    if sys.platform != "darwin":
        raise RuntimeError("The macOS client requires macOS.")


def nwn_log_directories():
    home = Path.home()
    paths = []
    if os.environ.get("NWN_USER_DIRECTORY"):
        paths.append(Path(os.environ["NWN_USER_DIRECTORY"]).expanduser() / "logs")
    paths.extend([
        home / "Documents/Neverwinter Nights/logs",
        home / "Library/Application Support/Neverwinter Nights/logs",
    ])
    return list(dict.fromkeys(paths))


def migrate_default_log_paths(settings):
    default = str(nwn_log_directories()[0] / "nwclientLog1.txt")

    def local_path(raw):
        if not raw or Path(raw).expanduser().is_file():
            return raw
        normalized = str(raw).replace("\\", "/").lower()
        known_default = re.match(
            r"^(?:[a-z]:/users/[^/]+/documents|/home/[^/]+/(?:\.local/share|documents)|/users/[^/]+/documents)/neverwinter nights/logs/nwclientlog1\.txt$",
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
        ["pbcopy"], input=normalized, text=True, encoding="utf-8",
        check=True, timeout=5,
    )
    print("[DRAFT] Copied to clipboard. Open NWN chat, press Command+V, review, then Enter.")


def get_foreground_window_title():
    return None, None


def find_window_handle(title_contains):
    return None, None


def focus_nwn_window(title_contains):
    return False, None


def manual_focus_countdown(seconds=5):
    return None, None


def send_chat_to_nwn(text, settings, leave_unsent=False, force_method=None):
    text = " ".join(str(text).split())
    text = text[: int(settings.get("max_reply_characters", 430))].strip()
    if not text:
        return False
    try:
        copy_draft(text)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[CLIPBOARD ERROR] {exc}")
    # A clipboard copy is never evidence that the player sent the line.
    return False
