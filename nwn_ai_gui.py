import os
import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from openai import OpenAI

import nwn_ai_bot as core


class QueueWriter:
    """Thread-safe stdout/stderr bridge into the Tk UI."""
    def __init__(self, output_queue):
        self.output_queue = output_queue
        self.buffer = ""

    def write(self, text):
        if not text:
            return
        self.buffer += str(text)
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self.output_queue.put(line)

    def flush(self):
        if self.buffer:
            self.output_queue.put(self.buffer)
            self.buffer = ""


class NWNAIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NWN:EE AI Roleplay Client")
        self.root.geometry("820x720")
        self.root.minsize(700, 600)

        self.output_queue = queue.Queue()
        self.writer = QueueWriter(self.output_queue)
        sys.stdout = self.writer
        sys.stderr = self.writer

        self.bot = None
        self.bot_thread = None
        self.hotkeys = None
        self.running = False
        self.guidance_dirty = False
        self.last_guidance_file_value = None

        self.settings = core.load_settings()
        self.character_prompt = core.load_character_prompt()

        self._build_ui()
        self._load_initial_values()
        self._poll_output()
        self._poll_bot_state()
        self._poll_guidance_file()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        # Connection / status
        top = ttk.Frame(outer)
        top.pack(fill="x")

        ttk.Label(top, text="Status:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="Stopped")
        self.status_label = ttk.Label(top, textvariable=self.status_var)
        self.status_label.pack(side="left", padx=(6, 18))

        ttk.Label(top, text="Character:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.character_var = tk.StringVar()
        ttk.Label(top, textvariable=self.character_var).pack(side="left", padx=(6, 18))

        ttk.Label(top, text="Area:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.area_var = tk.StringVar(value="—")
        ttk.Label(top, textvariable=self.area_var).pack(side="left", padx=(6, 0))

        # API key
        api_frame = ttk.LabelFrame(outer, text="OpenAI", padding=10)
        api_frame.pack(fill="x", pady=(12, 8))

        ttk.Label(api_frame, text="API key:").grid(row=0, column=0, sticky="w")
        self.api_key_var = tk.StringVar()
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="•")
        self.api_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            api_frame,
            text="Show",
            variable=self.show_key_var,
            command=self._toggle_key_visibility,
        ).grid(row=0, column=2, sticky="e")
        api_frame.columnconfigure(1, weight=1)

        ttk.Label(
            api_frame,
            text="If OPENAI_API_KEY is already set in Windows, you can leave this blank.",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))

        # Guidance
        guide_frame = ttk.LabelFrame(outer, text="Guidance for the next AI reply", padding=10)
        guide_frame.pack(fill="x", pady=(0, 8))

        self.guidance_text = tk.Text(guide_frame, height=5, wrap="word", undo=True)
        self.guidance_text.pack(fill="x")
        self.guidance_text.bind("<<Modified>>", self._on_guidance_modified)

        guide_buttons = ttk.Frame(guide_frame)
        guide_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(guide_buttons, text="Set Guidance", command=self.set_guidance).pack(side="left")
        ttk.Button(guide_buttons, text="Clear Guidance", command=self.clear_guidance).pack(side="left", padx=(8, 0))
        self.guide_status_var = tk.StringVar(value="No guidance queued.")
        ttk.Label(guide_buttons, textvariable=self.guide_status_var).pack(side="left", padx=(14, 0))

        ttk.Label(
            guide_frame,
            text="One-shot: the guidance is cleared after the next successful AI generation. Ctrl+Enter also sets it.",
        ).pack(anchor="w", pady=(6, 0))
        self.guidance_text.bind("<Control-Return>", self._ctrl_enter_guidance)

        # Main controls
        controls = ttk.LabelFrame(outer, text="Controls", padding=10)
        controls.pack(fill="x", pady=(0, 8))

        row1 = ttk.Frame(controls)
        row1.pack(fill="x")
        self.start_btn = ttk.Button(row1, text="Start", command=self.start_bot)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(row1, text="Stop", command=self.stop_bot, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        self.pause_btn = ttk.Button(row1, text="Pause Listening (F6)", command=self.toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", padx=(18, 0))

        self.auto_btn = ttk.Button(row1, text="Auto Reply OFF (F10)", command=self.toggle_auto, state="disabled")
        self.auto_btn.pack(side="left", padx=(8, 0))

        row2 = ttk.Frame(controls)
        row2.pack(fill="x", pady=(8, 0))

        self.draft_btn = ttk.Button(row2, text="Draft in Activity Log (F8)", command=self.generate_draft, state="disabled")
        self.draft_btn.pack(side="left")

        self.f9_btn = ttk.Button(row2, text="F9 → Draft into NWN Chat", command=self.generate_to_nwn, state="disabled")
        self.f9_btn.pack(side="left", padx=(8, 0))

        self.clear_btn = ttk.Button(row2, text="Clear Conversation (F11)", command=self.clear_context, state="disabled")
        self.clear_btn.pack(side="left", padx=(8, 0))

        self.test_btn = ttk.Button(row2, text="Keyboard Test", command=self.keyboard_test, state="disabled")
        self.test_btn.pack(side="left", padx=(8, 0))

        ttk.Label(
            controls,
            text="F9 behavior: AI generates → 2-second countdown → click NWN → draft is pasted but NOT sent. Edit it, then press Enter yourself.",
            wraplength=760,
        ).pack(anchor="w", pady=(9, 0))

        # Conversation/activity
        activity = ttk.LabelFrame(outer, text="Activity / Conversation", padding=8)
        activity.pack(fill="both", expand=True)

        self.log_text = tk.Text(activity, height=16, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(activity, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(8, 0))
        self.context_var = tk.StringVar(value="Context messages: 0")
        ttk.Label(bottom, textvariable=self.context_var).pack(side="left")
        ttk.Button(bottom, text="Clear Activity Display", command=self.clear_activity_display).pack(side="right")

    def _load_initial_values(self):
        self.character_var.set(self.settings.get("character_name", "Unknown"))
        env_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if env_key:
            self.api_key_var.set("")
        current_guide = core.read_shared_guidance()
        self.last_guidance_file_value = current_guide
        if current_guide:
            self.guidance_text.insert("1.0", current_guide)
            self.guidance_text.edit_modified(False)
            self.guide_status_var.set("Guidance queued.")
        self._append_log("UI ready. Click Start to begin watching the NWN log.")

    def _toggle_key_visibility(self):
        self.api_entry.configure(show="" if self.show_key_var.get() else "•")

    def _on_guidance_modified(self, event=None):
        if self.guidance_text.edit_modified():
            self.guidance_dirty = True
            self.guidance_text.edit_modified(False)

    def _ctrl_enter_guidance(self, event=None):
        self.set_guidance()
        return "break"

    def set_guidance(self):
        value = self.guidance_text.get("1.0", "end").strip()
        if core.write_shared_guidance(value):
            if self.bot:
                self.bot.next_guidance = value
            self.last_guidance_file_value = value
            self.guidance_dirty = False
            self.guide_status_var.set("Guidance queued." if value else "No guidance queued.")
            self._append_log("[GUIDE] Guidance set for next reply.")

    def clear_guidance(self):
        core.clear_shared_guidance()
        if self.bot:
            self.bot.next_guidance = ""
        self.guidance_text.delete("1.0", "end")
        self.guidance_text.edit_modified(False)
        self.guidance_dirty = False
        self.last_guidance_file_value = ""
        self.guide_status_var.set("No guidance queued.")
        self._append_log("[GUIDE] Guidance cleared.")

    def _effective_api_key(self):
        return self.api_key_var.get().strip() or os.environ.get("OPENAI_API_KEY", "").strip()

    def start_bot(self):
        if self.running:
            return

        api_key = self._effective_api_key()
        if not api_key:
            messagebox.showerror(
                "OpenAI API key required",
                "Enter an OpenAI API key or set OPENAI_API_KEY in Windows before starting.",
            )
            return

        try:
            self.settings = core.load_settings()
            self.character_prompt = core.load_character_prompt()
            client = OpenAI(api_key=api_key)
            self.bot = core.NWNAIBot(self.settings, self.character_prompt, client)
            self.bot.next_guidance = core.read_shared_guidance()

            threading.Thread(target=self.bot.action_worker, daemon=True).start()
            self.hotkeys = self.bot.hotkey_listener()

            self.running = True
            self._set_running_controls(True)
            self.status_var.set("Running")
            self._append_log(f"[START] Watching: {self.settings['log_path']}")
            self._append_log("[HOTKEYS] F6 pause, F8 draft, F9 NWN draft, F10 auto, F11 clear, F12 stop.")

            self.bot_thread = threading.Thread(target=self._log_loop, daemon=True)
            self.bot_thread.start()

        except Exception as exc:
            self.running = False
            self.bot = None
            messagebox.showerror("Start failed", f"{type(exc).__name__}: {exc}")
            self._append_log(traceback.format_exc())

    def _log_loop(self):
        follower = core.LogFollower(
            self.settings["log_path"],
            float(self.settings["poll_interval_seconds"]),
        )
        try:
            for line in follower.lines(self.bot.stop_event):
                if not self.bot or self.bot.stop_event.is_set():
                    break

                self.bot.add_system_event(line)

                event = core.parse_chat_line(
                    line,
                    self.settings["character_name"],
                )
                if not event:
                    continue

                if self.bot.should_suppress_duplicate_self(event):
                    try:
                        self.bot.context.pop()
                    except IndexError:
                        pass

                self.bot.add_chat_event(event)

        except Exception:
            self.output_queue.put("[LOG ERROR] " + traceback.format_exc())
        finally:
            self.output_queue.put("[STATE] BOT_LOOP_STOPPED")

    def stop_bot(self):
        if not self.bot:
            return
        self._append_log("[STOP] Stopping...")
        self.bot.stop_event.set()
        try:
            if self.hotkeys:
                self.hotkeys.stop()
        except Exception:
            pass
        self.running = False
        self._set_running_controls(False)
        self.status_var.set("Stopped")

    def _set_running_controls(self, running):
        normal = "normal" if running else "disabled"
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state=normal)
        self.pause_btn.configure(state=normal)
        self.auto_btn.configure(state=normal)
        self.draft_btn.configure(state=normal)
        self.f9_btn.configure(state=normal)
        self.clear_btn.configure(state=normal)
        self.test_btn.configure(state=normal)

    def toggle_pause(self):
        if self.bot:
            self.bot.action_queue.put(("toggle_pause", "ui"))

    def toggle_auto(self):
        if self.bot:
            self.bot.action_queue.put(("toggle_auto", "ui"))

    def generate_draft(self):
        if self.bot:
            self.set_guidance_if_changed()
            self.bot.action_queue.put(("suggest", "ui"))

    def generate_to_nwn(self):
        if self.bot:
            self.set_guidance_if_changed()
            self._append_log("[F9] Generating. Be ready to click NWN during the 2-second countdown.")
            self.bot.action_queue.put(("generate_and_send", "manual"))

    def clear_context(self):
        if self.bot:
            self.bot.action_queue.put(("clear", "ui"))

    def keyboard_test(self):
        if self.bot:
            self._append_log("[TEST] Click NWN when instructed.")
            self.bot.action_queue.put(("manual_keyboard_test", "ui"))

    def set_guidance_if_changed(self):
        if self.guidance_dirty:
            self.set_guidance()

    def clear_activity_display(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _append_log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", str(line) + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _poll_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line == "[STATE] BOT_LOOP_STOPPED":
                    if self.running:
                        self.running = False
                        self._set_running_controls(False)
                        self.status_var.set("Stopped")
                    continue
                self._append_log(line)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_output)

    def _poll_bot_state(self):
        if self.bot:
            try:
                self.area_var.set(self.bot.current_area or "—")
                self.context_var.set(f"Context messages: {len(self.bot.context)}")

                if self.bot.paused:
                    self.pause_btn.configure(text="Resume Listening (F6)")
                else:
                    self.pause_btn.configure(text="Pause Listening (F6)")

                self.auto_btn.configure(
                    text="Auto Reply ON (F10)" if self.bot.auto_reply else "Auto Reply OFF (F10)"
                )

                if self.bot.stop_event.is_set() and self.running:
                    self.running = False
                    self._set_running_controls(False)
                    self.status_var.set("Stopped")
            except Exception:
                pass
        self.root.after(250, self._poll_bot_state)

    def _poll_guidance_file(self):
        try:
            value = core.read_shared_guidance()
            # Do not overwrite text the user is actively editing. But when the
            # bot consumes queued guidance, clear the box automatically.
            if value != self.last_guidance_file_value:
                if value == "":
                    self.guidance_text.delete("1.0", "end")
                    self.guidance_text.edit_modified(False)
                    self.guidance_dirty = False
                    self.guide_status_var.set("No guidance queued.")
                    self.last_guidance_file_value = ""
                elif not self.guidance_dirty:
                    self.guidance_text.delete("1.0", "end")
                    self.guidance_text.insert("1.0", value)
                    self.guidance_text.edit_modified(False)
                    self.guide_status_var.set("Guidance queued.")
                    self.last_guidance_file_value = value
        except Exception:
            pass
        self.root.after(500, self._poll_guidance_file)

    def on_close(self):
        try:
            self.stop_bot()
        finally:
            self.root.destroy()


def main():
    if os.name != "nt":
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Windows required", "This build is intended for Windows.")
        root.destroy()
        return

    root = tk.Tk()
    app = NWNAIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
