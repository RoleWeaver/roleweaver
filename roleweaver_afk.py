"""Session-only AFK scheduling shared by Windows and Linux."""
import re
import threading
import time


class AFKMixin:
    def init_afk(self):
        self.afk = False
        self._afk_lock = threading.RLock()
        self._afk_epoch = 0
        self._afk_pending = False
        self._afk_next_check = 0
        self._afk_next_reply = 0

    def toggle_afk(self):
        with self._afk_lock:
            if self.stop_event.is_set():
                return
            if not self.afk and not self.afk_available():
                print("[AFK] Automatic sending is unavailable on Wayland.")
                return
            self.afk = not self.afk
            self._afk_epoch += 1
            self.pending_auto_token += 1
            if self.afk:
                self._afk_previous_auto = self.auto_reply
                self.auto_reply = False
                self._afk_pending = True
                self._afk_next_check = time.monotonic()
                self._afk_next_reply = 0
            else:
                self.auto_reply = self._afk_previous_auto
                self._afk_pending = False
            print(f"[AFK] {'ON' if self.afk else 'OFF'}")

    def observe_afk(self, event):
        with self._afk_lock:
            if not self.afk or self.paused or event.get("self") or event.get("_mode") == "OOC":
                return
            name = self.settings.get("character_name", "").strip()
            names = [name] + ([name.split()[0]] if name else [])
            addressed = event.get("channel") == "Tell" or (
                event.get("channel") in ("Talk", "Whisper", "Party", "DM")
                and any(re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)",
                                  event.get("message", ""), re.IGNORECASE)
                        for n in names if n)
            )
            if addressed:
                self._afk_pending = True

    def check_afk(self):
        now = time.monotonic()
        with self._afk_lock:
            if not self.afk or self.stop_event.is_set() or self.paused:
                return
            if now < self._afk_next_check:
                return
            self._afk_next_check = now + 30
            if not self._afk_pending or now < self._afk_next_reply:
                return
            epoch = self._afk_epoch
            self._afk_pending = False
            # Failed requests also back off; never hammer the provider.
            self._afk_next_reply = now + 180
        instructions = (
            "Write one brief third-person roleplay emote showing this character "
            "is distracted, daydreaming or dozing and not paying attention. "
            "Use the character profile only for personality. Do not answer anyone, "
            "make decisions, advance the scene, or mention AI or automation. "
            "Return only the emote, surrounded by asterisks, at most 200 characters."
        )
        try:
            with self.request_lock:
                with self._afk_lock:
                    if not self.afk or epoch != self._afk_epoch or self.stop_event.is_set():
                        return
                raw = self.client.generate(instructions, "Character profile:\n" + self.character_prompt)
            text = " ".join(str(raw or "").split()).strip()
            if not text or text == "<NO_REPLY>":
                return
            limit = min(200, int(self.settings["max_reply_characters"]))
            text = "*" + text.strip("*")[:max(0, limit - 2)].strip() + "*"
            with self._afk_lock:
                if not self.afk or epoch != self._afk_epoch or self.paused or self.stop_event.is_set():
                    return
                if self.send_afk(text):
                    self._afk_next_reply = time.monotonic() + 180
                    print("[AFK] Emote sent.")
        except Exception as exc:
            print(f"[AFK ERROR] {exc}")
