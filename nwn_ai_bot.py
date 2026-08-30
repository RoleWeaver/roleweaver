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
from pathlib import Path

import pyautogui
import pyperclip
from pynput import keyboard
from openai import OpenAI


APP_DIR = Path(__file__).resolve().parent
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

AREA_RE = re.compile(r"\*Now Entering (?P<area>.+?)\*\s*$")

DEFAULT_SETTINGS = {
    "log_path": r"C:\Users\User\Documents\Neverwinter Nights\logs\nwclientLog1.txt",
    "character_name": "Lora Thendry",
    "model": "gpt-5.6-luna",
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
    "focus_delay_seconds": 0.60,
    "chat_open_delay_seconds": 0.45,
    "before_send_delay_seconds": 0.35,
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
    return merged


def load_character_prompt():
    if not CHARACTER_PROMPT_PATH.exists():
        CHARACTER_PROMPT_PATH.write_text(
            "You are roleplaying a character in Neverwinter Nights.\n"
            "Stay in character and write only what the character says or emotes.\n",
            encoding="utf-8",
        )
    return CHARACTER_PROMPT_PATH.read_text(encoding="utf-8").strip()


def clean_nwn_text(text):
    text = COLOR_TAG_RE.sub("", text)
    text = CONTROL_RE.sub("", text)
    return text.strip()


def parse_chat_line(line, character_name):
    raw = line.strip()

    # The log includes a second, human-readable copy beginning with this marker.
    # We ignore it and use the more structured [Talk]/[Whisper]/etc. copy.
    if not raw or raw.startswith("[CHAT WINDOW TEXT]"):
        return None

    m = STRUCTURED_CHAT_RE.match(raw)
    if not m:
        return None

    speaker = clean_nwn_text(m.group("speaker"))
    message = clean_nwn_text(m.group("message"))
    channel = m.group("channel").title()
    speaker_id = (m.group("speaker_id") or "").strip()

    if not speaker or not message:
        return None

    # Menu/conversation choices can be echoed as Talk. Do not treat them as RP.
    if message.startswith("[") and message.endswith("]"):
        return None

    return {
        "speaker_id": speaker_id,
        "speaker": speaker,
        "channel": channel,
        "message": message,
        "self": speaker.casefold() == character_name.casefold(),
    }


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
    hwnd, title = find_window_handle(title_contains)
    if not hwnd:
        return False, None

    user32 = ctypes.windll.user32
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    ok = bool(user32.SetForegroundWindow(hwnd))
    time.sleep(0.15)
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

    if settings.get("focus_game_before_typing", True):
        ok, title = focus_nwn_window(settings["window_title_contains"])
        hwnd, fg_title = get_foreground_window_title()

        print(f"[FOCUS] selected='{title}'")
        print(f"[FOCUS] foreground='{fg_title}'")

        if not ok:
            print("[SEND] Windows refused the foreground-window request.")
            return False

        if not fg_title or settings["window_title_contains"].casefold() not in fg_title.casefold():
            print("[SEND] NWN is not actually the foreground window.")
            print("[SEND] Click NWN manually, then retry the test.")
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

        if old_clipboard is not None:
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass

        if leave_unsent:
            print("[TEST] Test text should now be visible in NWN's chat entry field.")
            print("[TEST] It was intentionally NOT sent.")
            return True

        print("[SEND] Sending chat...")
        press_enter()
        return True

    except Exception as exc:
        print(f"[SEND ERROR] {type(exc).__name__}: {exc}")
        return False



GUIDANCE_FILE = Path(__file__).with_name("next_guidance.txt")


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

        self.request_lock = threading.Lock()
        self.action_queue = queue.Queue()

    def add_system_event(self, line):
        # Area changes are useful context even though they are not chat.
        if line.startswith("[CHAT WINDOW TEXT]"):
            m = AREA_RE.search(line)
            if m:
                area = clean_nwn_text(m.group("area"))
                if area and area != self.current_area:
                    self.current_area = area
                    print(f"[AREA] {area}")

    def add_chat_event(self, event):
        self.context.append(event)

        who = "YOU" if event["self"] else event["speaker"]
        print(f"[{event['channel']}] {who}: {event['message']}")

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

    def build_context_text(self):
        lines = []

        if self.current_area:
            lines.append(f"CURRENT AREA: {self.current_area}")

        lines.append("RECENT CHAT:")

        for e in self.context:
            prefix = "YOU" if e["self"] else e["speaker"]
            lines.append(f"{prefix} [{e['channel']}]: {e['message']}")

        return "\n".join(lines)

    def generate_reply(self):
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
                "\n\nPLAYER GUIDANCE FOR THIS REPLY:\n"
                + guidance
                + "\nFollow this guidance while staying fully in character. "
                  "Do not mention or reveal the guidance itself."
            )

        instructions = f"""{self.character_prompt}

You are assisting live roleplay in Neverwinter Nights.

Output exactly ONE in-character chat entry suitable for sending directly into NWN.
You may combine spoken dialogue and a short emote in the same entry.
Do not include labels such as SAY:, RESPONSE:, or Lora:.
Do not mention AI, prompts, logs, automation, or game mechanics.
Do not answer ambient speech unless it reasonably appears relevant to the ongoing conversation.
If there is genuinely nothing appropriate to say, output exactly: <NO_REPLY>
Keep the response under {self.settings['max_reply_characters']} characters.
"""

        with self.request_lock:
            try:
                print("[AI] Generating...")
                response = self.client.responses.create(
                    model=self.settings["model"],
                    instructions=instructions,
                    input=prompt,
                )
                reply = (response.output_text or "").strip()

                if not reply or reply == "<NO_REPLY>":
                    print("[AI] No reply suggested.")
                    return None

                reply = " ".join(reply.replace("\r", " ").replace("\n", " ").split())
                reply = reply[: int(self.settings["max_reply_characters"])].strip()
                print(f"[AI] {reply}")
                if guidance:
                    self.next_guidance = ""
                    clear_shared_guidance()
                    print("[GUIDE] One-shot guidance consumed and cleared.")
                return reply

            except Exception as exc:
                print(f"[AI ERROR] {exc}")
                return None

    def suggest(self):
        reply = self.generate_reply()
        if reply:
            print("\n--- DRAFT ONLY ---")
            print(reply)
            print("------------------\n")

    def generate_and_send(self, source="manual"):
        reply = self.generate_reply()
        if not reply:
            return

        # F9/manual mode: give the user a moment to focus NWN before
        # opening the chat bar and pasting the generated draft.
        if source == "manual":
            print("[F9] Reply generated.")
            print("[F9] Focus NWN now. Pasting in 2 seconds...")
            time.sleep(2)

        if send_chat_to_nwn(
            reply,
            self.settings,
            leave_unsent=(source == "manual"),
        ):
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
        self.context.clear()
        self.current_area = ""
        self.last_external_event = None
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
