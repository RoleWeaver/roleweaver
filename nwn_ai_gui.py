import os
import ctypes
import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

import nwn_ai_bot as core


RESOURCE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = RESOURCE_DIR / "assets"


def apply_windows_app_identity(root):
    """Use Role Weaver branding in the title bar, taskbar and Alt-Tab."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "RoleWeaver.NWN.RPClient"
        )
    except Exception:
        pass

    try:
        ico = ASSETS_DIR / "RoleWeaver.ico"
        if ico.exists():
            root.iconbitmap(default=str(ico))
    except Exception:
        pass

    try:
        png = ASSETS_DIR / "role_weaver_icon.png"
        if png.exists():
            root._role_weaver_icon = tk.PhotoImage(file=str(png))
            root.iconphoto(True, root._role_weaver_icon)
    except Exception:
        pass


def show_splash(root, duration_ms=1400):
    """Small startup splash. Click it to dismiss immediately."""
    splash_path = ASSETS_DIR / "role_weaver_splash.png"
    if not splash_path.exists():
        return

    root.withdraw()
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg="#111318")

    try:
        photo = tk.PhotoImage(file=str(splash_path))
    except Exception:
        splash.destroy()
        return

    splash._photo = photo
    label = tk.Label(
        splash,
        image=photo,
        bd=0,
        highlightthickness=0,
        bg="#111318",
    )
    label.pack()

    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    width = photo.width()
    height = photo.height()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")

    def close_splash(event=None):
        try:
            splash.destroy()
        except Exception:
            pass

    splash.bind("<Button-1>", close_splash)
    label.bind("<Button-1>", close_splash)
    splash.after(duration_ms, close_splash)
    splash.update_idletasks()
    root.wait_window(splash)


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
        apply_windows_app_identity(self.root)
        self.root.title("Role Weaver: NWN RP Client")
        self.root.geometry("1240x800")
        self.root.minsize(1040, 700)
        self.root.configure(bg="#313338")

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", font=("Segoe UI", 9))
        style.configure("TFrame", background="#313338")
        style.configure("Sidebar.TFrame", background="#2b2d31")
        style.configure("Content.TFrame", background="#313338")
        style.configure("TLabel", background="#313338", foreground="#dbdee1")
        style.configure("Sidebar.TLabel", background="#2b2d31", foreground="#dbdee1")
        style.configure("TLabelframe", background="#2b2d31", foreground="#f2f3f5",
                        bordercolor="#1e1f22", relief="flat")
        style.configure("TLabelframe.Label", background="#2b2d31", foreground="#f2f3f5",
                        font=("Segoe UI", 9, "bold"))
        style.configure("TButton", background="#4e5058", foreground="#f2f3f5",
                        borderwidth=0, padding=(8, 5))
        style.map("TButton",
                  background=[("active", "#5c5e66"), ("pressed", "#404249"),
                              ("disabled", "#35373c")],
                  foreground=[("disabled", "#80848e")])
        style.configure("Accent.TButton", background="#5865f2", foreground="#ffffff",
                        borderwidth=0, padding=(8, 5))
        style.map("Accent.TButton",
                  background=[("active", "#4752c4"), ("pressed", "#3c45a5")])
        style.configure("Nav.TButton", background="#232428", foreground="#b5bac1",
                        borderwidth=1, relief="flat", padding=(10, 10), anchor="w")
        style.map("Nav.TButton",
                  background=[("active", "#35373c"), ("pressed", "#404249")],
                  foreground=[("active", "#ffffff")])
        style.configure("NavSelected.TButton", background="#5865f2", foreground="#ffffff",
                        borderwidth=1, relief="flat", padding=(10, 10), anchor="w")
        style.configure("Locked.TButton", background="#3a3c43", foreground="#777c86",
                        borderwidth=1, relief="flat", padding=(10, 10), anchor="w")
        style.map("NavSelected.TButton",
                  background=[("active", "#5865f2"), ("pressed", "#4752c4")])
        style.configure("SettingsTitle.TLabel", background="#2b2d31", foreground="#949ba4",
                        font=("Segoe UI", 8, "bold"))
        style.configure("TEntry", fieldbackground="#1e1f22", foreground="#dbdee1",
                        insertcolor="#dbdee1", bordercolor="#1e1f22", lightcolor="#1e1f22",
                        darkcolor="#1e1f22")
        style.configure("TCombobox", fieldbackground="#1e1f22", foreground="#dbdee1",
                        background="#1e1f22", arrowcolor="#b5bac1", bordercolor="#1e1f22")
        style.map("TCombobox", fieldbackground=[("readonly", "#1e1f22")],
                  foreground=[("readonly", "#dbdee1")])
        style.configure("Vertical.TScrollbar", background="#2b2d31", troughcolor="#1e1f22",
                        arrowcolor="#b5bac1", bordercolor="#1e1f22")

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
        self.last_seen_draft_version = -1
        self.last_seen_ai_context_version = -1
        self.last_relationship_names = ()
        self.context_event_lookup = {}
        self.last_context_event_signature = None
        self.last_seen_candidate_version = -1

        self.settings = core.load_settings()
        self.character_prompt = ""

        self._build_ui()
        self._load_initial_values()
        self._poll_output()
        self._poll_bot_state()
        self._poll_guidance_file()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=8)
        outer.pack(fill="both", expand=True)

        # Draggable split: users can resize the control/settings side and the
        # Activity / Conversation area at any time.
        main_split = tk.PanedWindow(
            outer,
            orient="horizontal",
            sashwidth=7,
            sashrelief="flat",
            bg="#1e1f22",
            bd=0,
            relief="flat",
        )
        main_split.pack(fill="both", expand=True)

        left = ttk.Frame(main_split, width=455, style="Sidebar.TFrame")
        right = ttk.Frame(main_split, style="Content.TFrame")

        main_split.add(left, minsize=390, width=455, stretch="never")
        main_split.add(right, minsize=500, stretch="always")

        # Initial split position. The sash remains draggable.
        self.root.after_idle(lambda: main_split.sash_place(0, 455, 0))

        # Connection / status
        top = ttk.Frame(left, style="Sidebar.TFrame")
        top.pack(fill="x", padx=8, pady=(6, 4))

        ttk.Label(top, text="Status:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="Stopped")
        self.status_label = ttk.Label(top, textvariable=self.status_var)
        self.status_label.pack(side="left", padx=(4, 10))

        ttk.Label(top, text="Character:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.character_var = tk.StringVar(value="Unknown")
        ttk.Label(top, textvariable=self.character_var).pack(side="left", padx=(4, 10))

        ttk.Label(top, text="Area:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.area_var = tk.StringVar(value="—")
        ttk.Label(top, textvariable=self.area_var).pack(side="left", padx=(4, 0))

        # Vertical settings tabs. Only one settings panel is visible at a time.
        settings_shell = ttk.Frame(left, style="Sidebar.TFrame", height=275)
        settings_shell.pack(fill="x", padx=8, pady=(4, 8))
        settings_shell.pack_propagate(False)

        settings_nav = ttk.Frame(settings_shell, width=112, style="Sidebar.TFrame")
        settings_nav.pack(side="left", fill="y", padx=(0, 8))
        settings_nav.pack_propagate(False)

        ttk.Label(
            settings_nav, text="SETTINGS", style="SettingsTitle.TLabel"
        ).pack(fill="x", padx=(3, 0), pady=(0, 6))

        settings_panel_host = ttk.Frame(settings_shell, style="Sidebar.TFrame")
        settings_panel_host.pack(side="left", fill="both", expand=True)
        self.settings_lock_var = tk.StringVar(value="")
        ttk.Label(
            left,
            textvariable=self.settings_lock_var,
            style="Sidebar.TLabel",
            foreground="#f0b232",
        ).pack(fill="x", padx=10, pady=(0, 4))

        self._settings_frames = {}
        self._settings_nav_buttons = {}

        def show_settings_panel(name):
            if self.running:
                return

            for frame in self._settings_frames.values():
                frame.pack_forget()
            frame = self._settings_frames[name]
            frame.pack(fill="both", expand=True)

            for key, button in self._settings_nav_buttons.items():
                button.configure(style="NavSelected.TButton" if key == name else "Nav.TButton")

        self._show_settings_panel = show_settings_panel

        # Character profile
        character_frame = ttk.LabelFrame(settings_panel_host, text="Character Profile", padding=8)
        self._settings_frames["Character"] = character_frame

        ttk.Label(character_frame, text="Prompt file:").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.character_profile_var = tk.StringVar()
        self.character_profile_combo = ttk.Combobox(
            character_frame,
            textvariable=self.character_profile_var,
            state="readonly",
            width=38,
        )
        self.character_profile_combo.grid(
            row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 6)
        )
        self.character_profile_combo.bind("<<ComboboxSelected>>", self._on_character_profile_changed)

        self.refresh_profiles_btn = ttk.Button(
            character_frame,
            text="Refresh",
            command=self._refresh_character_profiles,
        )
        self.refresh_profiles_btn.grid(row=1, column=1, sticky="e", pady=(5, 0))

        self.character_file_display_var = tk.StringVar(value="")
        ttk.Label(
            character_frame,
            textvariable=self.character_file_display_var,
            style="Sidebar.TLabel",
            wraplength=310,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(7, 0))

        ttk.Label(
            character_frame,
            text="Profiles are server-specific under Characters/<server>/. Character name is read from Name: or Character Name:.",
            wraplength=310,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 0))
        character_frame.columnconfigure(0, weight=1)

        # Server / log profile
        server_frame = ttk.LabelFrame(settings_panel_host, text="Server and Log", padding=8)
        self._settings_frames["Server / Log"] = server_frame
        ttk.Label(server_frame, text="Server:").grid(row=0, column=0, sticky="w")
        self.server_var = tk.StringVar()
        self.server_combo = ttk.Combobox(
            server_frame, textvariable=self.server_var, state="readonly",
            values=[core.SERVER_PROFILES["TDN"]["display_name"], core.SERVER_PROFILES["Arelith"]["display_name"]],
            width=26,
        )
        self.server_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.server_combo.bind("<<ComboboxSelected>>", self._on_server_changed)

        ttk.Label(server_frame, text="Log file:").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(9, 0)
        )
        self.log_path_var = tk.StringVar()
        self.log_path_entry = ttk.Entry(server_frame, textvariable=self.log_path_var)
        self.log_path_entry.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0)
        )
        self.browse_btn = ttk.Button(server_frame, text="Browse...", command=self._browse_log_file)
        self.browse_btn.grid(row=3, column=0, sticky="w", pady=(7, 0))
        server_frame.columnconfigure(1, weight=1)

        # AI provider
        ai_frame = ttk.LabelFrame(settings_panel_host, text="AI Provider", padding=8)
        self._settings_frames["AI Provider"] = ai_frame

        ttk.Label(ai_frame, text="Provider:").grid(row=0, column=0, sticky="w")
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(
            ai_frame,
            textvariable=self.provider_var,
            state="readonly",
            values=list(core.AI_PROVIDERS.keys()),
            width=20,
        )
        self.provider_combo.grid(row=0, column=1, sticky="w", padx=(8, 14))
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        ttk.Label(ai_frame, text="Model:").grid(row=0, column=2, sticky="w")
        self.model_var = tk.StringVar()
        self.model_entry = ttk.Entry(ai_frame, textvariable=self.model_var, width=22)
        self.model_entry.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        self.api_key_label = ttk.Label(ai_frame, text="API key:")
        self.api_key_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.api_key_var = tk.StringVar()
        self.api_entry = ttk.Entry(ai_frame, textvariable=self.api_key_var, show="•")
        self.api_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 8), pady=(8, 0))
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_btn = ttk.Checkbutton(
            ai_frame, text="Show", variable=self.show_key_var, command=self._toggle_key_visibility
        )
        self.show_key_btn.grid(row=1, column=3, sticky="w", pady=(8, 0))

        self.lm_url_label = ttk.Label(ai_frame, text="LM Studio URL:")
        self.lm_url_var = tk.StringVar(value="http://localhost:1234/v1")
        self.lm_url_entry = ttk.Entry(ai_frame, textvariable=self.lm_url_var)

        self.provider_hint_var = tk.StringVar()
        ttk.Label(ai_frame, textvariable=self.provider_hint_var, wraplength=310).grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(7, 0)
        )

        self.test_ai_btn = ttk.Button(ai_frame, text="Test AI Connection", command=self.test_ai_connection)
        self.test_ai_btn.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Label(
            ai_frame,
            text="Provider, model and response length are saved per server-specific character profile.",
            wraplength=310,
        ).grid(row=5, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ai_frame.columnconfigure(3, weight=1)
        self._settings_nav_buttons["Character"] = ttk.Button(
            settings_nav, text="▌ Character", style="NavSelected.TButton",
            command=lambda: self._show_settings_panel("Character")
        )
        self._settings_nav_buttons["Character"].pack(fill="x", pady=(0, 3))

        self._settings_nav_buttons["Server / Log"] = ttk.Button(
            settings_nav, text="▌ Server / Log", style="Nav.TButton",
            command=lambda: self._show_settings_panel("Server / Log")
        )
        self._settings_nav_buttons["Server / Log"].pack(fill="x", pady=(0, 3))

        self._settings_nav_buttons["AI Provider"] = ttk.Button(
            settings_nav, text="▌ AI Provider", style="Nav.TButton",
            command=lambda: self._show_settings_panel("AI Provider")
        )
        self._settings_nav_buttons["AI Provider"].pack(fill="x")

        self._show_settings_panel("Character")

        # Guidance
        guide_frame = ttk.LabelFrame(left, text="Guidance for next AI reply", padding=8)
        guide_frame.pack(fill="x", padx=8, pady=(0, 7))

        self.guidance_text = tk.Text(
            guide_frame, height=4, wrap="word", undo=True,
            bg="#1e1f22", fg="#dbdee1", insertbackground="#dbdee1",
            selectbackground="#5865f2", selectforeground="#ffffff",
            relief="flat", bd=0, padx=7, pady=6
        )
        self.guidance_text.pack(fill="x")
        self.guidance_text.bind("<<Modified>>", self._on_guidance_modified)

        guide_buttons = ttk.Frame(guide_frame)
        guide_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(guide_buttons, text="Set Guidance", command=self.set_guidance).pack(side="left")
        ttk.Button(guide_buttons, text="Clear Guidance", command=self.clear_guidance).pack(side="left", padx=(8, 0))
        self.guide_status_var = tk.StringVar(value="No guidance active.")
        ttk.Label(guide_buttons, textvariable=self.guide_status_var).pack(side="left", padx=(14, 0))

        ttk.Label(
            guide_frame,
            text="One-shot: cleared after the next successful generation. Ctrl+Enter sets it.",
            wraplength=315,
        ).pack(anchor="w", pady=(6, 0))
        self.guidance_text.bind("<Control-Return>", self._ctrl_enter_guidance)

        # Main controls
        controls = ttk.LabelFrame(left, text="Controls", padding=8)
        controls.pack(fill="x", padx=8, pady=(0, 7))

        row1 = ttk.Frame(controls)
        row1.pack(fill="x")
        self.start_btn = ttk.Button(
            row1, text="Start", command=self.start_bot, style="Accent.TButton"
        )
        self.start_btn.pack(side="left", fill="x", expand=True)

        self.stop_btn = ttk.Button(
            row1, text="Stop", command=self.stop_bot, state="disabled"
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.pause_btn = ttk.Button(
            row1, text="Pause (F6)", command=self.toggle_pause, state="disabled"
        )
        self.pause_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        row2 = ttk.Frame(controls)
        row2.pack(fill="x", pady=(7, 0))

        self.auto_btn = ttk.Button(
            row2, text="Auto Reply OFF (F10)", command=self.toggle_auto, state="disabled"
        )
        self.auto_btn.pack(side="left", fill="x", expand=True)

        self.draft_btn = ttk.Button(
            row2, text="3 Drafts (F8)", command=self.generate_draft, state="disabled"
        )
        self.draft_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.f9_btn = ttk.Button(
            row2,
            text="Draft into NWN (F9)",
            command=self.generate_to_nwn,
            state="disabled",
            style="Accent.TButton",
        )
        self.f9_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        row3 = ttk.Frame(controls)
        row3.pack(fill="x", pady=(7, 0))

        self.clear_btn = ttk.Button(
            row3,
            text="Clear Conversation (F11)",
            command=self.clear_context,
            state="disabled",
        )
        self.clear_btn.pack(side="left", fill="x", expand=True)

        self.test_btn = ttk.Button(
            row3, text="Keyboard Test", command=self.keyboard_test, state="disabled"
        )
        self.test_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        ttk.Label(
            controls,
            text="F9 generates, waits 2 seconds, then pastes an editable draft into NWN.",
            wraplength=320,
        ).pack(anchor="w", pady=(8, 0))

        # Conversation/activity and lower workspace are separated by a draggable sash.
        right_split = tk.PanedWindow(
            right,
            orient="vertical",
            sashwidth=7,
            sashrelief="flat",
            bg="#1e1f22",
            bd=0,
            relief="flat",
        )
        right_split.pack(fill="both", expand=True)

        activity = ttk.LabelFrame(right_split, text="Activity / Conversation", padding=7)
        lower_workspace = ttk.Frame(right_split)

        # Activity starts smaller so the draft workspace is immediately visible.
        right_split.add(activity, minsize=150, height=285, stretch="always")
        right_split.add(lower_workspace, minsize=250, height=390, stretch="always")
        self.root.after_idle(lambda: right_split.sash_place(0, 0, 285))

        self.log_text = tk.Text(
            activity,
            width=74,
            height=16,
            wrap="word",
            state="disabled",
            bg="#1e1f22",
            fg="#dbdee1",
            insertbackground="#dbdee1",
            selectbackground="#5865f2",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            font=("Segoe UI", 10),
        )
        scroll = ttk.Scrollbar(activity, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Lower workspace tabs: Draft, exact AI Context, and persistent Relationships.
        lower_tabs = ttk.Notebook(lower_workspace)
        lower_tabs.pack(fill="both", expand=True)

        draft_frame = ttk.Frame(lower_tabs, padding=7)
        context_frame = ttk.Frame(lower_tabs, padding=7)
        relationship_frame = ttk.Frame(lower_tabs, padding=7)
        history_frame = ttk.Frame(lower_tabs, padding=7)
        lower_tabs.add(draft_frame, text="AI Draft")
        lower_tabs.add(context_frame, text="AI Context")
        lower_tabs.add(relationship_frame, text="Relationships")
        lower_tabs.add(history_frame, text="History")

        candidate_bar = ttk.Frame(draft_frame)
        candidate_bar.pack(fill="x", pady=(0, 6))
        ttk.Label(candidate_bar, text="Candidates:").pack(side="left")
        self.candidate_var = tk.StringVar(value="Candidate 1")
        self.candidate_combo = ttk.Combobox(
            candidate_bar,
            textvariable=self.candidate_var,
            state="readonly",
            width=18,
            values=[],
        )
        self.candidate_combo.pack(side="left", padx=(7, 0))
        self.candidate_combo.bind("<<ComboboxSelected>>", self._select_candidate)
        self.length_mode_var = tk.StringVar(value="Auto")
        ttk.Label(candidate_bar, text="Response length:").pack(side="left", padx=(18, 0))
        self.length_mode_combo = ttk.Combobox(
            candidate_bar,
            textvariable=self.length_mode_var,
            state="readonly",
            width=11,
            values=["Auto", "Brief", "Normal", "Detailed"],
        )
        self.length_mode_combo.pack(side="left", padx=(7, 0))
        self.length_mode_combo.bind("<<ComboboxSelected>>", self._on_length_mode_changed)

        self.ai_draft_text = tk.Text(
            draft_frame,
            height=8,
            wrap="word",
            undo=True,
            bg="#1e1f22",
            fg="#dbdee1",
            insertbackground="#dbdee1",
            selectbackground="#5865f2",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=7,
            font=("Segoe UI", 10),
        )
        self.ai_draft_text.pack(fill="both", expand=True)

        draft_buttons = ttk.Frame(draft_frame)
        draft_buttons.pack(fill="x", pady=(7, 0))

        self.regenerate_btn = ttk.Button(
            draft_buttons, text="Regenerate", command=self.regenerate_draft, state="disabled"
        )
        self.regenerate_btn.pack(side="left")
        self.shorter_btn = ttk.Button(
            draft_buttons, text="Shorter", command=self.shorter_draft, state="disabled"
        )
        self.shorter_btn.pack(side="left", padx=(6, 0))
        self.longer_btn = ttk.Button(
            draft_buttons, text="Longer", command=self.longer_draft, state="disabled"
        )
        self.longer_btn.pack(side="left", padx=(6, 0))
        self.clear_draft_btn = ttk.Button(
            draft_buttons, text="Clear", command=self.clear_ai_draft, state="disabled"
        )
        self.clear_draft_btn.pack(side="right", padx=(6, 0))
        self.paste_draft_btn = ttk.Button(
            draft_buttons,
            text="Paste Edited Draft into NWN",
            command=self.paste_current_draft,
            state="disabled",
            style="Accent.TButton",
        )
        self.paste_draft_btn.pack(side="right")

        # Exact content used in the latest AI reply request. Read-only.
        ttk.Label(
            context_frame,
            text="Shows the exact character instructions and contextual content used for the latest reply generation.",
            wraplength=620,
        ).pack(anchor="w", pady=(0, 6))
        context_text_host = ttk.Frame(context_frame)
        context_text_host.pack(fill="both", expand=True)
        self.ai_context_text = tk.Text(
            context_text_host,
            wrap="word",
            state="disabled",
            bg="#1e1f22",
            fg="#dbdee1",
            insertbackground="#dbdee1",
            selectbackground="#5865f2",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=7,
            font=("Consolas", 9),
        )
        context_scroll = ttk.Scrollbar(
            context_text_host, orient="vertical", command=self.ai_context_text.yview
        )
        self.ai_context_text.configure(yscrollcommand=context_scroll.set)
        self.ai_context_text.pack(side="left", fill="both", expand=True)
        context_scroll.pack(side="right", fill="y")

        context_controls = ttk.LabelFrame(context_frame, text="Manual Context Controls", padding=6)
        context_controls.pack(fill="x", pady=(7, 0))

        self.context_event_var = tk.StringVar()
        self.context_event_combo = ttk.Combobox(
            context_controls,
            textvariable=self.context_event_var,
            state="readonly",
            width=66,
        )
        self.context_event_combo.pack(fill="x")

        context_button_row = ttk.Frame(context_controls)
        context_button_row.pack(fill="x", pady=(6, 0))

        self.ignore_context_btn = ttk.Button(
            context_button_row,
            text="Ignore / Unignore",
            command=self.toggle_ignore_selected_context,
            state="disabled",
        )
        self.ignore_context_btn.pack(side="left")

        self.pin_context_btn = ttk.Button(
            context_button_row,
            text="Remember / Unremember",
            command=self.toggle_pin_selected_context,
            state="disabled",
        )
        self.pin_context_btn.pack(side="left", padx=(6, 0))

        self.forget_before_btn = ttk.Button(
            context_button_row,
            text="Forget Before Here",
            command=self.forget_before_selected_context,
            state="disabled",
        )
        self.forget_before_btn.pack(side="left", padx=(6, 0))

        ttk.Label(
            context_controls,
            text="OOC is detected from ((...)), parenthetical OOC lines, //, and OOC: prefixes. "
                 "OOC lines remain visible in history but are excluded from AI context by default.",
            wraplength=650,
        ).pack(anchor="w", pady=(6, 0))

        # Persistent relationship editor.
        relationship_top = ttk.Frame(relationship_frame)
        relationship_top.pack(fill="x")
        ttk.Label(relationship_top, text="Character:").pack(side="left")
        self.relationship_character_var = tk.StringVar()
        self.relationship_character_combo = ttk.Combobox(
            relationship_top,
            textvariable=self.relationship_character_var,
            state="readonly",
            width=32,
        )
        self.relationship_character_combo.pack(side="left", padx=(7, 0))
        self.relationship_character_combo.bind(
            "<<ComboboxSelected>>", self._load_relationship_record
        )

        ttk.Label(relationship_frame, text="Relationship / attitude:").pack(
            anchor="w", pady=(9, 3)
        )
        self.relationship_text = tk.Text(
            relationship_frame,
            height=3,
            wrap="word",
            bg="#1e1f22",
            fg="#dbdee1",
            insertbackground="#dbdee1",
            selectbackground="#5865f2",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            font=("Segoe UI", 10),
        )
        self.relationship_text.pack(fill="x")

        ttk.Label(relationship_frame, text="Persistent memory notes:").pack(
            anchor="w", pady=(8, 3)
        )
        self.relationship_memory_text = tk.Text(
            relationship_frame,
            height=5,
            wrap="word",
            bg="#1e1f22",
            fg="#dbdee1",
            insertbackground="#dbdee1",
            selectbackground="#5865f2",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            font=("Segoe UI", 10),
        )
        self.relationship_memory_text.pack(fill="both", expand=True)

        rel_buttons = ttk.Frame(relationship_frame)
        rel_buttons.pack(fill="x", pady=(7, 0))
        self.save_relationship_btn = ttk.Button(
            rel_buttons,
            text="Save Relationship / Memory",
            command=self.save_relationship_record,
            state="disabled",
            style="Accent.TButton",
        )
        self.save_relationship_btn.pack(side="right")

        # Conversation history viewer.
        history_tools = ttk.Frame(history_frame)
        history_tools.pack(fill="x", pady=(0, 6))
        self.history_file_var = tk.StringVar()
        self.history_file_combo = ttk.Combobox(
            history_tools, textvariable=self.history_file_var, state="readonly", width=30
        )
        self.history_file_combo.pack(side="left")
        self.history_file_combo.bind("<<ComboboxSelected>>", self._load_selected_history)
        ttk.Button(history_tools, text="Refresh", command=self._refresh_history_files).pack(side="left", padx=(6,0))
        ttk.Label(history_tools, text="Find:").pack(side="left", padx=(14,4))
        self.history_search_var = tk.StringVar()
        history_search = ttk.Entry(history_tools, textvariable=self.history_search_var, width=20)
        history_search.pack(side="left", fill="x", expand=True)
        history_search.bind("<Return>", self._search_history)
        ttk.Button(history_tools, text="Find Next", command=self._search_history).pack(side="left", padx=(6,0))

        history_host = ttk.Frame(history_frame)
        history_host.pack(fill="both", expand=True)
        self.history_text = tk.Text(
            history_host, wrap="word", state="disabled",
            bg="#1e1f22", fg="#dbdee1", insertbackground="#dbdee1",
            selectbackground="#5865f2", selectforeground="#ffffff",
            relief="flat", bd=0, padx=8, pady=7, font=("Consolas", 9),
        )
        history_scroll = ttk.Scrollbar(history_host, orient="vertical", command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=history_scroll.set)
        self.history_text.pack(side="left", fill="both", expand=True)
        history_scroll.pack(side="right", fill="y")

        bottom = ttk.Frame(right)
        bottom.pack(fill="x", pady=(6, 0))
        self.context_var = tk.StringVar(value="Context messages: 0")
        ttk.Label(bottom, textvariable=self.context_var).pack(side="left")
        self.timing_var = tk.StringVar(value="AI: —")
        ttk.Label(bottom, textvariable=self.timing_var).pack(side="left", padx=(14, 0))
        ttk.Label(
            bottom,
            text="Drag either divider to resize panels",
            foreground="#949ba4",
        ).pack(side="left", padx=(14, 0))
        ttk.Button(
            bottom, text="Clear Activity Display", command=self.clear_activity_display
        ).pack(side="right")

    def _load_initial_values(self):
        # Server must be selected before scanning character profiles because
        # profiles now live in server-specific folders.
        profile = self.settings.get("server_profile", "TDN")
        self.server_var.set(core.SERVER_PROFILES[profile]["display_name"])
        self.log_path_var.set(core.get_server_log_path(self.settings, profile))

        # Loading a profile also restores that character's AI/model/length settings.
        self._refresh_character_profiles(initial=True)

        # Fallback only when no character-specific value was loaded.
        provider = self.provider_var.get() or self.settings.get("ai_provider", "Google Gemini")
        if provider not in core.AI_PROVIDERS:
            provider = "Google Gemini"
        self.provider_var.set(provider)
        if not self.model_var.get().strip():
            self.model_var.set(
                self.settings.get("model")
                or core.AI_PROVIDERS[provider]["default_model"]
            )
        if not self.lm_url_var.get().strip():
            self.lm_url_var.set(
                self.settings.get("lm_studio_base_url", "http://127.0.0.1:1234")
            )
        if not self.length_mode_var.get().strip():
            self.length_mode_var.set(
                self.settings.get("response_length_mode", "Auto")
            )
        self._update_provider_ui()

        env_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if env_key:
            self.api_key_var.set("")

        current_guide = core.read_shared_guidance()
        self.last_guidance_file_value = current_guide
        if current_guide:
            self.guidance_text.insert("1.0", current_guide)
            self.guidance_text.edit_modified(False)
            self.guide_status_var.set("Guidance active until cleared.")
        self._append_log("UI ready. Click Start to begin watching the NWN log.")

    def _refresh_character_profiles(self, initial=False):
        profile = self._selected_server_profile() if hasattr(self, "server_var") else self.settings.get("server_profile", "TDN")
        profiles = core.list_character_profiles(profile)
        names = [p.name for p in profiles]
        self.character_profile_combo["values"] = names

        selected_map = self.settings.get("server_character_profiles", {})
        selected = selected_map.get(profile, "") or self.settings.get("character_profile_file", "")
        if selected and selected in names:
            target = selected
        elif names:
            target = names[0]
        else:
            target = ""

        if target:
            self.character_profile_var.set(target)
            self._load_selected_character_profile(save_setting=not initial)
        else:
            self.character_profile_var.set("")
            self.character_file_display_var.set("")
            self.character_var.set("No profile found")
            if not initial:
                self._append_log(f"[CHARACTER] No character_*.txt files found for {profile}.")

    def _current_character_profile_path(self):
        filename = self.character_profile_var.get().strip()
        if not filename:
            return None
        return core.resolve_character_profile(self._selected_server_profile(), filename)

    def _load_character_specific_ai_settings(self, path):
        if not path:
            return
        char_ai = core.load_character_ai_settings(path)
        provider = char_ai.get("ai_provider", "Google Gemini")
        if provider not in core.AI_PROVIDERS:
            provider = "Google Gemini"
        self.provider_var.set(provider)
        self.model_var.set(char_ai.get("model") or core.AI_PROVIDERS[provider]["default_model"])
        self.lm_url_var.set(char_ai.get("lm_studio_base_url", "http://127.0.0.1:1234/v1"))
        self.length_mode_var.set(char_ai.get("response_length_mode", "Auto"))
        self.settings["candidate_count"] = int(char_ai.get("candidate_count", 3))
        self._update_provider_ui()

    def _load_selected_character_profile(self, save_setting=True, load_ai_settings=True):
        filename = self.character_profile_var.get().strip()
        if hasattr(self, "character_file_display_var"):
            self.character_file_display_var.set(filename)
        if not filename:
            self.character_var.set("Unknown")
            return

        profile = self._selected_server_profile()
        path = core.resolve_character_profile(profile, filename)
        try:
            prompt_text, character_name = core.load_character_profile(path)
            self.character_prompt = prompt_text
            self.character_var.set(character_name or "Unknown")
            self.settings["character_name"] = character_name
            self.settings["character_profile_file"] = filename
            selected_map = dict(self.settings.get("server_character_profiles", {}))
            selected_map[profile] = filename
            self.settings["server_character_profiles"] = selected_map
            if load_ai_settings:
                self._load_character_specific_ai_settings(path)
            if save_setting:
                core.save_settings(self.settings)
            self._append_log(f"[CHARACTER] Loaded {profile}/{filename} -> {character_name or 'Unknown'}")
        except Exception as exc:
            self.character_var.set("Profile error")
            self._append_log(f"[CHARACTER ERROR] {type(exc).__name__}: {exc}")

    def _on_character_profile_changed(self, event=None):
        if self.running:
            return
        self._load_selected_character_profile(save_setting=True)

    def _selected_server_profile(self):
        selected = self.server_var.get() if hasattr(self, "server_var") else ""
        for key, profile in core.SERVER_PROFILES.items():
            if profile["display_name"] == selected:
                return key
        return self.settings.get("server_profile", "TDN")

    def _on_server_changed(self, event=None):
        if self.running:
            return
        profile = self._selected_server_profile()
        self.settings = core.load_settings()
        self.settings["server_profile"] = profile
        self.log_path_var.set(core.get_server_log_path(self.settings, profile))
        core.save_settings(self.settings)
        self._refresh_character_profiles(initial=False)
        self._append_log(f"[SERVER] Selected {core.SERVER_PROFILES[profile]['display_name']}; character list updated.")

    def _browse_log_file(self):
        filename = filedialog.askopenfilename(
            title="Select Neverwinter Nights client log",
            filetypes=[("Text logs", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self.log_path_var.set(filename)

    def _apply_server_settings(self):
        profile = self._selected_server_profile()
        path = self.log_path_var.get().strip()
        if not path:
            path = core.SERVER_PROFILES[profile]["default_log_path"]
            self.log_path_var.set(path)
        settings = core.load_settings()
        paths = dict(settings.get("server_log_paths", {}))
        paths[profile] = path
        settings["server_profile"] = profile
        settings["server_log_paths"] = paths
        settings["log_path"] = path
        core.save_settings(settings)
        self.settings = settings
        return profile, path

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
            self.guide_status_var.set("Guidance active until cleared." if value else "No guidance active.")
            self._append_log("[GUIDE] Persistent guidance activated.")

    def clear_guidance(self):
        core.clear_shared_guidance()
        if self.bot:
            self.bot.next_guidance = ""
        self.guidance_text.delete("1.0", "end")
        self.guidance_text.edit_modified(False)
        self.guidance_dirty = False
        self.last_guidance_file_value = ""
        self.guide_status_var.set("No guidance active.")
        self._append_log("[GUIDE] Persistent guidance cleared.")

    def _on_length_mode_changed(self, event=None):
        mode = self.length_mode_var.get() or "Auto"
        self.settings["response_length_mode"] = mode
        if self.bot:
            self.bot.settings["response_length_mode"] = mode

        core.save_settings(self.settings)
        profile_path = self._current_character_profile_path()
        if profile_path:
            source_settings = self.bot.settings if self.bot else self.settings
            core.save_character_ai_settings(profile_path, source_settings)

        self._append_log(f"[AI] Response length mode: {mode}")

    def _on_provider_changed(self, event=None):
        provider = self.provider_var.get()
        previous_provider = self.settings.get("ai_provider", "Google Gemini")
        current_model = self.model_var.get().strip()
        previous_default = core.AI_PROVIDERS.get(previous_provider, {}).get("default_model", "")
        if not current_model or current_model == previous_default:
            self.model_var.set(core.AI_PROVIDERS[provider]["default_model"])
        self.settings["ai_provider"] = provider
        self._update_provider_ui()

    def _update_provider_ui(self):
        provider = self.provider_var.get() or "OpenAI"
        info = core.AI_PROVIDERS[provider]
        if provider == "LM Studio":
            self.api_key_label.grid_remove()
            self.api_entry.grid_remove()
            self.show_key_btn.grid_remove()
            self.lm_url_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
            self.lm_url_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(8, 0))
            self.provider_hint_var.set(
                "Free/local. Start the LM Studio server first. Leave Model as 'auto' to use the first model LM Studio reports."
            )
        else:
            self.lm_url_label.grid_remove()
            self.lm_url_entry.grid_remove()
            self.api_key_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
            self.api_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 8), pady=(8, 0))
            self.show_key_btn.grid(row=1, column=3, sticky="w", pady=(8, 0))
            env_name = info["env_key"]
            if provider == "OpenAI":
                self.provider_hint_var.set(f"Uses OpenAI. Enter a key here or set {env_name} in Windows.")
            else:
                self.provider_hint_var.set(
                    f"Uses Google Gemini. Enter a key here or set {env_name} in Windows. "
                    "If a Gemini model is busy, rate-limited, or unavailable to the project, "
                    "Role Weaver automatically tries other Flash/Flash-Lite models with the same key."
                )

    def _effective_api_key(self):
        provider = self.provider_var.get() or "OpenAI"
        if provider == "LM Studio":
            return ""
        env_name = core.AI_PROVIDERS[provider]["env_key"]
        return self.api_key_var.get().strip() or os.environ.get(env_name, "").strip()

    def _save_ai_settings(self):
        provider = self.provider_var.get() or "OpenAI"
        self.settings["ai_provider"] = provider
        self.settings["model"] = self.model_var.get().strip() or core.AI_PROVIDERS[provider]["default_model"]
        raw_lm_url = self.lm_url_var.get().strip() or "http://127.0.0.1:1234"
        self.settings["lm_studio_base_url"] = core.normalize_lm_studio_base_url(raw_lm_url)
        self.settings["response_length_mode"] = self.length_mode_var.get() or "Auto"
        if provider == "LM Studio":
            self.lm_url_var.set(self.settings["lm_studio_base_url"])
        core.save_settings(self.settings)
        profile_path = self._current_character_profile_path()
        if profile_path:
            core.save_character_ai_settings(profile_path, self.settings)

    def test_ai_connection(self):
        try:
            self._save_ai_settings()
            provider = self.provider_var.get()
            api_key = self._effective_api_key()
            if core.AI_PROVIDERS[provider]["requires_key"] and not api_key:
                raise RuntimeError(f"{provider} requires an API key.")
            client = core.create_ai_provider(self.settings, api_key=api_key)
            message = client.test()
            if provider == "LM Studio" and self.model_var.get().strip().casefold() == "auto":
                self.model_var.set(client.model)
                self.settings["model"] = client.model
                core.save_settings(self.settings)
            elif provider == "Google Gemini":
                self.model_var.set(client.model)
                self.settings["model"] = client.model
                core.save_settings(self.settings)
            self._append_log(f"[AI TEST] {provider}: {message}")
            messagebox.showinfo("AI connection", message)
        except Exception as exc:
            self._append_log(f"[AI TEST ERROR] {type(exc).__name__}: {exc}")
            messagebox.showerror("AI connection failed", str(exc))

    def start_bot(self):
        if self.running:
            return

        provider = self.provider_var.get() or "OpenAI"
        api_key = self._effective_api_key()
        if core.AI_PROVIDERS[provider]["requires_key"] and not api_key:
            env_name = core.AI_PROVIDERS[provider]["env_key"]
            messagebox.showerror(
                f"{provider} API key required",
                f"Enter an API key or set {env_name} in Windows before starting.",
            )
            return

        try:
            filename = self.character_profile_var.get().strip()
            if not filename:
                messagebox.showerror(
                    "Character profile required",
                    "Select a character_*.txt prompt file before starting.",
                )
                return

            # Do not reload the character's saved AI settings here. The user may
            # have just changed Provider/Model in the UI; Start must honor those
            # currently selected values rather than reverting them.
            self._load_selected_character_profile(
                save_setting=True,
                load_ai_settings=False,
            )
            character_name = self.character_var.get().strip()
            if not character_name or character_name in ("Unknown", "Profile error", "No profile found"):
                messagebox.showerror(
                    "Character name not found",
                    "The selected character profile must contain a line like 'Name: Lora Thendry' or 'Character Name: Lora Thendry'.",
                )
                return

            profile, log_path = self._apply_server_settings()

            # The selected prompt file defines both the character instructions
            # and the character name used to identify self-chat in the log.
            self.settings["character_name"] = character_name
            self.settings["character_profile_file"] = filename
            self._save_ai_settings()
            provider = self.settings["ai_provider"]
            client = core.create_ai_provider(self.settings, api_key=api_key)
            if provider == "LM Studio" and self.settings.get("model", "").casefold() == "auto":
                self.settings["model"] = client.model
                self.model_var.set(client.model)
                core.save_settings(self.settings)
            self.bot = core.NWNAIBot(self.settings, self.character_prompt, client)
            self.bot.next_guidance = core.read_shared_guidance()
            self.bot.settings["response_length_mode"] = self.length_mode_var.get() or "Auto"

            threading.Thread(target=self.bot.action_worker, daemon=True).start()
            self.hotkeys = self.bot.hotkey_listener()

            self.running = True
            self._set_running_controls(True)
            self.settings_lock_var.set("Settings locked while Role Weaver is running.")
            self.status_var.set("Running")
            self.character_profile_combo.configure(state="disabled")
            self.refresh_profiles_btn.configure(state="disabled")
            self.provider_combo.configure(state="disabled")
            self.model_entry.configure(state="disabled")
            self.api_entry.configure(state="disabled")
            self.lm_url_entry.configure(state="disabled")
            self.test_ai_btn.configure(state="disabled")
            self.server_combo.configure(state="disabled")
            self.log_path_entry.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            self._append_log(f"[START] AI: {provider} / {self.settings['model']}")
            self._append_log(f"[START] Server: {core.SERVER_PROFILES[profile]['display_name']}")
            self._append_log(f"[START] Watching: {self.settings['log_path']}")
            memory_base, _, _, _ = core._memory_paths(self.settings)
            self._append_log(f"[MEMORY] Persistent RP memory: {memory_base}")
            core.LORE_DIR.mkdir(parents=True, exist_ok=True)
            lore_count = len(list(core.LORE_DIR.glob("*.txt")))
            self._append_log(f"[LORE] Reference folder: {core.LORE_DIR} ({lore_count} .txt file(s))")
            self._append_log(f"[HISTORY] Saving conversation to: {self.bot.history_path}")
            self._append_log("[TELL] Private Tell conversations use separate AI context threads.")
            self._append_log("[IC/OOC] Explicit OOC lines are excluded from AI reply context by default.")
            if core.read_shared_guidance():
                self._append_log("[GUIDE] Persistent guidance is active and will remain until cleared.")
            self._refresh_history_files()
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
                    self.settings.get("server_profile", "TDN"),
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
        try:
            if self.bot.summary_event_buffer and not self.bot.summary_in_progress:
                threading.Thread(target=self.bot.flush_memory_summary, daemon=True).start()
        except Exception:
            pass
        self.bot.stop_event.set()
        try:
            if self.hotkeys:
                self.hotkeys.stop()
        except Exception:
            pass
        self.running = False
        self._set_running_controls(False)
        self.settings_lock_var.set("")
        self.character_profile_combo.configure(state="readonly")
        self.refresh_profiles_btn.configure(state="normal")
        self.provider_combo.configure(state="readonly")
        self.model_entry.configure(state="normal")
        self.api_entry.configure(state="normal")
        self.lm_url_entry.configure(state="normal")
        self.test_ai_btn.configure(state="normal")
        self._update_provider_ui()
        self.server_combo.configure(state="readonly")
        self.log_path_entry.configure(state="normal")
        self.browse_btn.configure(state="normal")
        self.status_var.set("Stopped")

    def _set_running_controls(self, running):
        if running:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.pause_btn.configure(state="normal")
            self.auto_btn.configure(state="normal")
            self.draft_btn.configure(state="normal")
            self.f9_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
            self.test_btn.configure(state="normal")
            self.regenerate_btn.configure(state="normal")
            self.shorter_btn.configure(state="normal")
            self.longer_btn.configure(state="normal")
            self.paste_draft_btn.configure(state="normal")
            self.clear_draft_btn.configure(state="normal")
            self.save_relationship_btn.configure(state="normal")
            self.ignore_context_btn.configure(state="normal")
            self.pin_context_btn.configure(state="normal")
            self.forget_before_btn.configure(state="normal")

            # Make settings visibly locked while the bot is active.
            for button in self._settings_nav_buttons.values():
                button.configure(style="Locked.TButton")
        else:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.pause_btn.configure(state="disabled")
            self.auto_btn.configure(state="disabled")
            self.draft_btn.configure(state="disabled")
            self.f9_btn.configure(state="disabled")
            self.clear_btn.configure(state="disabled")
            self.test_btn.configure(state="disabled")
            self.regenerate_btn.configure(state="disabled")
            self.shorter_btn.configure(state="disabled")
            self.longer_btn.configure(state="disabled")
            self.paste_draft_btn.configure(state="disabled")
            self.clear_draft_btn.configure(state="disabled")
            self.save_relationship_btn.configure(state="disabled")
            self.ignore_context_btn.configure(state="disabled")
            self.pin_context_btn.configure(state="disabled")
            self.forget_before_btn.configure(state="disabled")

            # Restore normal tab appearance.
            for key, button in self._settings_nav_buttons.items():
                current = False
                try:
                    current = self._settings_frames[key].winfo_ismapped()
                except Exception:
                    pass
                button.configure(
                    style="NavSelected.TButton" if current else "Nav.TButton"
                )

    def toggle_pause(self):
        if self.bot:
            self.bot.action_queue.put(("toggle_pause", "ui"))

    def toggle_auto(self):
        if self.bot:
            self.bot.action_queue.put(("toggle_auto", "ui"))

    def _select_candidate(self, event=None):
        if not self.bot:
            return
        try:
            index = int(self.candidate_var.get().split()[-1]) - 1
        except Exception:
            index = 0
        if 0 <= index < len(self.bot.candidate_replies):
            text = self.bot.candidate_replies[index]
            self.ai_draft_text.delete("1.0", "end")
            self.ai_draft_text.insert("1.0", text)
            self.bot.last_draft = text
            self.bot.last_draft_version += 1
            self.last_seen_draft_version = self.bot.last_draft_version

    def _refresh_history_files(self):
        if not self.bot:
            return
        files = core.list_history_files(self.bot.settings)
        names = [p.name for p in files]
        self.history_file_combo["values"] = names
        current = self.history_file_var.get()
        if current not in names:
            current = self.bot.history_path.name if self.bot.history_path.name in names else (names[0] if names else "")
            self.history_file_var.set(current)
        if current:
            self._load_selected_history()

    def _load_selected_history(self, event=None):
        if not self.bot:
            return
        name = self.history_file_var.get().strip()
        if not name:
            return
        path = core._history_dir(self.bot.settings) / name
        try:
            text = core.read_history_file(path)
        except Exception as exc:
            text = f"Unable to read history: {exc}"
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        self.history_text.insert("1.0", text)
        self.history_text.configure(state="disabled")

    def _search_history(self, event=None):
        term = self.history_search_var.get().strip()
        if not term:
            return "break"
        self.history_text.configure(state="normal")
        start = self.history_text.index("insert +1c")
        pos = self.history_text.search(term, start, stopindex="end", nocase=True)
        if not pos:
            pos = self.history_text.search(term, "1.0", stopindex=start, nocase=True)
        if pos:
            end = f"{pos}+{len(term)}c"
            self.history_text.tag_remove("sel", "1.0", "end")
            self.history_text.tag_add("sel", pos, end)
            self.history_text.mark_set("insert", end)
            self.history_text.see(pos)
        self.history_text.configure(state="disabled")
        return "break"

    def _refresh_manual_context_list(self):
        if not self.bot:
            return
        rows = self.bot.context_rows()
        signature = tuple(
            (r["id"], r["ignored"], r["pinned"], r["mode"], r["message"])
            for r in rows
        )
        if signature == self.last_context_event_signature:
            return
        self.last_context_event_signature = signature
        self.context_event_lookup = {}
        display = []
        for row in rows:
            flags = []
            if row["mode"] == "OOC":
                flags.append("OOC")
            if row["ignored"]:
                flags.append("IGNORED")
            if row["pinned"]:
                flags.append("REMEMBER")
            flag_text = (" [" + ", ".join(flags) + "]") if flags else ""
            snippet = row["message"].replace("\n", " ")
            if len(snippet) > 90:
                snippet = snippet[:87] + "..."
            label = (
                f"#{row['id']} {row['speaker']} [{row['channel']}]"
                f"{flag_text}: {snippet}"
            )
            display.append(label)
            self.context_event_lookup[label] = row["id"]

        current = self.context_event_var.get()
        self.context_event_combo["values"] = display
        if current not in display:
            self.context_event_var.set(display[-1] if display else "")

    def _selected_context_id(self):
        label = self.context_event_var.get()
        return self.context_event_lookup.get(label)

    def toggle_ignore_selected_context(self):
        if not self.bot:
            return
        cid = self._selected_context_id()
        if cid is None:
            return
        rows = {r["id"]: r for r in self.bot.context_rows()}
        row = rows.get(cid, {})
        self.bot.ignore_context_event(cid, not row.get("ignored", False))
        self.last_context_event_signature = None
        self._refresh_manual_context_list()

    def toggle_pin_selected_context(self):
        if not self.bot:
            return
        cid = self._selected_context_id()
        if cid is None:
            return
        rows = {r["id"]: r for r in self.bot.context_rows()}
        row = rows.get(cid, {})
        self.bot.pin_context_event(cid, not row.get("pinned", False))
        self.last_context_event_signature = None
        self._refresh_manual_context_list()

    def forget_before_selected_context(self):
        if not self.bot:
            return
        cid = self._selected_context_id()
        if cid is None:
            return
        self.bot.forget_before(cid)
        self.last_context_event_signature = None
        self._refresh_manual_context_list()

    def _refresh_relationship_list(self):
        if not self.bot:
            return
        names = tuple(
            sorted(
                self.bot.memory_data.get("characters", {}).keys(),
                key=str.casefold,
            )
        )
        if names == self.last_relationship_names:
            return
        self.last_relationship_names = names
        self.relationship_character_combo["values"] = names

        current = self.relationship_character_var.get().strip()
        if current not in names:
            current = names[0] if names else ""
            self.relationship_character_var.set(current)
        if current:
            self._load_relationship_record()

    def _load_relationship_record(self, event=None):
        if not self.bot:
            return
        name = self.relationship_character_var.get().strip()
        item = self.bot.memory_data.get("characters", {}).get(name, {})
        if not isinstance(item, dict):
            item = {"notes": str(item or "")}

        self.relationship_text.delete("1.0", "end")
        self.relationship_text.insert("1.0", item.get("relationship", "") or "")
        self.relationship_memory_text.delete("1.0", "end")
        self.relationship_memory_text.insert("1.0", item.get("notes", "") or "")

    def save_relationship_record(self):
        if not self.bot:
            return
        name = self.relationship_character_var.get().strip()
        if not name:
            self._append_log("[MEMORY] No remembered character selected.")
            return
        relationship = self.relationship_text.get("1.0", "end").strip()
        notes = self.relationship_memory_text.get("1.0", "end").strip()
        if self.bot.update_character_record(
            name, notes=notes, relationship=relationship
        ):
            self._append_log(f"[MEMORY] Saved relationship/memory for {name}.")

    def _request_draft_variant(self, variant):
        if self.bot:
            self.set_guidance_if_changed()
            self.bot.action_queue.put(("draft_variant", variant))

    def regenerate_draft(self):
        self._request_draft_variant("regenerate")

    def shorter_draft(self):
        self._request_draft_variant("shorter")

    def longer_draft(self):
        self._request_draft_variant("longer")

    def paste_current_draft(self):
        if not self.bot:
            return
        text = self.ai_draft_text.get("1.0", "end").strip()
        if not text:
            self._append_log("[DRAFT] Draft box is empty.")
            return
        self._append_log("[DRAFT] Be ready to click NWN during the 2-second countdown.")
        self.bot.action_queue.put(("paste_existing_draft", text))

    def clear_ai_draft(self):
        self.ai_draft_text.delete("1.0", "end")
        if self.bot:
            self.bot.last_draft = ""
            self.bot.last_draft_version += 1
            self.last_seen_draft_version = self.bot.last_draft_version
        self._append_log("[DRAFT] Draft box cleared.")

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
                        self.character_profile_combo.configure(state="readonly")
                        self.refresh_profiles_btn.configure(state="normal")
                        self.provider_combo.configure(state="readonly")
                        self.model_entry.configure(state="normal")
                        self.api_entry.configure(state="normal")
                        self.lm_url_entry.configure(state="normal")
                        self.test_ai_btn.configure(state="normal")
                        self._update_provider_ui()
                        self.server_combo.configure(state="readonly")
                        self.log_path_entry.configure(state="normal")
                        self.browse_btn.configure(state="normal")
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
                memory_people = len(self.bot.memory_data.get("characters", {}))
                summary_state = "summary ready" if self.bot.running_summary else "no summary yet"
                self.context_var.set(
                    f"Context: {len(self.bot.context)} | Memory: {memory_people} people | {summary_state}"
                )

                if self.bot.last_draft_version != self.last_seen_draft_version:
                    self.last_seen_draft_version = self.bot.last_draft_version
                    if self.bot.last_draft:
                        self.ai_draft_text.delete("1.0", "end")
                        self.ai_draft_text.insert("1.0", self.bot.last_draft)

                if self.bot.candidate_version != self.last_seen_candidate_version:
                    self.last_seen_candidate_version = self.bot.candidate_version
                    values = [f"Candidate {i+1}" for i in range(len(self.bot.candidate_replies))]
                    self.candidate_combo["values"] = values
                    if values:
                        self.candidate_var.set(values[0])

                if self.bot.last_ai_context_version != self.last_seen_ai_context_version:
                    self.last_seen_ai_context_version = self.bot.last_ai_context_version
                    self.ai_context_text.configure(state="normal")
                    self.ai_context_text.delete("1.0", "end")
                    self.ai_context_text.insert(
                        "1.0",
                        self.bot.last_ai_context_display
                        or "No AI reply has been generated yet.",
                    )
                    self.ai_context_text.configure(state="disabled")

                self._refresh_relationship_list()
                self._refresh_manual_context_list()

                if self.bot.last_generation_timestamp:
                    self.timing_var.set(
                        f"AI: {self.bot.last_generation_seconds:.2f}s "
                        f"({self.bot.last_generation_model or 'model'})"
                    )
                else:
                    self.timing_var.set("AI: —")

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
                    self.settings_lock_var.set("")
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
                    self.guide_status_var.set("No guidance active.")
                    self.last_guidance_file_value = ""
                elif not self.guidance_dirty:
                    self.guidance_text.delete("1.0", "end")
                    self.guidance_text.insert("1.0", value)
                    self.guidance_text.edit_modified(False)
                    self.guide_status_var.set("Guidance active until cleared.")
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
    apply_windows_app_identity(root)
    show_splash(root)
    app = NWNAIApp(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
