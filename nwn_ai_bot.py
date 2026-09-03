import os
import re
import sys
import time
import json
import queue
import getpass
import threading
import ctypes
from ctypes import wintypes
from collections import deque
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

import pyautogui
import pyperclip
from pynput import keyboard
from openai import OpenAI

try:
    from google import genai
except Exception:
    genai = None


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
SETTINGS_PATH = APP_DIR / "settings.json"
CHARACTER_PROMPT_PATH = APP_DIR / "character_prompt.txt"

COLOR_TAG_RE = re.compile(r"</?c[^>]*>", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Matches examples such as:
# [fMlNM2u] Lora Thendry: [Talk] <c   >"Hello."</c>
# [rHfBdZh] <c...>Bookish Rascal</c>: [Talk] <c...>"Hello."</c>
# Scrivener of the Vaunted Word: [Talk] "We live and learn."
STRUCTURED_CHAT_RE = re.compile(
    r"^(?:\[(?P<speaker_id>[^\]]+)\]\s+)?"
    r"(?P<speaker>.*?):\s*"
    r"\[(?P<channel>Talk|Whisper|Party|Tell|Shout|DM)\]\s*"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)

TDN_AREA_RE = re.compile(r"\*Now Entering (?P<area>.+?)\*\s*$")
RAVENLOFT_AREA_RE = re.compile(
    r"<<\s*You have entered the area:\s*(?P<area>.+?)\.?\s*>>",
    re.IGNORECASE,
)

DEFAULT_NWN_LOG_PATH = str(
    Path.home() / "Documents" / "Neverwinter Nights" / "logs" / "nwclientLog1.txt"
)

SERVER_PROFILES = {
    "CUSTOM": {"display_name": "Custom / Other NWN Server", "default_log_path": DEFAULT_NWN_LOG_PATH},
    "TDN": {"display_name": "The Dragon's Neck (TDN)", "default_log_path": DEFAULT_NWN_LOG_PATH},
    "Arelith": {"display_name": "Arelith", "default_log_path": DEFAULT_NWN_LOG_PATH},
    "RAVENLOFT_POTM": {"display_name": "Ravenloft: Prisoners of the Mist", "default_log_path": DEFAULT_NWN_LOG_PATH},
    "CORMYR_DALELANDS": {"display_name": "Cormyr and the Dalelands", "default_log_path": DEFAULT_NWN_LOG_PATH},
    "STAR_WARS_LOR": {"display_name": "Star Wars: Legends of the Old Republic", "default_log_path": DEFAULT_NWN_LOG_PATH},
    "HAZE_SALTBORNE": {"display_name": "Haze: Saltborne", "default_log_path": DEFAULT_NWN_LOG_PATH},
}

DEFAULT_SETTINGS = {
    "server_profile": "CUSTOM",
    "server_log_paths": {
        "CUSTOM": SERVER_PROFILES["CUSTOM"]["default_log_path"],
        "TDN": SERVER_PROFILES["TDN"]["default_log_path"],
        "Arelith": SERVER_PROFILES["Arelith"]["default_log_path"],
        "RAVENLOFT_POTM": SERVER_PROFILES["RAVENLOFT_POTM"]["default_log_path"],
        "CORMYR_DALELANDS": SERVER_PROFILES["CORMYR_DALELANDS"]["default_log_path"],
        "STAR_WARS_LOR": SERVER_PROFILES["STAR_WARS_LOR"]["default_log_path"],
        "HAZE_SALTBORNE": SERVER_PROFILES["HAZE_SALTBORNE"]["default_log_path"],
    },
    "log_path": DEFAULT_NWN_LOG_PATH,
    "character_name": "Example NPC",
    "ai_provider": "Google Gemini",
    "model": "gemini-3.7-flash",
    "lm_studio_base_url": "http://127.0.0.1:1234",
    "window_title_contains": "Neverwinter Nights",
    "poll_interval_seconds": 0.10,
    "context_messages": 30,
    "max_reply_characters": 430,
    "auto_reply_delay_seconds": 2.5,
    "auto_reply_cooldown_seconds": 8.0,
    "auto_reply_channels": ["Talk", "Whisper"],
    "start_paused": False,
    "auto_reply_on_start": False,
    "focus_game_before_typing": True,
    "keyboard_method": "scancode",
    "focus_delay_seconds": 0.60,
    "chat_open_delay_seconds": 0.45,
    "before_send_delay_seconds": 0.35,
    "memory_enabled": True,
    "summary_interval_messages": 18,
    "memory_max_characters_per_person": 1600,
    "tell_context_messages": 20,
    "generation_timing": True,
    "ignore_ooc_for_ai": True,
    "response_length_mode": "Auto",
    "candidate_count": 3,
}


def load_settings():
    if not SETTINGS_PATH.exists():
        SETTINGS_PATH.write_text(
            json.dumps(DEFAULT_SETTINGS, indent=2),
            encoding="utf-8",
        )
    data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_SETTINGS)
    merged.update(data)
    paths = dict(DEFAULT_SETTINGS["server_log_paths"])
    paths.update(data.get("server_log_paths", {}))
    if "server_log_paths" not in data and data.get("log_path"):
        paths["TDN"] = data["log_path"]
    merged["server_log_paths"] = paths
    if merged.get("server_profile") not in SERVER_PROFILES:
        merged["server_profile"] = "CUSTOM"
    merged["log_path"] = paths.get(
        merged["server_profile"],
        SERVER_PROFILES[merged["server_profile"]]["default_log_path"],
    )
    return merged


def save_settings(settings):
    SETTINGS_PATH.write_text(json.dumps(dict(settings), indent=2), encoding="utf-8")


def get_server_log_path(settings, server_profile=None):
    profile = server_profile or settings.get("server_profile", "CUSTOM")
    paths = settings.get("server_log_paths", {})
    return paths.get(profile) or SERVER_PROFILES.get(profile, SERVER_PROFILES["CUSTOM"])["default_log_path"]


def load_character_prompt():
    if not CHARACTER_PROMPT_PATH.exists():
        CHARACTER_PROMPT_PATH.write_text(
            "You are roleplaying a character in Neverwinter Nights.\n"
            "Stay in character and write only what the character says or emotes.\n",
            encoding="utf-8",
        )
    return CHARACTER_PROMPT_PATH.read_text(encoding="utf-8").strip()


ROLEPLAY_RULES_DIR = APP_DIR / "RoleplayRules"


def roleplay_rules_dir(server_profile="CUSTOM"):
    profile = server_profile if server_profile in SERVER_PROFILES else "CUSTOM"
    path = ROLEPLAY_RULES_DIR / profile
    path.mkdir(parents=True, exist_ok=True)
    return path


def roleplay_rules_path(server_profile="CUSTOM"):
    return roleplay_rules_dir(server_profile) / "roleplay_rules.txt"


def load_server_roleplay_rules(server_profile="CUSTOM"):
    path = roleplay_rules_path(server_profile)
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def clean_nwn_text(text):
    text = COLOR_TAG_RE.sub("", text)
    text = CONTROL_RE.sub("", text)
    return text.strip()


def _parse_standard_structured_chat(raw, character_name, server_profile):
    """Parse the structured copy of an NWN chat message."""
    m = STRUCTURED_CHAT_RE.match(raw)
    if not m:
        return None
    speaker = clean_nwn_text(m.group("speaker"))
    message = clean_nwn_text(m.group("message"))
    channel = m.group("channel").title()
    speaker_id = clean_nwn_text((m.group("speaker_id") or "").strip())
    if not speaker or not message:
        return None
    if message.startswith("[") and message.endswith("]"):
        return None
    return {
        "speaker_id": speaker_id,
        "speaker": speaker,
        "channel": channel,
        "message": message,
        "self": speaker.casefold() == character_name.casefold(),
        "server_profile": server_profile,
    }


def _parse_custom_chat(raw, character_name, server_profile):
    return _parse_standard_structured_chat(raw, character_name, server_profile)


def _parse_tdn_chat(raw, character_name, server_profile):
    return _parse_standard_structured_chat(raw, character_name, server_profile)


def _parse_arelith_chat(raw, character_name, server_profile):
    event = _parse_standard_structured_chat(raw, character_name, server_profile)
    if event and event["speaker"].casefold() == "public message board":
        return None
    return event


def _parse_ravenloft_potm_chat(raw, character_name, server_profile):
    return _parse_standard_structured_chat(raw, character_name, server_profile)


def _parse_cormyr_dalelands_chat(raw, character_name, server_profile):
    return _parse_standard_structured_chat(raw, character_name, server_profile)


def _parse_star_wars_lor_chat(raw, character_name, server_profile):
    return _parse_standard_structured_chat(raw, character_name, server_profile)


def _parse_haze_saltborne_chat(raw, character_name, server_profile):
    return _parse_standard_structured_chat(raw, character_name, server_profile)


SERVER_CHAT_PARSERS = {
    "CUSTOM": _parse_custom_chat,
    "TDN": _parse_tdn_chat,
    "Arelith": _parse_arelith_chat,
    "RAVENLOFT_POTM": _parse_ravenloft_potm_chat,
    "CORMYR_DALELANDS": _parse_cormyr_dalelands_chat,
    "STAR_WARS_LOR": _parse_star_wars_lor_chat,
    "HAZE_SALTBORNE": _parse_haze_saltborne_chat,
}


def parse_chat_line(line, character_name, server_profile="CUSTOM"):
    raw = line.strip()
    if not raw or raw.startswith("[CHAT WINDOW TEXT]"):
        return None
    parser = SERVER_CHAT_PARSERS.get(server_profile, SERVER_CHAT_PARSERS["CUSTOM"])
    return parser(raw, character_name, server_profile)



class LogFollower:
    """Follow a file that NWN may truncate or replace while running."""

    def __init__(self, path, poll_interval=0.1):
        self.path = Path(path)
        self.poll_interval = poll_interval
        self.file = None
        self.identity = None
        self.position = 0

    @staticmethod
    def _identity_from_stat(st):
        # st_ino is usable on modern Windows Python. Size/mtime are fallback hints.
        return (getattr(st, "st_ino", None), getattr(st, "st_dev", None))

    def _close(self):
        if self.file:
            try:
                self.file.close()
            except Exception:
                pass
        self.file = None
        self.identity = None
        self.position = 0

    def _open_at_end(self):
        self.file = open(self.path, "r", encoding="utf-8", errors="replace")
        st = os.fstat(self.file.fileno())
        self.identity = self._identity_from_stat(st)
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()

    def _open_at_start(self):
        self.file = open(self.path, "r", encoding="utf-8", errors="replace")
        st = os.fstat(self.file.fileno())
        self.identity = self._identity_from_stat(st)
        self.file.seek(0)
        self.position = 0

    def lines(self, stop_event):
        first_open = True

        while not stop_event.is_set():
            try:
                if self.file is None:
                    if not self.path.exists():
                        time.sleep(0.5)
                        continue

                    # On initial launch, ignore old contents. If NWN later truncates
                    # or replaces the file, we reopen from the beginning.
                    if first_open:
                        self._open_at_end()
                        first_open = False
                    else:
                        self._open_at_start()

                line = self.file.readline()
                if line:
                    self.position = self.file.tell()
                    yield line.rstrip("\r\n")
                    continue

                # No new data. Check whether the path now refers to a new file,
                # or whether NWN truncated the current one.
                try:
                    path_stat = self.path.stat()
                    handle_stat = os.fstat(self.file.fileno())

                    path_identity = self._identity_from_stat(path_stat)
                    handle_identity = self._identity_from_stat(handle_stat)

                    replaced = (
                        path_identity != (None, None)
                        and handle_identity != (None, None)
                        and path_identity != handle_identity
                    )
                    truncated = path_stat.st_size < self.position

                    if replaced or truncated:
                        self._close()
                        continue
                except FileNotFoundError:
                    self._close()
                    continue

                time.sleep(self.poll_interval)

            except (PermissionError, OSError) as exc:
                print(f"[LOG] Waiting for readable log file: {exc}")
                self._close()
                time.sleep(0.5)

        self._close()



# Windows SendInput definitions.
#
# IMPORTANT: INPUT is a union whose largest member is MOUSEINPUT. On 64-bit
# Windows, omitting that member makes ctypes.sizeof(INPUT) too small, and
# SendInput returns 0 with ERROR_INVALID_PARAMETER / "[WinError 0] The
# parameter is incorrect." These definitions mirror WinUser.h closely enough
# for both 32-bit and 64-bit Python.
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

VK_RETURN = 0x0D

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_SendInput = _user32.SendInput
_SendInput.argtypes = (
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.c_int,
)
_SendInput.restype = wintypes.UINT


def _send_key_event(vk, flags=0, scan=0):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.ki = KEYBDINPUT(
        wVk=vk,
        wScan=scan,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )

    ctypes.set_last_error(0)
    sent = _SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    if sent != 1:
        err = ctypes.get_last_error()
        # get_last_error() can still be 0 on some ctypes/user32 combinations;
        # include the INPUT size because that is the most common cause.
        raise OSError(
            err,
            f"SendInput failed (INPUT size={ctypes.sizeof(INPUT)} bytes, "
            f"Python={ctypes.sizeof(ctypes.c_void_p) * 8}-bit)"
        )


def press_windows_key(vk):
    _send_key_event(vk)
    time.sleep(0.05)
    _send_key_event(vk, KEYEVENTF_KEYUP)



# PC/AT set-1 scan codes used by many games through DirectInput/SDL.
SC_ENTER = 0x1C
SC_LCTRL = 0x1D
SC_V = 0x2F


def _send_scancode(scan, keyup=False):
    flags = KEYEVENTF_SCANCODE
    if keyup:
        flags |= KEYEVENTF_KEYUP
    _send_key_event(0, flags, scan)


def press_scancode(scan):
    _send_scancode(scan, False)
    time.sleep(0.05)
    _send_scancode(scan, True)


def press_ctrl_v_scancode():
    _send_scancode(SC_LCTRL, False)
    time.sleep(0.03)
    _send_scancode(SC_V, False)
    time.sleep(0.03)
    _send_scancode(SC_V, True)
    time.sleep(0.03)
    _send_scancode(SC_LCTRL, True)


def manual_focus_countdown(seconds=5):
    print()
    print(f"[MANUAL] Click the NWN game window now. Test begins in {seconds} seconds.")
    for i in range(seconds, 0, -1):
        print(f"[MANUAL] {i}...")
        time.sleep(1)
    hwnd, title = get_foreground_window_title()
    print(f"[MANUAL] Foreground at injection time: '{title}'")
    return hwnd, title


def type_unicode_sendinput(text):
    # Type Unicode through KEYEVENTF_UNICODE. If NWN does not accept Unicode
    # events reliably, the fallback clipboard method below can be enabled in
    # settings.json with "input_method": "clipboard".
    for ch in text:
        encoded = ch.encode("utf-16-le")
        units = [
            int.from_bytes(encoded[i:i+2], "little")
            for i in range(0, len(encoded), 2)
        ]

        for unit in units:
            _send_key_event(0, KEYEVENTF_UNICODE, unit)
            _send_key_event(0, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, unit)


def paste_with_hotkeys(text):
    old_clipboard = None
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        pass

    pyperclip.copy(text)
    time.sleep(0.10)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.10)

    if old_clipboard is not None:
        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass


def find_window_handle(title_contains):
    user32 = ctypes.windll.user32
    matches = []
    target = title_contains.casefold()

    EnumWindowsProc = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )

    @EnumWindowsProc
    def enum_proc(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        if target in title.casefold():
            matches.append((hwnd, title))
        return True

    user32.EnumWindows(enum_proc, 0)
    return matches[0] if matches else (None, None)



def get_foreground_window_title():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return hwnd, buf.value


def press_enter_keybd_event():
    # Older Win32 keyboard API. Kept as a fallback because some games respond
    # differently to it than to SendInput.
    KEYEVENTF_KEYUP_OLD = 0x0002
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP_OLD, 0)


def press_ctrl_v_sendinput():
    VK_CONTROL = 0x11
    VK_V = 0x56
    _send_key_event(VK_CONTROL)
    time.sleep(0.03)
    _send_key_event(VK_V)
    time.sleep(0.03)
    _send_key_event(VK_V, KEYEVENTF_KEYUP)
    time.sleep(0.03)
    _send_key_event(VK_CONTROL, KEYEVENTF_KEYUP)


def press_ctrl_v_keybd_event():
    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP_OLD = 0x0002
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.03)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP_OLD, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP_OLD, 0)


def press_enter_postmessage(hwnd):
    # Useful as a diagnostic fallback. Some games ignore window messages and
    # only accept real/input-queue keyboard events, so failure here is not
    # surprising.
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    user32 = ctypes.windll.user32
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0)


def focus_nwn_window(title_contains):
    # If the user already clicked NWN, do not call SetForegroundWindow again.
    # Windows can reject SetForegroundWindow from a background worker thread
    # even though the game is already correctly focused.
    fg_hwnd, fg_title = get_foreground_window_title()
    target = (title_contains or "").casefold()
    if fg_hwnd and fg_title and target in fg_title.casefold():
        return True, fg_title

    hwnd, title = find_window_handle(title_contains)
    if not hwnd:
        return False, None

    user32 = ctypes.windll.user32
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.20)

    # Verify the result instead of trusting SetForegroundWindow's return value.
    fg_hwnd, fg_title = get_foreground_window_title()
    ok = bool(fg_hwnd and fg_title and target in fg_title.casefold())
    return ok, title


def send_chat_to_nwn(text, settings, leave_unsent=False, force_method=None):
    text = " ".join(text.replace("\r", " ").replace("\n", " ").split())

    # Normalize common Unicode punctuation so NWN chat receives plain ASCII
    # characters instead of smart punctuation that can display as '?'.
    text = (
        text
        .replace("\u2018", "'")   # left single quotation mark
        .replace("\u2019", "'")   # right single quotation mark / apostrophe
        .replace("\u201c", '"')   # left double quotation mark
        .replace("\u201d", '"')   # right double quotation mark
        .replace("\u2013", "-")   # en dash
        .replace("\u2014", "-")   # em dash
        .replace("\u2026", "...") # ellipsis
        .replace("\u00a0", " ")   # non-breaking space
    )
    text = text[: int(settings["max_reply_characters"])].strip()
    if not text:
        return False

    hwnd = None
    title = None

    target_title = settings.get("window_title_contains", "Neverwinter Nights")

    if settings.get("focus_game_before_typing", True):
        ok, title = focus_nwn_window(target_title)
        hwnd, fg_title = get_foreground_window_title()

        print(f"[FOCUS] selected='{title}'")
        print(f"[FOCUS] foreground='{fg_title}'")

        if not ok:
            print("[SEND] Could not put NWN in the foreground.")
            print("[SEND] Click the NWN window during the countdown and try again.")
            return False

        if not fg_title or target_title.casefold() not in fg_title.casefold():
            print("[SEND] NWN is not actually the foreground window.")
            print("[SEND] Click NWN manually, then retry.")
            return False
    else:
        hwnd, fg_title = get_foreground_window_title()
        print(f"[FOCUS] manual foreground='{fg_title}'")
        if not fg_title or target_title.casefold() not in fg_title.casefold():
            print("[SEND] Manual-focus mode expected NWN to be the foreground window.")
            print("[SEND] Click NWN during the countdown and retry.")
            return False

    time.sleep(float(settings.get("focus_delay_seconds", 0.75)))

    method = (force_method or settings.get("keyboard_method", "sendinput")).lower().strip()

    try:
        print(f"[SEND] Keyboard method: {method}")
        print(
            f"[SEND] INPUT size={ctypes.sizeof(INPUT)} bytes; "
            f"Python={ctypes.sizeof(ctypes.c_void_p) * 8}-bit"
        )

        if method == "scancode":
            press_enter = lambda: press_scancode(SC_ENTER)
            press_paste = press_ctrl_v_scancode
        elif method == "keybd_event":
            press_enter = press_enter_keybd_event
            press_paste = press_ctrl_v_keybd_event
        elif method == "postmessage":
            def press_enter():
                if not hwnd:
                    raise RuntimeError("No NWN hwnd available for PostMessage.")
                press_enter_postmessage(hwnd)
            # PostMessage is only used for Enter; clipboard paste still uses native keybd_event.
            press_paste = press_ctrl_v_keybd_event
        else:
            # Default: our own ctypes SendInput wrapper, no pynput/pyautogui dependency.
            press_enter = lambda: press_windows_key(VK_RETURN)
            press_paste = press_ctrl_v_sendinput

        print("[SEND] Opening NWN chat...")
        press_enter()
        time.sleep(float(settings.get("chat_open_delay_seconds", 0.65)))

        print("[SEND] Copying response to clipboard...")
        old_clipboard = None
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(0.10)

        print("[SEND] Pasting response...")
        press_paste()
        time.sleep(float(settings.get("before_send_delay_seconds", 0.50)))

        if leave_unsent:
            # Keep the generated response on the clipboard. If NWN rejects the
            # injected Ctrl+V for any reason, the user can still press Ctrl+V
            # manually without losing the draft.
            print("[DRAFT] Draft remains on the Windows clipboard as a fallback.")
            print("[TEST] Text should now be visible in NWN's chat entry field.")
            print("[TEST] It was intentionally NOT sent.")
            return True

        if old_clipboard is not None:
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass

        print("[SEND] Sending chat...")
        press_enter()
        return True

    except Exception as exc:
        print(f"[SEND ERROR] {type(exc).__name__}: {exc}")
        return False



GUIDANCE_FILE = APP_DIR / "next_guidance.txt"


def read_shared_guidance():
    """Read one-shot guidance entered in the Guidance window or console."""
    try:
        if GUIDANCE_FILE.exists():
            return GUIDANCE_FILE.read_text(encoding="utf-8").strip()
    except Exception as exc:
        print(f"[GUIDE] Could not read guidance file: {exc}")
    return ""


def write_shared_guidance(text):
    """Store one-shot guidance so both the GUI and bot console see the same value."""
    try:
        GUIDANCE_FILE.write_text((text or "").strip(), encoding="utf-8")
        return True
    except Exception as exc:
        print(f"[GUIDE] Could not write guidance file: {exc}")
        return False


def clear_shared_guidance():
    return write_shared_guidance("")



CHARACTER_PROFILE_PATTERN = "character_*.txt"
CHARACTERS_DIR = APP_DIR / "Characters"


def character_profile_dir(server_profile="TDN"):
    profile = server_profile if server_profile in SERVER_PROFILES else "CUSTOM"
    path = CHARACTERS_DIR / profile
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_character_profiles(server_profile="TDN"):
    """Return character prompts belonging to one server only."""
    base = character_profile_dir(server_profile)
    return sorted(
        [p for p in base.glob(CHARACTER_PROFILE_PATTERN) if p.is_file()],
        key=lambda p: p.name.casefold(),
    )


def resolve_character_profile(server_profile, filename):
    return character_profile_dir(server_profile) / Path(filename).name


def extract_character_name_from_prompt(text, fallback=""):
    patterns = [
        r"(?im)^\s*character\s+name\s*:\s*(.+?)\s*$",
        r"(?im)^\s*name\s*:\s*(.+?)\s*$",
    ]
    for pattern in patterns:
        m = re.search(pattern, text or "")
        if m:
            name = clean_nwn_text(m.group(1)).strip()
            if name:
                return name
    return (fallback or "").strip()


def load_character_profile(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    fallback = path.stem
    if fallback.lower().startswith("character_"):
        fallback = fallback[len("character_"):]
    fallback = fallback.replace("_", " ").strip()
    name = extract_character_name_from_prompt(text, fallback=fallback)
    return text, name


def character_ai_settings_path(profile_path):
    profile_path = Path(profile_path)
    return profile_path.with_suffix(".settings.json")


def load_character_ai_settings(profile_path):
    path = character_ai_settings_path(profile_path)
    defaults = {
        "ai_provider": "Google Gemini",
        "model": AI_PROVIDERS["Google Gemini"]["default_model"] if "AI_PROVIDERS" in globals() else "gemini-3.7-flash",
        "lm_studio_base_url": "http://127.0.0.1:1234/v1",
        "response_length_mode": "Auto",
        "candidate_count": 3,
    }
    if not path.exists():
        return defaults
    try:
        loaded=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict): defaults.update(loaded)
    except Exception:
        pass
    return defaults


def save_character_ai_settings(profile_path, settings):
    path=character_ai_settings_path(profile_path)
    data={
        "ai_provider": settings.get("ai_provider", "Google Gemini"),
        "model": settings.get("model", ""),
        "lm_studio_base_url": settings.get("lm_studio_base_url", "http://127.0.0.1:1234/v1"),
        "response_length_mode": settings.get("response_length_mode", "Auto"),
        "candidate_count": int(settings.get("candidate_count", 3)),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")



AI_PROVIDERS = {
    "LM Studio": {
        "requires_key": False,
        "default_model": "auto",
        "default_base_url": "http://127.0.0.1:1234",
        "env_key": "",
    },
    "OpenAI": {
        "requires_key": True,
        "default_model": "gpt-5.6-luna",
        "default_base_url": "",
        "env_key": "OPENAI_API_KEY",
    },
    "Google Gemini": {
        "requires_key": True,
        "default_model": "gemini-3.7-flash",
        "default_base_url": "",
        "env_key": "GEMINI_API_KEY",
    },
}



def normalize_lm_studio_base_url(url):
    """Accept either http://127.0.0.1:1234 or .../v1 for LM Studio."""
    url = (url or "http://127.0.0.1:1234").strip().rstrip("/")
    if not url.lower().endswith("/v1"):
        url += "/v1"
    return url


class OpenAICompatibleProvider:
    def __init__(self, model, api_key, base_url=None, auto_model=False, use_chat_completions=False):
        kwargs = {"api_key": api_key or "lm-studio"}
        if base_url:
            kwargs["base_url"] = base_url

        self.client = OpenAI(**kwargs)
        self.model = (model or "").strip()
        self.use_chat_completions = bool(use_chat_completions)

        if auto_model or not self.model or self.model.casefold() == "auto":
            models = self._list_model_ids()
            if not models:
                raise RuntimeError(
                    "Connected to the AI server, but no loaded models were reported. "
                    "In LM Studio, load a model and make sure the Local Server is running."
                )
            self.model = models[0]

    def _list_model_ids(self):
        response = self.client.models.list()
        data = getattr(response, "data", None)

        if data is None:
            try:
                data = list(response)
            except (TypeError, AttributeError):
                data = []

        model_ids = []
        for item in data or []:
            model_id = getattr(item, "id", None)
            if model_id:
                model_ids.append(str(model_id))
        return model_ids

    def generate(self, instructions, prompt):
        if self.use_chat_completions:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": prompt},
                ],
            )
            choices = getattr(response, "choices", None) or []
            if not choices:
                return ""
            message = getattr(choices[0], "message", None)
            return (getattr(message, "content", "") or "").strip()

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )
        return (response.output_text or "").strip()

    def test(self):
        models = self._list_model_ids()
        if models:
            return f"Connected. {len(models)} model(s) available. Using {self.model}."

        if self.model and self.model.casefold() != "auto" and self.use_chat_completions:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=8,
            )
            choices = getattr(response, "choices", None) or []
            if choices:
                return f"Connected. Using {self.model}."

        raise RuntimeError(
            "The server responded, but no models were available. "
            "Load a model in LM Studio and start the Local Server."
        )


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio provider with native REST model discovery/loading."""

    def __init__(self, model, base_url):
        self.server_root = (base_url or "http://127.0.0.1:1234").strip().rstrip("/")
        if self.server_root.lower().endswith("/v1"):
            self.server_root = self.server_root[:-3].rstrip("/")

        requested_model = (model or "auto").strip()

        # Discover downloaded models and ensure one is actually loaded.
        selected_model = self._prepare_model(requested_model)

        super().__init__(
            model=selected_model,
            api_key="lm-studio",
            base_url=normalize_lm_studio_base_url(self.server_root),
            auto_model=False,
            use_chat_completions=True,
        )

    def _native_request(self, method, path, body=None, timeout=120):
        url = self.server_root + path
        data = None
        headers = {"Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LM Studio API returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not connect to LM Studio at {self.server_root}. "
                "Make sure the Local Server is running."
            ) from exc

    def _prepare_model(self, requested_model):
        try:
            payload = self._native_request("GET", "/api/v1/models", timeout=15)
            models = payload.get("models") or []
        except Exception:
            # Older LM Studio versions may not support the native v1 endpoint.
            # Fall back to the OpenAI model list, but require manual loading.
            temp = OpenAI(
                api_key="lm-studio",
                base_url=normalize_lm_studio_base_url(self.server_root),
            )
            response = temp.models.list()
            data = getattr(response, "data", None) or []
            ids = [str(getattr(item, "id", "")) for item in data if getattr(item, "id", None)]
            if requested_model.casefold() == "auto":
                if not ids:
                    raise RuntimeError(
                        "No LM Studio models are available. Download and load a model in LM Studio first."
                    )
                return ids[0]
            return requested_model

        llms = [m for m in models if (m.get("type") or "").casefold() == "llm"]
        if not llms:
            raise RuntimeError(
                "LM Studio is running, but no downloaded LLMs were found. "
                "Download a chat/instruct model in LM Studio first."
            )

        selected = None
        if requested_model.casefold() == "auto":
            # Prefer an already-loaded model, otherwise use the first local LLM.
            selected = next((m for m in llms if m.get("loaded_instances")), llms[0])
        else:
            wanted = requested_model.casefold()
            for m in llms:
                candidates = {
                    str(m.get("key") or "").casefold(),
                    str(m.get("display_name") or "").casefold(),
                    str(m.get("name") or "").casefold(),
                }
                if wanted in candidates:
                    selected = m
                    break
            if selected is None:
                # It may be a valid identifier exposed only by compatibility mode.
                return requested_model

        model_key = str(selected.get("key") or selected.get("name") or "").strip()
        if not model_key:
            raise RuntimeError("LM Studio returned a model without a usable model identifier.")

        loaded_instances = selected.get("loaded_instances") or []
        if not loaded_instances:
            print(f"[LM STUDIO] Loading model: {model_key} ...")
            result = self._native_request(
                "POST",
                "/api/v1/models/load",
                body={"model": model_key},
                timeout=180,
            )
            if (result.get("status") or "").casefold() != "loaded":
                raise RuntimeError(
                    f"LM Studio did not confirm that model '{model_key}' was loaded."
                )
            print(f"[LM STUDIO] Model loaded: {model_key}")
        else:
            print(f"[LM STUDIO] Model already loaded: {model_key}")

        return model_key

    def test(self):
        # A real tiny inference test catches the difference between a model
        # merely being listed/downloaded and actually being usable.
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=8,
        )
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise RuntimeError("LM Studio connected, but the model returned no test response.")
        return f"Connected. Model loaded and responding: {self.model}."


class GeminiProvider:
    # Current text-oriented Flash / Flash-Lite models. Availability and free-tier
    # quotas are determined by the user's Google AI project, so unavailable
    # models are skipped automatically.
    FALLBACK_MODELS = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]

    def __init__(self, model, api_key):
        if genai is None:
            raise RuntimeError(
                "Google Gemini support is not installed. "
                "Run the launcher again to install dependencies."
            )
        if not api_key:
            raise RuntimeError("A Google Gemini API key is required.")

        self.client = genai.Client(api_key=api_key)
        self.model = (model or "gemini-3.7-flash").strip()
        self.last_successful_model = None

    def _candidate_models(self):
        requested = self.model.strip()

        if requested.casefold() in ("auto", "auto-free", "free-auto"):
            ordered = list(self.FALLBACK_MODELS)
        else:
            ordered = [requested] + self.FALLBACK_MODELS

        seen = set()
        result = []
        for name in ordered:
            key = name.casefold()
            if name and key not in seen:
                seen.add(key)
                result.append(name)

        # Prefer the model that most recently succeeded during this session.
        if self.last_successful_model in result:
            result.remove(self.last_successful_model)
            result.insert(0, self.last_successful_model)

        return result

    @staticmethod
    def _error_code(exc):
        for attr in ("status_code", "code"):
            value = getattr(exc, attr, None)
            try:
                if callable(value):
                    value = value()
            except Exception:
                value = None

            if isinstance(value, int):
                return value

            if value is not None:
                text = str(value)
                m = re.search(r"\b(400|403|404|408|409|429|500|502|503|504)\b", text)
                if m:
                    return int(m.group(1))

        text = str(exc)
        m = re.search(r"\b(400|403|404|408|409|429|500|502|503|504)\b", text)
        return int(m.group(1)) if m else None

    @classmethod
    def _should_try_another_model(cls, exc):
        code = cls._error_code(exc)
        text = str(exc).casefold()

        # Capacity/rate-limit errors are the main reason for fallback.
        if code in (408, 429, 500, 502, 503, 504):
            return True

        capacity_terms = (
            "resource_exhausted",
            "resource exhausted",
            "unavailable",
            "overloaded",
            "busy",
            "capacity",
            "rate limit",
            "rate_limit",
            "too many requests",
            "temporarily unavailable",
        )
        if any(term in text for term in capacity_terms):
            return True

        # A particular model may not be available to the user's project/free tier.
        model_access_terms = (
            "model not found",
            "not found for api version",
            "not supported for generatecontent",
            "does not have access",
            "permission denied",
            "not available for",
        )
        if code in (400, 403, 404) and any(term in text for term in model_access_terms):
            return True

        return False

    def _generate_with_fallback(self, contents):
        candidates = self._candidate_models()
        failures = []

        for index, model_name in enumerate(candidates):
            try:
                if len(candidates) > 1:
                    print(f"[GEMINI] Trying {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                )
                text = (getattr(response, "text", "") or "").strip()

                self.last_successful_model = model_name
                self.model = model_name

                if index > 0:
                    print(f"[GEMINI] Switched to available model: {model_name}")
                return text

            except Exception as exc:
                failures.append(f"{model_name}: {exc}")

                if not self._should_try_another_model(exc):
                    raise

                if index < len(candidates) - 1:
                    print(
                        f"[GEMINI] {model_name} unavailable/busy. "
                        "Trying another Gemini model..."
                    )

        detail = "\n".join(failures[-3:])
        raise RuntimeError(
            "No Gemini fallback model was available for this request. "
            "The project may be rate-limited, all candidate models may be busy, "
            "or the free-tier quota may be exhausted.\n" + detail
        )

    def generate(self, instructions, prompt):
        contents = instructions + "\n\n" + prompt
        return self._generate_with_fallback(contents)

    def test(self):
        text = self._generate_with_fallback("Reply with exactly: OK")
        if not text:
            raise RuntimeError("Gemini connected, but returned no text.")
        return f"Connected to Gemini. Working model: {self.model}."


def create_ai_provider(settings, api_key=""):
    provider = settings.get("ai_provider", "OpenAI")
    model = settings.get("model", "").strip()

    if provider == "LM Studio":
        base_url = settings.get("lm_studio_base_url", "http://127.0.0.1:1234")
        settings["lm_studio_base_url"] = normalize_lm_studio_base_url(base_url)
        return LMStudioProvider(
            model=model,
            base_url=base_url,
        )
    if provider == "Google Gemini":
        return GeminiProvider(model=model, api_key=api_key)
    if provider == "OpenAI":
        return OpenAICompatibleProvider(model=model, api_key=api_key)
    raise RuntimeError(f"Unknown AI provider: {provider}")



ROLEWEAVER_DATA_DIR = APP_DIR / "RoleWeaver_Data"


def _safe_filename(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(value or "").strip())
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "Unknown"


def _memory_paths(settings):
    server = _safe_filename(settings.get("server_profile", "TDN"))
    character = _safe_filename(settings.get("character_name", "Unknown"))
    base = ROLEWEAVER_DATA_DIR / server / character
    summaries = base / "session_summaries"
    return base, base / "character_memory.json", base / "running_summary.txt", summaries


def _history_dir(settings):
    base, _, _, _ = _memory_paths(settings)
    path = base / "conversation_history"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_history_files(settings):
    return sorted(_history_dir(settings).glob("*.txt"), key=lambda p: p.name, reverse=True)


def read_history_file(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def load_persistent_memory(settings):
    base, memory_path, summary_path, summaries = _memory_paths(settings)
    base.mkdir(parents=True, exist_ok=True)
    summaries.mkdir(parents=True, exist_ok=True)

    data = {
        "server": settings.get("server_profile", "TDN"),
        "player_character": settings.get("character_name", "Unknown"),
        "characters": {},
    }
    if memory_path.exists():
        try:
            loaded = json.loads(memory_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
                if not isinstance(data.get("characters"), dict):
                    data["characters"] = {}
        except Exception:
            pass

    summary = ""
    if summary_path.exists():
        try:
            summary = summary_path.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            pass

    return data, summary


def save_persistent_memory(settings, data, running_summary):
    base, memory_path, summary_path, summaries = _memory_paths(settings)
    base.mkdir(parents=True, exist_ok=True)
    summaries.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path.write_text((running_summary or "").strip(), encoding="utf-8")


def archive_session_summary(settings, summary):
    if not summary or not summary.strip():
        return
    _, _, _, summaries = _memory_paths(settings)
    summaries.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = summaries / f"{stamp}.txt"
    path.write_text(summary.strip(), encoding="utf-8")


def extract_json_object(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None



LORE_DIR = APP_DIR / "Lore"


def lore_dir(server_profile="CUSTOM"):
    """Return the lore folder belonging only to the selected server."""
    profile = server_profile if server_profile in SERVER_PROFILES else "CUSTOM"
    path = LORE_DIR / profile
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_lore_files(server_profile="CUSTOM"):
    return sorted(
        [p for p in lore_dir(server_profile).glob("*.txt") if p.is_file()],
        key=lambda p: p.name.casefold(),
    )


def resolve_lore_file(server_profile, filename):
    return lore_dir(server_profile) / Path(filename).name


def load_relevant_lore(context_text, server_profile="CUSTOM", max_files=3, max_characters=5000):
    """Return relevant lore from the currently selected server only."""
    try:
        files = list_lore_files(server_profile)
    except Exception:
        return []
    if not files:
        return []

    haystack = (context_text or "").casefold()
    words = set(re.findall(r"[a-zA-Z0-9_'’-]{4,}", haystack))
    ranked = []

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            continue
        if not text:
            continue

        stem_words = set(re.findall(r"[a-zA-Z0-9_'’-]{3,}", path.stem.casefold()))
        body_words = set(re.findall(r"[a-zA-Z0-9_'’-]{5,}", text.casefold()))
        score = 0

        # Files prefixed with always_ are always included, but only for this server.
        if path.stem.casefold().startswith("always_"):
            score += 1000

        score += 12 * len(stem_words & words)
        score += min(20, len(body_words & words))

        if score > 0:
            ranked.append((score, path.name, text))

    ranked.sort(key=lambda item: (-item[0], item[1].casefold()))

    result = []
    used = 0
    for score, name, text in ranked[:max_files]:
        remaining = max_characters - used
        if remaining <= 0:
            break
        excerpt = text[:remaining].strip()
        if excerpt:
            result.append((name, excerpt))
            used += len(excerpt)
    return result



OOC_PREFIX_RE = re.compile(
    r"^\s*(?:\(\(|//|ooc\s*:|out\s+of\s+character\s*:|afk\s*:)",
    re.IGNORECASE,
)

OOC_SUFFIX_RE = re.compile(r"\)\)\s*$")


def classify_ic_ooc(message):
    """Return 'OOC' for common explicit OOC conventions, otherwise 'IC'."""
    text = (message or "").strip()
    if not text:
        return "IC"
    if OOC_PREFIX_RE.search(text):
        return "OOC"
    if text.startswith("(") and text.endswith(")") and len(text) > 2:
        # A single parenthetical line is treated as OOC; ordinary emotes are
        # normally written with asterisks in NWN RP.
        return "OOC"
    if OOC_SUFFIX_RE.search(text) and text.startswith("(("):
        return "OOC"
    return "IC"


class NWNAIBot:
    def __init__(self, settings, character_prompt, client):
        self.settings = settings
        self.character_prompt = character_prompt
        self.client = client

        self.stop_event = threading.Event()
        self.paused = bool(settings.get("start_paused", False))
        self.auto_reply = bool(settings.get("auto_reply_on_start", False))

        self.context = deque(maxlen=int(settings["context_messages"]))
        self.current_area = ""
        self.last_external_event = None
        self.last_auto_reply_at = 0.0
        self.pending_auto_token = 0
        self.next_guidance = ""

        # Separate private Tell threads from public chat so unrelated tells do
        # not contaminate one another.
        self.tell_contexts = {}
        self.last_tell_partner = ""

        # Manual context controls.
        self.ignored_context_ids = set()
        self.pinned_context_ids = set()
        self._next_context_id = 1

        # Generation timing shown by the GUI.
        self.last_generation_seconds = 0.0
        self.last_generation_model = ""
        self.last_generation_timestamp = 0.0

        self.request_lock = threading.Lock()
        self.action_queue = queue.Queue()

        # Persistent RP memory and rolling session summary.
        self.memory_data, self.running_summary = load_persistent_memory(settings)
        self.summary_event_buffer = []
        self.summary_in_progress = False

        # Characters encountered during the current run are tracked separately
        # from durable memory. This lets the Relationships tab populate
        # immediately, before the periodic LLM memory summarizer has run.
        self.encountered_characters = set(
            str(name).strip()
            for name in self.memory_data.get("characters", {}).keys()
            if str(name).strip()
        )

        # Draft state is polled by the GUI.
        self.last_draft = ""
        self.last_draft_version = 0
        self.candidate_replies = []
        self.candidate_version = 0

        # One plain-text transcript per Role Weaver run.
        history_dir = _history_dir(settings)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.history_path = history_dir / f"{stamp}.txt"
        self.history_path.write_text(
            f"Role Weaver conversation history\nServer: {settings.get('server_profile','TDN')}\n"
            f"Character: {settings.get('character_name','Unknown')}\nStarted: {datetime.now().isoformat(timespec='seconds')}\n\n",
            encoding="utf-8",
        )

        # Exact content from the most recent reply-generation request.
        self.last_ai_context_display = ""
        self.last_ai_context_version = 0

    def add_system_event(self, line):
        if not line.startswith("[CHAT WINDOW TEXT]"):
            return
        profile = self.settings.get("server_profile", "TDN")
        area = ""
        if profile == "TDN":
            m = TDN_AREA_RE.search(line)
            if m:
                area = clean_nwn_text(m.group("area"))
        elif profile == "RAVENLOFT_POTM":
            m = RAVENLOFT_AREA_RE.search(line)
            if m:
                area = clean_nwn_text(m.group("area")).rstrip(".")
        if area and area != self.current_area:
            self.current_area = area
            print(f"[AREA] {area}")

    def add_chat_event(self, event):
        event = dict(event)
        event.setdefault("_context_id", self._next_context_id)
        self._next_context_id += 1
        event.setdefault("_mode", classify_ic_ooc(event.get("message", "")))

        self.context.append(event)

        # Make non-self speakers immediately available in the Relationships
        # tab. This is intentionally independent of the periodic summarizer:
        # the user can record a relationship after the first exchange.
        if not event.get("self"):
            speaker = str(event.get("speaker") or "").strip()
            if speaker:
                existing = None
                for known in self.encountered_characters:
                    if known.casefold() == speaker.casefold():
                        existing = known
                        break
                if existing is None:
                    self.encountered_characters.add(speaker)

        # Tells get a separate thread keyed by the other participant.
        if event.get("channel") == "Tell":
            partner = event.get("speaker", "")
            if event.get("self"):
                partner = self.last_tell_partner or "Tell"
            else:
                self.last_tell_partner = partner
            key = (partner or "Tell").casefold()
            dq = self.tell_contexts.setdefault(
                key,
                deque(maxlen=int(self.settings.get("tell_context_messages", 20))),
            )
            dq.append(event)

        who = "YOU" if event["self"] else event["speaker"]
        print(
            f"[{event['channel']}/{event.get('_mode', 'IC')}] "
            f"{who}: {event['message']}"
        )
        try:
            with self.history_path.open("a", encoding="utf-8") as history:
                now = datetime.now().strftime("%H:%M:%S")
                history.write(f"[{now}] [{event['channel']}] {who}: {event['message']}\n")
        except Exception as exc:
            print(f"[HISTORY ERROR] {exc}")

        if self.settings.get("memory_enabled", True):
            self.summary_event_buffer.append(dict(event))
            interval = max(6, int(self.settings.get("summary_interval_messages", 18)))
            if len(self.summary_event_buffer) >= interval and not self.summary_in_progress:
                chunk = self.summary_event_buffer[:]
                self.summary_event_buffer.clear()
                threading.Thread(
                    target=self._summarize_and_remember,
                    args=(chunk,),
                    daemon=True,
                ).start()

        if event["self"]:
            return

        self.last_external_event = event

        if self.paused or not self.auto_reply:
            return

        if event["channel"] not in self.settings["auto_reply_channels"]:
            return

        # Delay auto reply so several consecutive lines can arrive and be answered together.
        self.pending_auto_token += 1
        token = self.pending_auto_token
        delay = float(self.settings["auto_reply_delay_seconds"])

        def delayed():
            time.sleep(delay)
            if self.stop_event.is_set():
                return
            if token != self.pending_auto_token:
                return
            cooldown = float(self.settings["auto_reply_cooldown_seconds"])
            if time.time() - self.last_auto_reply_at < cooldown:
                return
            self.action_queue.put(("generate_and_send", "auto"))

        threading.Thread(target=delayed, daemon=True).start()

    def relationship_character_names(self):
        """Names available in the Relationships tab.

        Includes both durable memory records and speakers encountered during
        the current run, with case-insensitive de-duplication.
        """
        names = {}
        for name in self.memory_data.get("characters", {}).keys():
            clean = str(name or "").strip()
            if clean:
                names.setdefault(clean.casefold(), clean)
        for name in self.encountered_characters:
            clean = str(name or "").strip()
            if clean:
                names.setdefault(clean.casefold(), clean)
        return sorted(names.values(), key=str.casefold)

    def _memory_for_current_context(self):
        characters = self.memory_data.get("characters", {})
        if not characters:
            return []

        active = []
        seen = set()
        for event in self.context:
            if event.get("self"):
                continue
            name = (event.get("speaker") or "").strip()
            key = name.casefold()
            if not name or key in seen:
                continue
            seen.add(key)
            entry = characters.get(name)
            relationship = ""
            if isinstance(entry, dict):
                notes = (entry.get("notes") or "").strip()
                relationship = (entry.get("relationship") or "").strip()
            else:
                notes = str(entry or "").strip()
            if notes or relationship:
                active.append((name, notes, relationship))
        return active

    def update_character_record(self, name, notes=None, relationship=None):
        """Create or update one persistent relationship/memory record."""
        name = str(name or "").strip()
        if not name:
            print("[MEMORY] Cannot save an empty character name.")
            return False

        if name.casefold() == self.settings.get("character_name", "").casefold():
            print("[MEMORY] Refusing to create a relationship record for the active player character.")
            return False

        try:
            store = self.memory_data.setdefault("characters", {})

            # Match existing names case-insensitively so capitalization changes
            # do not create duplicate records.
            record_key = name
            for existing_name in list(store):
                if str(existing_name).casefold() == name.casefold():
                    record_key = existing_name
                    break

            current = store.get(record_key, {})
            if not isinstance(current, dict):
                current = {"notes": str(current or "").strip()}

            limit = int(self.settings.get("memory_max_characters_per_person", 1600))

            if notes is not None:
                current["notes"] = str(notes or "").strip()[:limit]
            if relationship is not None:
                current["relationship"] = str(relationship or "").strip()[:800]

            current["updated"] = datetime.now().isoformat(timespec="seconds")

            # Clearing both editable fields removes the obsolete record.
            if not current.get("notes", "").strip() and not current.get("relationship", "").strip():
                store.pop(record_key, None)
                print(f"[MEMORY] Removed empty relationship/memory record for {record_key}.")
            else:
                store[record_key] = current

            save_persistent_memory(
                self.settings,
                self.memory_data,
                self.running_summary,
            )
            self.encountered_characters.add(record_key)
            return True
        except Exception as exc:
            print(
                f"[MEMORY ERROR] Could not save relationship/memory for {name}: "
                f"{type(exc).__name__}: {exc}"
            )
            return False

    def _event_is_visible_to_ai(self, event):
        cid = event.get("_context_id")
        if cid in self.ignored_context_ids:
            return False
        if self.settings.get("ignore_ooc_for_ai", True) and event.get("_mode") == "OOC":
            return False
        return True

    def _active_context_events(self):
        # If the latest external message is a Tell, use only that private Tell
        # thread plus pinned messages. Otherwise use normal public context and
        # exclude Tell traffic to prevent private conversations leaking across.
        latest = self.last_external_event or {}
        if latest.get("channel") == "Tell":
            partner = (latest.get("speaker") or self.last_tell_partner or "Tell").casefold()
            base = list(self.tell_contexts.get(partner, []))
        else:
            base = [e for e in self.context if e.get("channel") != "Tell"]

        by_id = {e.get("_context_id"): e for e in self.context}
        for cid in self.pinned_context_ids:
            e = by_id.get(cid)
            if e and e not in base:
                base.insert(0, e)

        return [e for e in base if self._event_is_visible_to_ai(e)]

    def context_rows(self):
        rows = []
        for e in self.context:
            cid = e.get("_context_id")
            rows.append({
                "id": cid,
                "speaker": "YOU" if e.get("self") else e.get("speaker", ""),
                "channel": e.get("channel", ""),
                "mode": e.get("_mode", "IC"),
                "message": e.get("message", ""),
                "ignored": cid in self.ignored_context_ids,
                "pinned": cid in self.pinned_context_ids,
            })
        return rows

    def ignore_context_event(self, context_id, ignored=True):
        if ignored:
            self.ignored_context_ids.add(context_id)
        else:
            self.ignored_context_ids.discard(context_id)

    def pin_context_event(self, context_id, pinned=True):
        if pinned:
            self.pinned_context_ids.add(context_id)
        else:
            self.pinned_context_ids.discard(context_id)

    def forget_before(self, context_id):
        kept = [e for e in self.context if e.get("_context_id", 0) >= context_id]
        self.context.clear()
        self.context.extend(kept)
        live_ids = {e.get("_context_id") for e in kept}
        self.ignored_context_ids.intersection_update(live_ids)
        self.pinned_context_ids.intersection_update(live_ids)
        print(f"[CONTEXT] Forgot messages before #{context_id}.")

    def build_context_text(self):
        lines = []

        if self.current_area:
            lines.append(f"CURRENT AREA: {self.current_area}")

        if self.running_summary:
            lines.append("")
            lines.append("EARLIER SESSION SUMMARY:")
            lines.append(self.running_summary)

        memories = self._memory_for_current_context()
        if memories:
            lines.append("")
            lines.append("PERSISTENT CHARACTER MEMORY / RELATIONSHIPS:")
            for name, notes, relationship in memories:
                details = []
                if relationship:
                    details.append(f"Relationship: {relationship}")
                if notes:
                    details.append(f"Memory: {notes}")
                lines.append(f"- {name}: " + " | ".join(details))

        active_events = self._active_context_events()

        recent_for_lore = "\n".join(
            f"{e.get('speaker', '')} {e.get('message', '')}" for e in active_events
        )
        lore = load_relevant_lore(
            (self.running_summary or "") + "\n" + recent_for_lore,
            self.settings.get("server_profile", "CUSTOM"),
        )
        if lore:
            lines.append("")
            lines.append("RELEVANT LORE REFERENCES:")
            for filename, text in lore:
                lines.append(f"--- {filename} ---")
                lines.append(text)

        if self.last_external_event and self.last_external_event.get("channel") == "Tell":
            lines.append("")
            lines.append(
                "PRIVATE TELL CONTEXT: Answer only this Tell conversation. "
                "Do not blend in unrelated public chat or other private Tell threads."
            )

        lines.append("")
        lines.append("RECENT CHAT:")
        for e in active_events:
            prefix = "YOU" if e.get("self") else e.get("speaker", "")
            mode = e.get("_mode", "IC")
            lines.append(
                f"#{e.get('_context_id')} {prefix} "
                f"[{e.get('channel', 'Talk')}/{mode}]: {e.get('message', '')}"
            )

        if not active_events:
            lines.append("(No active IC context after filters.)")

        return "\n".join(lines).strip()

    def _summarize_and_remember(self, events):
        if not events or self.summary_in_progress:
            return

        self.summary_in_progress = True
        try:
            transcript = []
            participants = []
            seen = set()
            for e in events:
                who = "YOU" if e.get("self") else (e.get("speaker") or "Unknown")
                transcript.append(f"{who} [{e.get('channel', 'Talk')}]: {e.get('message', '')}")
                if not e.get("self"):
                    name = (e.get("speaker") or "").strip()
                    if name and name.casefold() not in seen:
                        seen.add(name.casefold())
                        participants.append(name)

            existing = {}
            existing_relationships = {}
            all_memory = self.memory_data.get("characters", {})
            for name in participants:
                item = all_memory.get(name, {})
                notes = item.get("notes", "") if isinstance(item, dict) else str(item or "")
                relationship = item.get("relationship", "") if isinstance(item, dict) else ""
                if notes:
                    existing[name] = notes
                if relationship:
                    existing_relationships[name] = relationship

            prompt = (
                "Maintain memory for a live roleplay assistant. Return STRICT JSON only.\n"
                "Use this exact shape:\n"
                '{"summary":"concise rolling session summary","memories":{"Character Name":"concise durable facts"},"relationships":{"Character Name":"brief description of the player character relationship and attitude"}}\n\n'
                "The summary should combine the earlier summary with the new transcript, preserving "
                "important promises, relationships, conflicts, discoveries, goals, and unresolved matters. "
                "Do not invent facts. Memories should contain only durable facts useful when that character "
                "is encountered again. Relationships should describe trust, attitude, obligations, conflicts, "
                "friendship, suspicion, affection, authority, or other meaningful interpersonal state only when supported. "
                "Do not include the player character as a memory/relationship key.\n\n"
                f"PLAYER CHARACTER: {self.settings.get('character_name', '')}\n"
                f"EARLIER SUMMARY:\n{self.running_summary or '(none)'}\n\n"
                f"EXISTING MEMORIES:\n{json.dumps(existing, ensure_ascii=False)}\n\n"
                f"EXISTING RELATIONSHIPS:\n{json.dumps(existing_relationships, ensure_ascii=False)}\n\n"
                "NEW TRANSCRIPT:\n" + "\n".join(transcript)
            )
            instructions = (
                "You are a precise roleplay continuity summarizer. "
                "Return valid JSON only, with no markdown or commentary."
            )

            with self.request_lock:
                raw = self.client.generate(instructions, prompt)

            parsed = extract_json_object(raw)
            if not isinstance(parsed, dict):
                print("[MEMORY] Summary response was not valid JSON; existing memory was left unchanged.")
                return

            summary = str(parsed.get("summary") or "").strip()
            memories = parsed.get("memories") or {}
            relationships = parsed.get("relationships") or {}

            if summary:
                self.running_summary = summary

            store = self.memory_data.setdefault("characters", {})
            limit = int(self.settings.get("memory_max_characters_per_person", 1600))
            stamp = datetime.now().isoformat(timespec="seconds")

            if isinstance(memories, dict):
                for name, notes in memories.items():
                    name = str(name or "").strip()
                    notes = " ".join(str(notes or "").split()).strip()
                    if not name or not notes:
                        continue
                    if name.casefold() == self.settings.get("character_name", "").casefold():
                        continue
                    record_key = name
                    for existing_name in list(store):
                        if str(existing_name).casefold() == name.casefold():
                            record_key = existing_name
                            break
                    current = store.get(record_key, {})
                    if not isinstance(current, dict):
                        current = {}
                    current["notes"] = notes[:limit]
                    current["updated"] = stamp
                    store[record_key] = current
                    self.encountered_characters.add(record_key)

            if isinstance(relationships, dict):
                for name, relationship in relationships.items():
                    name = str(name or "").strip()
                    relationship = " ".join(str(relationship or "").split()).strip()
                    if not name or not relationship:
                        continue
                    if name.casefold() == self.settings.get("character_name", "").casefold():
                        continue
                    record_key = name
                    for existing_name in list(store):
                        if str(existing_name).casefold() == name.casefold():
                            record_key = existing_name
                            break
                    current = store.get(record_key, {})
                    if not isinstance(current, dict):
                        current = {}
                    current["relationship"] = relationship[:800]
                    current["updated"] = stamp
                    store[record_key] = current
                    self.encountered_characters.add(record_key)

            save_persistent_memory(self.settings, self.memory_data, self.running_summary)
            archive_session_summary(self.settings, self.running_summary)
            print(
                f"[MEMORY] Updated session summary and persistent memory "
                f"for {len(memories) if isinstance(memories, dict) else 0} character(s)."
            )
        except Exception as exc:
            print(f"[MEMORY ERROR] {type(exc).__name__}: {exc}")
        finally:
            self.summary_in_progress = False

    def flush_memory_summary(self):
        if not self.settings.get("memory_enabled", True):
            return
        if not self.summary_event_buffer or self.summary_in_progress:
            return
        chunk = self.summary_event_buffer[:]
        self.summary_event_buffer.clear()
        self._summarize_and_remember(chunk)

    def _response_length_target(self):
        mode = str(self.settings.get("response_length_mode", "Auto") or "Auto").title()
        hard_max = int(self.settings.get("max_reply_characters", 430))
        if mode == "Brief":
            return min(hard_max, 220), "brief and direct"
        if mode == "Normal":
            return min(hard_max, 340), "moderately concise"
        if mode == "Detailed":
            return hard_max, "as detailed and expressive as the live scene reasonably needs"

        # Auto: infer from the latest incoming RP line. Short banter stays short;
        # longer questions/exposition are allowed more room.
        latest = self.last_external_event or {}
        msg = str(latest.get("message", ""))
        if len(msg) < 80 and "?" not in msg:
            return min(hard_max, 220), "brief because the current exchange is short"
        if len(msg) < 190:
            return min(hard_max, 340), "natural conversational length"
        return hard_max, "detailed enough to address the longer exchange"

    def generate_reply(self, draft_instruction=""):
        if not self.context:
            print("[AI] No chat context yet.")
            return None

        prompt = self.build_context_text()

        # Guidance may come from either the small Guidance window or the
        # console command. The shared file lets both interfaces stay in sync.
        shared_guidance = read_shared_guidance()
        guidance = shared_guidance or self.next_guidance.strip()
        if guidance:
            prompt += (
                "\n\nPLAYER GUIDANCE:\n"
                + guidance
                + "\nFollow this guidance while staying fully in character. "
                  "Do not mention or reveal the guidance itself."
            )

        if draft_instruction:
            prompt += (
                "\n\nDRAFT REVISION INSTRUCTION:\n"
                + draft_instruction
                + "\nFollow this instruction without mentioning it."
            )

        target_characters, length_guidance = self._response_length_target()
        server_rules = load_server_roleplay_rules(
            self.settings.get("server_profile", "CUSTOM")
        )
        rules_block = (
            "\n\nSERVER RESPONSE RULES (follow these for this server):\n" + server_rules
            if server_rules else ""
        )
        instructions = f"""{self.character_prompt}{rules_block}

You are assisting live roleplay in Neverwinter Nights.

Output exactly ONE in-character chat entry suitable for sending directly into NWN.
You may combine spoken dialogue and a short emote in the same entry.
Do not include labels such as SAY:, RESPONSE:, or Lora:.
Do not mention AI, prompts, logs, automation, or game mechanics.
Do not answer ambient speech unless it reasonably appears relevant to the ongoing conversation.
If there is genuinely nothing appropriate to say, output exactly: <NO_REPLY>
Aim for a {length_guidance} response and keep it under {target_characters} characters.
"""

        self.last_ai_context_display = (
            "=== CHARACTER / SYSTEM INSTRUCTIONS ===\n"
            + instructions.strip()
            + "\n\n=== CONTENT SENT FOR THIS REPLY ===\n"
            + prompt.strip()
        )
        self.last_ai_context_version += 1

        with self.request_lock:
            try:
                print("[AI] Generating...")
                started = time.perf_counter()
                reply = self.client.generate(instructions, prompt)
                self.last_generation_seconds = time.perf_counter() - started
                self.last_generation_model = getattr(self.client, "model", self.settings.get("model", ""))
                self.last_generation_timestamp = time.time()
                if self.settings.get("generation_timing", True):
                    print(
                        f"[AI TIMING] {self.last_generation_seconds:.2f}s "
                        f"using {self.last_generation_model}"
                    )

                if not reply or reply == "<NO_REPLY>":
                    print("[AI] No reply suggested.")
                    return None

                reply = " ".join(reply.replace("\r", " ").replace("\n", " ").split())
                reply = reply[: target_characters].strip()
                print(f"[AI] {reply}")
                if guidance:
                    # Guidance now persists until the user explicitly clears it.
                    self.next_guidance = guidance
                return reply

            except Exception as exc:
                print(f"[AI ERROR] {exc}")
                return None

    def generate_candidates(self):
        if not self.context:
            print("[AI] No chat context yet.")
            return []

        count = max(2, min(5, int(self.settings.get("candidate_count", 3))))
        prompt = self.build_context_text()
        shared_guidance = read_shared_guidance()
        guidance = shared_guidance or self.next_guidance.strip()
        if guidance:
            prompt += (
                "\n\nPLAYER GUIDANCE FOR THESE REPLIES:\n" + guidance
                + "\nFollow it while staying in character; never reveal the guidance."
            )

        target_characters, length_guidance = self._response_length_target()
        server_rules = load_server_roleplay_rules(
            self.settings.get("server_profile", "CUSTOM")
        )
        rules_block = (
            "\n\nSERVER RESPONSE RULES (follow these for this server):\n" + server_rules
            if server_rules else ""
        )
        instructions = f"""{self.character_prompt}{rules_block}

You are assisting live roleplay in Neverwinter Nights.
Generate {count} meaningfully different candidate replies for the same moment.
Each candidate must be a single in-character NWN chat entry.
Do not include speaker labels or wrap spoken dialogue in quotation marks.
Do not mention AI, prompts, logs, automation, or game mechanics.
Each candidate should be {length_guidance} and under {target_characters} characters.
Return STRICT JSON only in this form: {{"candidates":["reply 1","reply 2","reply 3"]}}
"""
        self.last_ai_context_display = (
            "=== CHARACTER / SYSTEM INSTRUCTIONS ===\n" + instructions.strip()
            + "\n\n=== CONTENT SENT FOR THIS REPLY ===\n" + prompt.strip()
        )
        self.last_ai_context_version += 1

        with self.request_lock:
            try:
                print(f"[AI] Generating {count} candidate replies...")
                raw=self.client.generate(instructions,prompt)
                parsed=extract_json_object(raw)
                values=parsed.get("candidates",[]) if isinstance(parsed,dict) else []
                candidates=[]
                for value in values:
                    text=" ".join(str(value).replace("\r"," ").replace("\n"," ").split()).strip()
                    if text and text != "<NO_REPLY>":
                        candidates.append(text[:target_characters].strip())
                candidates=candidates[:count]
                if not candidates:
                    print("[AI] No candidates returned.")
                    return []
                self.candidate_replies=candidates
                self.candidate_version += 1
                self._publish_draft(candidates[0])
                if guidance:
                    self.next_guidance=""
                    clear_shared_guidance()
                    print("[GUIDE] One-shot guidance consumed and cleared.")
                print(f"[AI] {len(candidates)} candidates ready.")
                return candidates
            except Exception as exc:
                print(f"[AI ERROR] Candidate generation failed: {exc}")
                return []

    def _publish_draft(self, reply):
        if not reply:
            return
        self.last_draft = reply
        self.last_draft_version += 1

    def suggest(self, variant="normal"):
        if variant == "normal" or variant == "regenerate":
            return self.generate_candidates()

        instruction = ""
        if variant == "regenerate":
            instruction = (
                "Generate a different in-character reply to the same situation. "
                "Do not merely paraphrase the previous draft."
            )
        elif variant == "shorter":
            instruction = (
                "Make the reply noticeably shorter and more concise than the previous draft. "
                f"Previous draft: {self.last_draft}"
            )
        elif variant == "longer":
            instruction = (
                "Make the reply somewhat longer and more expressive than the previous draft, "
                "while still respecting the maximum reply length. "
                f"Previous draft: {self.last_draft}"
            )

        reply = self.generate_reply(draft_instruction=instruction)
        if reply:
            self._publish_draft(reply)
            print("\n--- AI DRAFT ---")
            print(reply)
            print("----------------\n")

    def generate_and_send(self, source="manual"):
        reply = self.generate_reply()
        if not reply:
            return

        # F9/manual mode goes directly to NWN and should not alter the
        # dedicated AI Draft box. F8 and the draft-variation controls own that box.

        # F9/manual mode: give the user a moment to focus NWN before
        # opening the chat bar and pasting the generated draft.
        original_focus = self.settings.get("focus_game_before_typing", True)
        if source == "manual":
            print("[F9] Reply generated.")
            print("[F9] Click/focus NWN now. Pasting in 2 seconds...")
            time.sleep(2)
            # The user has been explicitly asked to focus NWN. Avoid a
            # SetForegroundWindow call from this background worker immediately
            # afterward, because Windows may reject that focus steal.
            self.settings["focus_game_before_typing"] = False

        try:
            sent_ok = send_chat_to_nwn(
                reply,
                self.settings,
                leave_unsent=(source == "manual"),
            )
        finally:
            self.settings["focus_game_before_typing"] = original_focus

        if sent_ok:
            self.last_auto_reply_at = time.time()

            if source == "manual":
                print("[DRAFT] Response placed in NWN chat for editing.")
            else:
                print(f"[SEND] Sent ({source}).")

            # F9 creates an editable draft. Do not record it as something the
            # character actually said; the real edited/sent version will be
            # picked up from the NWN log. Auto/F10 replies are actually sent,
            # so record those immediately.
            if source != "manual":
                self.context.append({
                    "speaker_id": "",
                    "speaker": self.settings["character_name"],
                    "channel": "Talk",
                    "message": reply,
                    "self": True,
                    "_generated": True,
                })


    def paste_existing_draft(self, text):
        text = " ".join((text or "").replace("\r", " ").replace("\n", " ").split()).strip()
        if not text:
            print("[DRAFT] No draft text to paste.")
            return
        text = text[: int(self.settings["max_reply_characters"])].strip()
        self._publish_draft(text)
        print("[DRAFT] Click/focus NWN now. Pasting edited draft in 2 seconds...")
        time.sleep(2)
        original_focus = self.settings.get("focus_game_before_typing", True)
        self.settings["focus_game_before_typing"] = False
        try:
            sent_ok = send_chat_to_nwn(text, self.settings, leave_unsent=True)
        finally:
            self.settings["focus_game_before_typing"] = original_focus
        if sent_ok:
            print("[DRAFT] Edited draft placed in NWN chat. Review it and press Enter yourself.")

    def keyboard_test(self, force_method=None, manual_focus=False):
        method = force_method or self.settings.get("keyboard_method", "scancode")
        test_text = f"NWN AI keyboard test ({method}) - visible but NOT sent."
        print(f"[TEST] Keyboard test using: {method}")

        original_focus = self.settings.get("focus_game_before_typing", True)

        if manual_focus:
            # Do not let the program change focus. The user places NWN in the
            # foreground during the countdown, then we inject directly.
            self.settings["focus_game_before_typing"] = False
            manual_focus_countdown(5)

        try:
            ok = send_chat_to_nwn(
                test_text,
                self.settings,
                leave_unsent=True,
                force_method=method,
            )
        finally:
            self.settings["focus_game_before_typing"] = original_focus

        if ok:
            print("[TEST] If you see the text in NWN, press Escape there to cancel it.")
        else:
            print("[TEST] This method failed before completing the test.")


    def run_all_keyboard_tests(self):
        print("[TEST] Running keyboard methods one at a time.")
        print("[TEST] After each successful test, press Escape in NWN before continuing.")
        for method in ("scancode", "sendinput", "keybd_event", "postmessage"):
            input(f"\nPress ENTER here to test '{method}'...")
            self.keyboard_test(force_method=method)


    def toggle_pause(self):
        self.paused = not self.paused
        print(f"[MODE] {'PAUSED' if self.paused else 'LISTENING'}")

    def toggle_auto(self):
        self.auto_reply = not self.auto_reply
        print(f"[MODE] Auto-reply {'ON' if self.auto_reply else 'OFF'}")

    def clear_context(self):
        if self.settings.get("memory_enabled", True) and self.summary_event_buffer and not self.summary_in_progress:
            threading.Thread(target=self.flush_memory_summary, daemon=True).start()
        self.context.clear()
        self.tell_contexts.clear()
        self.ignored_context_ids.clear()
        self.pinned_context_ids.clear()
        self.current_area = ""
        self.last_external_event = None
        self.last_tell_partner = ""
        print("[CONTEXT] Cleared.")

    def should_suppress_duplicate_self(self, event):
        if not event["self"] or not self.context:
            return False
        last = self.context[-1]
        return (
            last.get("_generated")
            and last["message"].strip() == event["message"].strip()
        )

    def action_worker(self):
        while not self.stop_event.is_set():
            try:
                action, source = self.action_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if action == "keyboard_test":
                self.keyboard_test()
            elif action == "manual_keyboard_test":
                self.keyboard_test(force_method="scancode", manual_focus=True)
            elif action == "all_keyboard_tests":
                self.run_all_keyboard_tests()
            elif action == "suggest":
                self.suggest()
            elif action == "draft_variant":
                self.suggest(variant=source)
            elif action == "paste_existing_draft":
                self.paste_existing_draft(source)
            elif action == "generate_and_send":
                self.generate_and_send(source=source)
            elif action == "toggle_pause":
                self.toggle_pause()
            elif action == "toggle_auto":
                self.toggle_auto()
            elif action == "clear":
                self.clear_context()
            elif action == "quit":
                self.stop_event.set()

    def console_listener(self):
        print()
        print("Console commands are also available (use these if function keys are swallowed by NWN):")
        print("  test       = test configured keyboard method")
        print("  manualtest = 5-second countdown; click NWN, then scancode test")
        print("  tests      = test pynput, pyautogui, sendinput, postmessage")
        print("  speak      = generate + send one reply")
        print("  draft      = generate draft only")
        print("  guide <text> = guide the next AI reply only")
        print("  guide?       = show queued guidance")
        print("  guide clear  = clear queued guidance")
        print("  auto       = toggle auto-reply")
        print("  pause      = pause/resume listening")
        print("  clear      = clear context")
        print("  quit       = quit")
        print()

        while not self.stop_event.is_set():
            try:
                raw_cmd = input("NWN-AI> ").strip()
                cmd = raw_cmd.lower()
            except (EOFError, KeyboardInterrupt):
                return

            if cmd == "guide?":
                queued_guidance = read_shared_guidance() or self.next_guidance.strip()
                if queued_guidance:
                    print(f"[GUIDE] Queued: {queued_guidance}")
                else:
                    print("[GUIDE] No guidance queued.")
            elif cmd == "guide clear":
                self.next_guidance = ""
                clear_shared_guidance()
                print("[GUIDE] Cleared.")
            elif cmd.startswith("guide "):
                guidance = raw_cmd[6:].strip()
                if guidance:
                    self.next_guidance = guidance
                    write_shared_guidance(guidance)
                    print(f"[GUIDE] Next reply: {guidance}")
                else:
                    print("[GUIDE] Usage: guide <instruction>")
            elif cmd == "test":
                self.action_queue.put(("keyboard_test", "console"))
            elif cmd == "manualtest":
                self.action_queue.put(("manual_keyboard_test", "console"))
            elif cmd == "tests":
                self.action_queue.put(("all_keyboard_tests", "console"))
            elif cmd == "speak":
                self.action_queue.put(("generate_and_send", "console"))
            elif cmd == "draft":
                self.action_queue.put(("suggest", "console"))
            elif cmd == "auto":
                self.action_queue.put(("toggle_auto", "console"))
            elif cmd == "pause":
                self.action_queue.put(("toggle_pause", "console"))
            elif cmd == "clear":
                self.action_queue.put(("clear", "console"))
            elif cmd == "quit":
                self.action_queue.put(("quit", "console"))
                return
            elif cmd:
                print("[CONSOLE] Unknown command.")

    def hotkey_listener(self):
        def on_f6():
            self.action_queue.put(("toggle_pause", "hotkey"))

        def on_f7():
            print("[HOTKEY] F7 detected")
            self.action_queue.put(("keyboard_test", "hotkey"))

        def on_f8():
            self.action_queue.put(("suggest", "hotkey"))

        def on_f9():
            print("[HOTKEY] F9 detected")
            self.action_queue.put(("generate_and_send", "manual"))

        def on_f10():
            print("[HOTKEY] F10 detected")
            self.action_queue.put(("toggle_auto", "hotkey"))

        def on_f11():
            self.action_queue.put(("clear", "hotkey"))

        def on_f12():
            self.action_queue.put(("quit", "hotkey"))

        hotkeys = keyboard.GlobalHotKeys({
            "<f6>": on_f6,
            "<f7>": on_f7,
            "<f8>": on_f8,
            "<f9>": on_f9,
            "<f10>": on_f10,
            "<f11>": on_f11,
            "<f12>": on_f12,
        })
        hotkeys.start()
        return hotkeys

    def run(self):
        print("=" * 68)
        print("NWN:EE AI Roleplay Client")
        print("=" * 68)
        print(f"Character : {self.settings['character_name']}")
        print(f"Model     : {self.settings['model']}")
        print(f"Log       : {self.settings['log_path']}")
        print()
        print("Hotkeys (work globally while NWN is focused):")
        print("  F6   Pause/resume listening")
        print("  F7   Keyboard test: open chat + type text, DO NOT send")
        print("  F8   Generate a draft in this console only")
        print("  F9   Generate a reply and send it to NWN")
        print("  F10  Toggle automatic replies")
        print("  F11  Clear conversation context")
        print("  F12  Quit")
        print()
        print("Start NWN now. This program will wait for the client log.")
        print("Auto-reply starts OFF unless settings.json says otherwise.")
        print("=" * 68)

        worker = threading.Thread(target=self.action_worker, daemon=True)
        worker.start()
        hotkeys = self.hotkey_listener()
        console_thread = threading.Thread(target=self.console_listener, daemon=True)
        console_thread.start()

        follower = LogFollower(
            self.settings["log_path"],
            float(self.settings["poll_interval_seconds"]),
        )

        try:
            for line in follower.lines(self.stop_event):
                self.add_system_event(line)

                event = parse_chat_line(
                    line,
                    self.settings["character_name"],
                    self.settings.get("server_profile", "CUSTOM"),
                )
                if not event:
                    continue

                if self.should_suppress_duplicate_self(event):
                    # Replace generated placeholder with authoritative log copy.
                    self.context.pop()

                self.add_chat_event(event)

        except KeyboardInterrupt:
            pass
        finally:
            self.stop_event.set()
            try:
                hotkeys.stop()
            except Exception:
                pass
            print("\nStopped.")


def main():
    if os.name != "nt":
        print("This build is intended for Windows.")
        sys.exit(1)

    settings = load_settings()
    character_prompt = load_character_prompt()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("OPENAI_API_KEY is not set.")
        print("Paste your OpenAI API key below. It is used for this run only.")
        api_key = getpass.getpass("API key: ").strip()

    if not api_key:
        print("No API key supplied.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    bot = NWNAIBot(settings, character_prompt, client)
    bot.run()


if __name__ == "__main__":
    main()
