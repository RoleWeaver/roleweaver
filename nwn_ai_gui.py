import os
import ctypes
import queue
import re
import sys
import threading
import time
import traceback
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path

import nwn_ai_bot as core


RESOURCE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
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
        self.last_memory_overview_signature = None
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

        character_buttons = ttk.Frame(character_frame)
        character_buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(7, 0))
        self.new_character_btn = ttk.Button(
            character_buttons, text="New Character...", command=self._open_character_editor
        )
        self.new_character_btn.pack(side="left")
        self.edit_character_btn = ttk.Button(
            character_buttons, text="Edit Selected...",
            command=lambda: self._open_character_editor(edit_selected=True),
        )
        self.edit_character_btn.pack(side="left", padx=(7, 0))

        self.character_file_display_var = tk.StringVar(value="")
        ttk.Label(
            character_frame,
            textvariable=self.character_file_display_var,
            style="Sidebar.TLabel",
            wraplength=310,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(7, 0))

        ttk.Label(
            character_frame,
            text="Profiles are stored locally for each detected world. Generic Player and NPC examples are available when a world is first discovered.",
            wraplength=310,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 0))
        character_frame.columnconfigure(0, weight=1)

        # Server / log profile
        server_frame = ttk.LabelFrame(settings_panel_host, text="Server and Log", padding=8)
        self._settings_frames["Server / Log"] = server_frame
        ttk.Label(server_frame, text="World:").grid(row=0, column=0, sticky="w")
        self.server_var = tk.StringVar()
        self.server_combo = ttk.Combobox(
            server_frame, textvariable=self.server_var, state="readonly",
            values=[profile["display_name"] for profile in core.SERVER_PROFILES.values()],
            width=40,
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
        button_row = ttk.Frame(server_frame)
        button_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(7, 0))
        self.browse_btn = ttk.Button(button_row, text="Browse...", command=self._browse_log_file)
        self.browse_btn.pack(side="left")
        self.rescan_logs_btn = ttk.Button(button_row, text="Rescan Logs", command=self._rescan_server_logs)
        self.rescan_logs_btn.pack(side="left", padx=(6, 0))
        self.lore_editor_btn = ttk.Button(
            button_row, text="Lore Editor...", command=self._open_lore_editor
        )
        self.lore_editor_btn.pack(side="right")
        ttk.Label(
            server_frame,
            text="Starts with Auto Detect only. Worlds appear here after they are discovered from your own NWN logs.",
            wraplength=310,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
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
            text="Provider, model and response length are saved per world-specific character profile.",
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
            text="Persistent: remains active until you clear or replace it. Ctrl+Enter sets it.",
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
            row2, text="Generate 3 Drafts (F8)", command=self.generate_draft, state="disabled"
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
            text="F8 creates drafts here. F9: after generation, click NWN during the 2-second countdown; the draft is pasted but not sent.",
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
        memory_frame = ttk.Frame(lower_tabs, padding=7)
        cast_frame = ttk.Frame(lower_tabs, padding=7)
        continuity_frame = ttk.Frame(lower_tabs, padding=7)
        adaptive_frame = ttk.Frame(lower_tabs, padding=7)
        history_frame = ttk.Frame(lower_tabs, padding=7)
        lower_tabs.add(draft_frame, text="AI Draft")
        lower_tabs.add(context_frame, text="AI Context")
        lower_tabs.add(relationship_frame, text="Relationships")
        lower_tabs.add(memory_frame, text="Character Memory")
        lower_tabs.add(cast_frame, text="DM Cast")
        lower_tabs.add(continuity_frame, text="Continuity")
        lower_tabs.add(adaptive_frame, text="Adaptive")
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

        ttk.Label(relationship_frame, text="Interaction history (automatic):").pack(
            anchor="w", pady=(8, 3)
        )
        self.relationship_history_text = tk.Text(
            relationship_frame,
            height=5,
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
            pady=6,
            font=("Segoe UI", 9),
        )
        self.relationship_history_text.pack(fill="both", expand=True)

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
        ttk.Button(rel_buttons, text="Add Alias...", command=self._add_relationship_alias).pack(side="left")
        ttk.Button(rel_buttons, text="Merge Into...", command=self._merge_relationship_record).pack(side="left", padx=(6, 0))
        ttk.Button(rel_buttons, text="Delete Character...", command=self._delete_relationship_record).pack(side="left", padx=(6, 0))

        # Character Memory v1.1: learned voice and ongoing story threads.
        memory_buttons = ttk.Frame(memory_frame)
        memory_buttons.pack(fill="x", pady=(0, 6))
        ttk.Button(memory_buttons, text="Refresh", command=self._refresh_memory_overview).pack(side="left")
        ttk.Button(memory_buttons, text="Summarize Now", command=self.summarize_memory_now).pack(side="left", padx=(6, 0))
        ttk.Button(
            memory_buttons,
            text="Reset Learned Voice",
            command=self.reset_learned_voice,
        ).pack(side="right")
        ttk.Label(
            memory_frame,
            text="Character Intelligence tracks observed voice, emotional continuity, IC knowledge, and story threads. It learns only from IC context; the explicit character profile always takes precedence.",
            wraplength=700,
        ).pack(anchor="w", pady=(0, 6))
        # Keep the automatic intelligence overview and manual knowledge manager in a
        # user-resizable vertical split.  This is particularly useful on smaller
        # displays where the fixed alpha3 layout made one section difficult to see.
        memory_split = ttk.PanedWindow(memory_frame, orient="vertical")
        memory_split.pack(fill="both", expand=True)

        overview_frame = ttk.Frame(memory_split)
        self.memory_overview_text = tk.Text(
            overview_frame, wrap="word", state="disabled",
            bg="#1e1f22", fg="#dbdee1", insertbackground="#dbdee1",
            selectbackground="#5865f2", selectforeground="#ffffff",
            relief="flat", bd=0, padx=8, pady=7, font=("Segoe UI", 9),
        )
        self.memory_overview_text.pack(fill="both", expand=True)

        knowledge_frame = ttk.LabelFrame(memory_split, text="Manual Character Knowledge Management", padding=6)
        ttk.Label(
            knowledge_frame,
            text="Add, correct, reclassify, or remove facts the character knows. DM_ONLY entries are stored for DM reference and are never sent to the character AI.",
            wraplength=700,
        ).pack(anchor="w", pady=(0, 5))
        self.knowledge_tree = ttk.Treeview(
            knowledge_frame, columns=("privacy", "confidence", "fact"), show="headings", height=7
        )
        self.knowledge_tree.heading("privacy", text="Privacy")
        self.knowledge_tree.heading("confidence", text="Confidence")
        self.knowledge_tree.heading("fact", text="Knowledge")
        self.knowledge_tree.column("privacy", width=90, anchor="center", stretch=False)
        self.knowledge_tree.column("confidence", width=90, anchor="center", stretch=False)
        self.knowledge_tree.column("fact", width=500, anchor="w")
        self.knowledge_tree.pack(fill="x", expand=False)
        self.knowledge_tree.bind("<Double-1>", lambda _e: self._edit_knowledge_item())
        kb = ttk.Frame(knowledge_frame)
        kb.pack(fill="x", pady=(5, 0))
        ttk.Button(kb, text="Add Knowledge...", command=self._add_knowledge_item).pack(side="left")
        ttk.Button(kb, text="Edit Selected...", command=self._edit_knowledge_item).pack(side="left", padx=(6, 0))
        ttk.Button(kb, text="Delete Selected", command=self._delete_knowledge_item).pack(side="left", padx=(6, 0))

        # The sash between these panes can be dragged vertically to give either the
        # overview or manual manager more room.  Weight keeps both useful when the
        # main window itself is resized.
        memory_split.add(overview_frame, weight=3)
        memory_split.add(knowledge_frame, weight=2)

        # Alpha4 Continuity Tools: threads, commitments, and significant event history.
        continuity_split = ttk.PanedWindow(continuity_frame, orient="vertical")
        continuity_split.pack(fill="both", expand=True)
        self.continuity_trees = {}
        specs = [
            ("thread", "Active Story Threads", ("status","importance","summary"), ("Status","Imp.","Thread")),
            ("commitment", "Promises & Commitments", ("status","due","summary"), ("Status","Due","Commitment")),
            ("event", "Continuity Event History", ("when","importance","summary"), ("When","Imp.","Event")),
        ]
        for kind, title, cols, headings in specs:
            pane=ttk.Frame(continuity_split, padding=(0,0,0,6))
            head=ttk.Frame(pane); head.pack(fill="x", pady=(0,4))
            ttk.Label(head,text=title,font=("Segoe UI",9,"bold")).pack(side="left")
            ttk.Button(head,text="Delete",command=lambda k=kind:self._delete_continuity(k)).pack(side="right")
            ttk.Button(head,text="Edit",command=lambda k=kind:self._edit_continuity(k)).pack(side="right",padx=(0,4))
            ttk.Button(head,text="Add",command=lambda k=kind:self._add_continuity(k)).pack(side="right",padx=(0,4))
            tree=ttk.Treeview(pane,columns=cols,show="headings",height=5)
            for c,h in zip(cols,headings): tree.heading(c,text=h)
            for c in cols: tree.column(c,width=90 if c != "summary" else 620,anchor="w",stretch=(c=="summary"))
            tree.pack(fill="both",expand=True)
            tree.bind("<Double-1>",lambda _e,k=kind:self._edit_continuity(k))
            self.continuity_trees[kind]=tree
            continuity_split.add(pane,weight=1)

        # Alpha5 Adaptive Characters: correction learning plus player-approved
        # development. Nothing in the development proposal list changes portrayal
        # until the player explicitly approves it.
        adaptive_split = ttk.PanedWindow(adaptive_frame, orient="vertical")
        adaptive_split.pack(fill="both", expand=True)
        corr_frame=ttk.LabelFrame(adaptive_split,text="Correction Learning",padding=6)
        ttk.Label(corr_frame,text="Role Weaver learns recurring style preferences only when you edit an AI draft and the edited line actually appears in the NWN log.",wraplength=760).pack(anchor="w",pady=(0,5))
        self.correction_text=tk.Text(corr_frame,wrap="word",state="disabled",height=7,bg="#1e1f22",fg="#dbdee1",relief="flat",bd=0,padx=8,pady=7,font=("Segoe UI",9))
        self.correction_text.pack(fill="both",expand=True)

        dev_frame=ttk.LabelFrame(adaptive_split,text="Player-Approved Character Development",padding=6)
        ttk.Label(dev_frame,text="Role Weaver may propose durable changes suggested by repeated IC portrayal. Pending proposals do not affect the character until you approve them.",wraplength=760).pack(anchor="w",pady=(0,5))
        ttk.Label(dev_frame,text="Pending proposals",font=("Segoe UI",9,"bold")).pack(anchor="w")
        self.development_tree=ttk.Treeview(dev_frame,columns=("area","confidence","statement"),show="headings",height=5)
        for c,h,w in (("area","Area",120),("confidence","Conf.",60),("statement","Proposed Development",560)):
            self.development_tree.heading(c,text=h); self.development_tree.column(c,width=w,anchor="w",stretch=(c=="statement"))
        self.development_tree.pack(fill="both",expand=True)
        db=ttk.Frame(dev_frame); db.pack(fill="x",pady=(4,6))
        ttk.Button(db,text="Approve Selected",command=self._approve_development).pack(side="left")
        ttk.Button(db,text="Reject Selected",command=self._reject_development).pack(side="left",padx=(6,0))
        ttk.Label(dev_frame,text="Approved development",font=("Segoe UI",9,"bold")).pack(anchor="w")
        self.approved_development_tree=ttk.Treeview(dev_frame,columns=("area","statement"),show="headings",height=4)
        self.approved_development_tree.heading("area",text="Area"); self.approved_development_tree.heading("statement",text="Approved Development")
        self.approved_development_tree.column("area",width=120,anchor="w",stretch=False); self.approved_development_tree.column("statement",width=620,anchor="w")
        self.approved_development_tree.pack(fill="both",expand=True)
        ab=ttk.Frame(dev_frame); ab.pack(fill="x",pady=(4,0))
        ttk.Button(ab,text="Remove Selected Approval",command=self._remove_approved_development).pack(side="left")
        ttk.Button(ab,text="Refresh",command=self._refresh_adaptive).pack(side="right")
        adaptive_split.add(corr_frame,weight=1); adaptive_split.add(dev_frame,weight=2)

        # DM Cast Manager / shared Campaign Memory (v1.2 alpha stage 1).
        cast_header = ttk.Frame(cast_frame)
        cast_header.pack(fill="x", pady=(0, 6))
        ttk.Label(cast_header, text="NPC Cast Manager", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(cast_header, text="Refresh", command=self._refresh_dm_cast).pack(side="right")

        campaign_bar = ttk.Frame(cast_frame)
        campaign_bar.pack(fill="x", pady=(0, 7))
        ttk.Label(campaign_bar, text="Campaign:").pack(side="left")
        self.campaign_var = tk.StringVar(value=str(self.settings.get("campaign_id", "default")))
        self.campaign_combo = ttk.Combobox(campaign_bar, textvariable=self.campaign_var, state="readonly", width=24)
        self.campaign_combo.pack(side="left", padx=(5, 6))
        self.campaign_combo.bind("<<ComboboxSelected>>", self._on_campaign_changed)
        ttk.Button(campaign_bar, text="New", command=self._new_campaign).pack(side="left")
        ttk.Button(campaign_bar, text="Rename", command=self._rename_campaign).pack(side="left", padx=(4, 0))
        ttk.Button(campaign_bar, text="Delete", command=self._delete_campaign).pack(side="left", padx=(4, 0))
        ttk.Button(campaign_bar, text="Campaign Manager", command=self._open_campaign_manager, style="Accent.TButton").pack(side="left", padx=(8, 0))
        self.campaign_status_var = tk.StringVar(value="")
        ttk.Label(campaign_bar, textvariable=self.campaign_status_var, foreground="#949ba4").pack(side="left", padx=(10, 0))

        cast_body = ttk.PanedWindow(cast_frame, orient="horizontal")
        cast_body.pack(fill="both", expand=True)
        cast_left = ttk.Frame(cast_body, padding=(0, 0, 7, 0))
        cast_right = ttk.Frame(cast_body, padding=(7, 0, 0, 0))
        cast_body.add(cast_left, weight=1)
        cast_body.add(cast_right, weight=2)

        self.dm_cast_tree = ttk.Treeview(
            cast_left, columns=("character", "member", "last"), show="headings", height=12
        )
        self.dm_cast_tree.heading("character", text="NPC")
        self.dm_cast_tree.heading("member", text="Campaign")
        self.dm_cast_tree.heading("last", text="Memory Updated")
        self.dm_cast_tree.column("character", width=150, anchor="w")
        self.dm_cast_tree.column("member", width=72, anchor="center")
        self.dm_cast_tree.column("last", width=115, anchor="w")
        self.dm_cast_tree.pack(fill="both", expand=True)
        self.dm_cast_tree.bind("<<TreeviewSelect>>", self._on_dm_cast_selected)
        self.dm_cast_tree.bind("<Double-1>", self._load_selected_cast_npc)

        cast_buttons = ttk.Frame(cast_left)
        cast_buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(cast_buttons, text="Load NPC", command=self._load_selected_cast_npc).pack(side="left")
        ttk.Button(cast_buttons, text="Edit Profile", command=self._edit_selected_cast_npc).pack(side="left", padx=(6, 0))
        ttk.Button(cast_buttons, text="Add/Remove Campaign", command=self._toggle_cast_membership).pack(side="left", padx=(6, 0))
        ttk.Button(cast_buttons, text="NPC Briefing", command=self._show_npc_briefing, style="Accent.TButton").pack(side="left", padx=(6, 0))

        ttk.Label(cast_right, text="Selected NPC", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.dm_cast_detail_text = tk.Text(
            cast_right, height=7, wrap="word", state="disabled",
            bg="#1e1f22", fg="#dbdee1", insertbackground="#dbdee1",
            selectbackground="#5865f2", selectforeground="#ffffff",
            relief="flat", bd=0, padx=8, pady=7, font=("Segoe UI", 9),
        )
        self.dm_cast_detail_text.pack(fill="x", pady=(4, 8))

        ttk.Label(cast_right, text="Shared Campaign Memory", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(
            cast_right,
            text="Character-readable continuity shared by this campaign. DM Notes below are never sent to the character AI.",
            wraplength=500,
        ).pack(anchor="w", pady=(2, 4))
        self.campaign_shared_text = tk.Text(
            cast_right, height=6, wrap="word", bg="#1e1f22", fg="#dbdee1",
            insertbackground="#dbdee1", selectbackground="#5865f2", selectforeground="#ffffff",
            relief="flat", bd=0, padx=8, pady=7, font=("Segoe UI", 9),
        )
        self.campaign_shared_text.pack(fill="both", expand=True)
        ttk.Label(cast_right, text="DM-only Notes", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(7, 3))
        self.campaign_dm_text = tk.Text(
            cast_right, height=4, wrap="word", bg="#1e1f22", fg="#dbdee1",
            insertbackground="#dbdee1", selectbackground="#5865f2", selectforeground="#ffffff",
            relief="flat", bd=0, padx=8, pady=7, font=("Segoe UI", 9),
        )
        self.campaign_dm_text.pack(fill="x")

        campaign_buttons = ttk.Frame(cast_right)
        campaign_buttons.pack(fill="x", pady=(7, 0))
        ttk.Button(campaign_buttons, text="Save Campaign Memory", command=self._save_campaign_memory, style="Accent.TButton").pack(side="right")
        ttk.Button(campaign_buttons, text="Campaign Briefing", command=self._show_campaign_briefing, style="Accent.TButton").pack(side="right", padx=(0, 6))
        ttk.Button(campaign_buttons, text="Export Campaign Pack...", command=self._export_campaign_pack).pack(side="left")
        ttk.Button(campaign_buttons, text="Import Campaign Pack...", command=self._import_campaign_pack).pack(side="left", padx=(6, 0))

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
        # profiles now live in world-specific folders.
        self.settings = core.refresh_discovered_servers(self.settings)
        profile = self.settings.get("server_profile", "AUTO")
        # When AUTO has a recognizable current log, use the discovered local world
        # immediately so character/lore/campaign data remain isolated by world.
        if profile == "AUTO":
            auto_path = core.get_server_log_path(self.settings, "AUTO")
            detected = core.detect_world_from_log(auto_path)
            if detected:
                core.register_discovered_server(self.settings, detected)
                profile = detected["id"]
                self.settings["server_profile"] = profile
                self.settings["log_path"] = detected["log_path"]
        core.save_settings(self.settings)
        self._refresh_server_combo(select_profile=profile)
        self.server_var.set(core.server_display_name(self.settings, profile))
        self.log_path_var.set(core.get_server_log_path(self.settings, profile))

        # Loading a profile also restores that character's AI/model/length settings.
        self._refresh_character_profiles(initial=True)
        self._refresh_campaigns(select=self.settings.get("campaign_id", "default"))
        self._refresh_dm_cast()

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
        profile = self._selected_server_profile() if hasattr(self, "server_var") else self.settings.get("server_profile", "AUTO")
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

    @staticmethod
    def _safe_text_filename(value, prefix="", default="new_file"):
        name = Path((value or "").strip()).name
        if name.lower().endswith(".txt"):
            name = name[:-4]
        name = re.sub(r"[^A-Za-z0-9_. -]+", "_", name).strip(" ._")
        if not name:
            name = default
        name = name.replace(" ", "_")
        if prefix and not name.casefold().startswith(prefix.casefold()):
            name = prefix + name
        return name + ".txt"

    def _open_character_editor(self, edit_selected=False):
        if self.running:
            return
        profile = self._selected_server_profile()
        existing_path = self._current_character_profile_path() if edit_selected else None
        existing_text = ""
        existing_filename = ""
        if existing_path and existing_path.exists():
            existing_text = existing_path.read_text(encoding="utf-8", errors="replace")
            existing_filename = existing_path.name

        win = tk.Toplevel(self.root)
        win.title("Role Weaver — Character Editor")
        win.geometry("820x760")
        win.minsize(680, 560)
        win.transient(self.root)

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=f"World / Server: {core.server_display_name(self.settings, profile)}",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")

        file_row = ttk.Frame(outer)
        file_row.pack(fill="x", pady=(8, 6))
        ttk.Label(file_row, text="Character file name:").pack(side="left")
        file_var = tk.StringVar(value=existing_filename or "character_New_Character.txt")
        ttk.Entry(file_row, textvariable=file_var).pack(side="left", fill="x", expand=True, padx=(8, 0))

        canvas = tk.Canvas(outer, bg="#313338", highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        form = ttk.Frame(canvas)
        form_id = canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(form_id, width=e.width))

        sections = [
            ("Character Name", 2),
            ("Profile Type", 2),
            ("Personality", 5),
            ("Speaking Style", 5),
            ("Background", 6),
            ("Beliefs", 5),
            ("Relationships", 5),
            ("Current Goals", 5),
            ("Secrets / Knowledge Boundaries", 5),
            ("Roleplay Rules", 6),
        ]
        boxes = {}

        def parse_sections(text):
            vals = {heading: "" for heading, _ in sections}
            aliases = {"Name": "Character Name", "Secrets": "Secrets / Knowledge Boundaries",
                       "Player Notes": "Roleplay Rules", "DM Notes": "Roleplay Rules"}
            current = None
            acc = []
            def flush():
                nonlocal acc
                if current:
                    vals[current] = "\n".join(acc).strip()
                acc = []
            for line in text.splitlines():
                m = re.match(r"^([^:]{1,80}):\s*(.*)$", line)
                if m:
                    raw = m.group(1).strip()
                    heading = aliases.get(raw, raw)
                    if heading in vals:
                        flush()
                        current = heading
                        if m.group(2).strip(): acc.append(m.group(2).strip())
                        continue
                if current is not None:
                    acc.append(line)
            flush()
            return vals

        values = parse_sections(existing_text)
        for heading, height in sections:
            ttk.Label(form, text=heading + ":", font=("Segoe UI", 9, "bold")).pack(fill="x", pady=(8, 3))
            if heading == "Profile Type":
                value = values.get(heading, "").strip()
                key = value.casefold()
                value = "NPC" if (key in {"npc", "dm npc", "non-player", "non player", "non-player character"} or "npc" in key or "non-player" in key) else "Player"
                var = tk.StringVar(value=value)
                box = ttk.Combobox(form, textvariable=var, state="readonly", values=["Player", "NPC"], width=24)
                box.pack(fill="x")
                box._roleweaver_var = var
            else:
                box = tk.Text(form, height=height, wrap="word", bg="#1e1f22", fg="#dbdee1",
                              insertbackground="#dbdee1", relief="flat", padx=7, pady=6,
                              selectbackground="#5865f2", selectforeground="#ffffff")
                box.pack(fill="x")
                box.insert("1.0", values.get(heading, ""))
            boxes[heading] = box

        button_row = ttk.Frame(win, padding=(10, 0, 10, 10))
        button_row.pack(fill="x")

        def save_character():
            filename = self._safe_text_filename(file_var.get(), prefix="character_", default="New_Character")
            name = boxes["Character Name"].get("1.0", "end-1c").strip()
            if not name:
                messagebox.showerror("Character name required", "Enter a Character Name before saving.", parent=win)
                return
            parts = []
            for heading, _ in sections:
                widget = boxes[heading]
                if heading == "Profile Type":
                    value = widget.get().strip() or "Player"
                else:
                    value = widget.get("1.0", "end-1c").strip()
                parts.append(f"{heading}: {value}" if "\n" not in value else f"{heading}:\n{value}")
            path = core.resolve_character_profile(profile, filename)
            path.write_text("\n\n".join(parts).strip() + "\n", encoding="utf-8")
            self._refresh_character_profiles(initial=False)
            if filename in list(self.character_profile_combo["values"]):
                self.character_profile_var.set(filename)
                self._load_selected_character_profile(save_setting=True)
            self._append_log(f"[CHARACTER] Saved {profile}/{filename}")
            self._refresh_dm_cast()
            win.destroy()

        ttk.Button(button_row, text="Save Character", command=save_character).pack(side="right")
        ttk.Button(button_row, text="Cancel", command=win.destroy).pack(side="right", padx=(0, 8))

    def _open_lore_editor(self):
        if self.running:
            return
        profile = self._selected_server_profile()
        win = tk.Toplevel(self.root)
        win.title("Role Weaver — Lore Editor")
        win.geometry("780x650")
        win.minsize(620, 480)
        win.transient(self.root)

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=f"Lore for: {core.server_display_name(self.settings, profile)}",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Only lore in this server folder is used while this server is selected.").pack(anchor="w", pady=(3, 8))

        existing_var = tk.StringVar()
        file_var = tk.StringVar(value="new_lore.txt")
        top = ttk.Frame(outer)
        top.pack(fill="x")
        ttk.Label(top, text="Existing:").grid(row=0, column=0, sticky="w")
        existing_combo = ttk.Combobox(top, textvariable=existing_var, state="readonly", width=34)
        existing_combo.grid(row=0, column=1, sticky="ew", padx=(7, 7))
        ttk.Label(top, text="File name:").grid(row=1, column=0, sticky="w", pady=(7, 0))
        ttk.Entry(top, textvariable=file_var).grid(row=1, column=1, sticky="ew", padx=(7, 7), pady=(7, 0))
        top.columnconfigure(1, weight=1)

        text = tk.Text(outer, wrap="word", bg="#1e1f22", fg="#dbdee1", insertbackground="#dbdee1",
                       relief="flat", padx=8, pady=8, selectbackground="#5865f2", selectforeground="#ffffff")
        text.pack(fill="both", expand=True, pady=(9, 8))

        def refresh_files(select_name=None):
            names = [p.name for p in core.list_lore_files(profile)]
            existing_combo["values"] = names
            if select_name in names:
                existing_var.set(select_name)
            elif names:
                existing_var.set(names[0])
            else:
                existing_var.set("")

        def load_selected(event=None):
            name = existing_var.get().strip()
            if not name: return
            path = core.resolve_lore_file(profile, name)
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                messagebox.showerror("Lore error", str(exc), parent=win); return
            file_var.set(name)
            text.delete("1.0", "end"); text.insert("1.0", content)

        def new_lore():
            existing_var.set("")
            file_var.set("new_lore.txt")
            text.delete("1.0", "end")
            text.focus_set()

        def save_lore():
            filename = self._safe_text_filename(file_var.get(), default="new_lore")
            content = text.get("1.0", "end-1c").strip()
            if not content:
                messagebox.showerror("Lore is empty", "Enter or paste lore before saving.", parent=win); return
            path = core.resolve_lore_file(profile, filename)
            path.write_text(content + "\n", encoding="utf-8")
            file_var.set(filename)
            refresh_files(filename)
            self._append_log(f"[LORE] Saved {profile}/{filename}")
            messagebox.showinfo("Lore saved", f"Saved {filename} for {core.server_display_name(self.settings, profile)}.", parent=win)

        existing_combo.bind("<<ComboboxSelected>>", load_selected)
        row = ttk.Frame(outer)
        row.pack(fill="x")
        ttk.Button(row, text="New", command=new_lore).pack(side="left")
        ttk.Button(row, text="Load", command=load_selected).pack(side="left", padx=(7, 0))
        ttk.Button(row, text="Save Lore", command=save_lore).pack(side="right")
        ttk.Button(row, text="Close", command=win.destroy).pack(side="right", padx=(0, 7))
        refresh_files()

    def _refresh_campaigns(self, select=None):
        if not hasattr(self, "campaign_combo"):
            return
        server=self._selected_server_profile()
        campaigns=core.list_campaigns(server)
        ids=[str(c.get("id") or c.get("name") or "default") for c in campaigns]
        self.campaign_combo["values"]=ids
        desired=core.sanitize_campaign_id(select or self.settings.get("campaign_id","default"))
        if desired not in ids: desired=ids[0] if ids else "default"
        self.campaign_var.set(desired)
        self.settings["campaign_id"]=desired
        core.save_settings(self.settings)
        meta=core.load_campaign_metadata({**self.settings,"server_profile":server,"campaign_id":desired})
        self.campaign_status_var.set(str(meta.get("name") or desired))

    def _on_campaign_changed(self, event=None):
        if self.running:
            return
        cid=core.sanitize_campaign_id(self.campaign_var.get())
        self.settings["campaign_id"]=cid; core.save_settings(self.settings)
        self._load_campaign_memory_ui(); self._refresh_dm_cast()
        meta=core.load_campaign_metadata({**self.settings,"server_profile":self._selected_server_profile(),"campaign_id":cid})
        self.campaign_status_var.set(str(meta.get("name") or cid))
        self._append_log(f"[CAMPAIGN] Loaded campaign: {cid}")

    def _new_campaign(self):
        if self.running: return
        name=simpledialog.askstring("New Campaign","Campaign name:",parent=self.root)
        if not name: return
        description=simpledialog.askstring("New Campaign","Short campaign description (optional):",parent=self.root) or ""
        cid=core.sanitize_campaign_id(name)
        try:
            core.create_campaign(self._selected_server_profile(),cid,name,description)
            self._refresh_campaigns(select=cid); self._refresh_dm_cast()
            self._append_log(f"[CAMPAIGN] Created campaign: {name}")
        except Exception as exc: messagebox.showerror("Could not create campaign",str(exc),parent=self.root)

    def _rename_campaign(self):
        if self.running: return
        old=core.sanitize_campaign_id(self.campaign_var.get())
        name=simpledialog.askstring("Rename Campaign","New campaign name:",initialvalue=old,parent=self.root)
        if not name: return
        new=core.sanitize_campaign_id(name)
        try:
            core.rename_campaign(self._selected_server_profile(),old,new,name)
            self.settings["campaign_id"]=new; core.save_settings(self.settings)
            self._refresh_campaigns(select=new); self._refresh_dm_cast()
        except Exception as exc: messagebox.showerror("Could not rename campaign",str(exc),parent=self.root)

    def _delete_campaign(self):
        if self.running: return
        cid=core.sanitize_campaign_id(self.campaign_var.get())
        campaigns=core.list_campaigns(self._selected_server_profile())
        if len(campaigns)<=1:
            messagebox.showinfo("Keep one campaign","Create another campaign before deleting the last campaign.",parent=self.root); return
        if not messagebox.askyesno("Delete Campaign",f"Delete campaign '{cid}'?\n\nNPC profile files and their personal memory are NOT deleted.",parent=self.root): return
        core.delete_campaign(self._selected_server_profile(),cid)
        self._refresh_campaigns(); self._refresh_dm_cast()

    def _toggle_cast_membership(self):
        meta=self._selected_cast_meta()
        if not meta: return
        settings={**self.settings,"server_profile":self._selected_server_profile(),"campaign_id":self.campaign_var.get()}
        data=core.load_campaign_memory(settings)
        all_names=[m.get("name") for m,_ in self._cast_profile_rows(raw=True)]
        members=data.get("npc_members")
        if members is None: members=list(all_names)
        key=str(meta.get("name") or "").casefold()
        members=[x for x in members if str(x).strip()]
        existing=next((x for x in members if str(x).casefold()==key),None)
        if existing: members.remove(existing)
        else: members.append(meta.get("name"))
        core.save_campaign_memory(settings,{"npc_members":members})
        self._refresh_dm_cast()

    def _cast_profile_rows(self, raw=False):
        profile = self._selected_server_profile()
        rows = []
        for path in core.list_character_profiles(profile):
            try:
                meta = core.character_profile_metadata(path)
            except Exception:
                continue
            if meta.get("profile_type") != "NPC":
                continue
            memory_settings = dict(self.settings)
            memory_settings["server_profile"] = profile
            memory_settings["character_name"] = meta.get("name") or "Unknown"
            _, memory_path, _, _ = core._memory_paths(memory_settings)
            updated = ""
            if memory_path.exists():
                try:
                    data = __import__("json").loads(memory_path.read_text(encoding="utf-8"))
                    updated = str(data.get("updated") or "")
                    if not updated:
                        updated = __import__("datetime").datetime.fromtimestamp(memory_path.stat().st_mtime).strftime("%Y-%m-%d")
                except Exception:
                    updated = ""
            rows.append((meta, updated))
        if raw:
            return rows
        settings={**self.settings,"server_profile":profile,"campaign_id":getattr(self,"campaign_var",tk.StringVar(value=self.settings.get("campaign_id","default"))).get()}
        data=core.load_campaign_memory(settings)
        members=data.get("npc_members")
        if members is None:
            member_keys={str(meta.get("name") or "").casefold() for meta,_ in rows}
        else:
            member_keys={str(x).casefold() for x in members}
        return [(meta, updated, str(meta.get("name") or "").casefold() in member_keys) for meta,updated in rows]

    def _refresh_dm_cast(self):
        if not hasattr(self, "dm_cast_tree"):
            return
        self._dm_cast_meta = {}
        for item in self.dm_cast_tree.get_children():
            self.dm_cast_tree.delete(item)
        for meta, updated, member in self._cast_profile_rows():
            iid = self.dm_cast_tree.insert("", "end", values=(meta.get("name", "Unknown"), "Yes" if member else "—", updated[:16]))
            self._dm_cast_meta[iid] = meta
        self._load_campaign_memory_ui()
        if not self.dm_cast_tree.get_children():
            self._set_dm_cast_detail("No NPC profiles found. Edit or create a character and set Profile Type to NPC.")

    def _selected_cast_meta(self):
        selected = self.dm_cast_tree.selection() if hasattr(self, "dm_cast_tree") else ()
        if not selected:
            return None
        return getattr(self, "_dm_cast_meta", {}).get(selected[0])

    def _set_dm_cast_detail(self, text):
        if not hasattr(self, "dm_cast_detail_text"):
            return
        self.dm_cast_detail_text.configure(state="normal")
        self.dm_cast_detail_text.delete("1.0", "end")
        self.dm_cast_detail_text.insert("1.0", text or "")
        self.dm_cast_detail_text.configure(state="disabled")

    def _on_dm_cast_selected(self, event=None):
        meta = self._selected_cast_meta()
        if not meta:
            return
        settings = dict(self.settings)
        settings["server_profile"] = self._selected_server_profile()
        settings["character_name"] = meta.get("name") or "Unknown"
        try:
            memory, summary = core.load_persistent_memory(settings)
            chars = memory.get("characters", {}) if isinstance(memory, dict) else {}
            threads = memory.get("story_threads", []) if isinstance(memory, dict) else []
            detail = [f"{meta.get('name', 'Unknown')}", f"Profile: {meta.get('filename', '')}", "Type: NPC"]
            if summary:
                detail += ["", "Recent continuity:", summary[:700]]
            if chars:
                detail += ["", f"Relationships remembered: {len(chars)}"]
            open_threads = [t for t in threads if isinstance(t, dict) and str(t.get("status", "open")).casefold() != "resolved"]
            if open_threads:
                detail += [f"Open story threads: {len(open_threads)}"]
            shared = memory.get("shared_with_players", {}) if isinstance(memory, dict) else {}
            if isinstance(shared, dict) and shared:
                detail += [f"Players with remembered disclosures: {len(shared)}"]
            self._set_dm_cast_detail("\n".join(detail))
        except Exception as exc:
            self._set_dm_cast_detail(f"Could not read NPC memory: {exc}")

    def _briefing_window(self, title, text):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("780x680")
        win.transient(self.root)
        body = tk.Text(win, wrap="word", bg="#1e1f22", fg="#dbdee1", insertbackground="#dbdee1",
                       selectbackground="#5865f2", selectforeground="#ffffff", relief="flat", bd=0,
                       padx=12, pady=10, font=("Segoe UI", 10))
        body.pack(fill="both", expand=True, padx=10, pady=(10, 6))
        body.insert("1.0", text)
        body.configure(state="disabled")
        bar = ttk.Frame(win); bar.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bar, text="Close", command=win.destroy).pack(side="right")

    def _npc_briefing_text(self, meta):
        settings = dict(self.settings)
        settings["server_profile"] = self._selected_server_profile()
        settings["character_name"] = meta.get("name") or "Unknown"
        memory, summary = core.load_persistent_memory(settings)
        lines = [f"{meta.get('name','Unknown').upper()} — NPC BRIEFING", ""]
        emo = memory.get("emotional_state", {}) if isinstance(memory, dict) else {}
        if isinstance(emo, dict) and (emo.get("summary") or emo.get("emotions")):
            lines += ["CURRENT STATE", str(emo.get("summary") or ", ".join(emo.get("emotions") or [])), ""]
        if summary:
            lines += ["RECENT CONTINUITY", summary[:1400], ""]
        threads=[x for x in memory.get("story_threads",[]) if isinstance(x,dict) and str(x.get("status","active")).casefold() not in ("resolved","abandoned")]
        if threads:
            lines += ["ACTIVE THREADS"] + [f"• {x.get('summary','')} [{x.get('status','active')}]" for x in threads[-8:]] + [""]
        commits=[x for x in memory.get("commitments",[]) if isinstance(x,dict) and str(x.get("status","active")).casefold() not in ("fulfilled","cancelled","resolved")]
        if commits:
            lines += ["OUTSTANDING COMMITMENTS"] + [f"• {x.get('summary','')}" for x in commits[-8:]] + [""]
        know=[x for x in memory.get("character_knowledge",[]) if isinstance(x,dict) and str(x.get("privacy","character")).casefold() != "dm_only"]
        if know:
            lines += ["IMPORTANT KNOWLEDGE"]
            for x in know[-12:]:
                src=str(x.get("source") or "unknown source")
                conf=str(x.get("confidence") or "known")
                lines.append(f"• {x.get('fact','')} — {conf}; source: {src}")
            lines.append("")
        chars=memory.get("characters",{}) if isinstance(memory,dict) else {}
        if isinstance(chars,dict) and chars:
            lines += ["RELATIONSHIPS"]
            for name, rec in list(chars.items())[-10:]:
                if isinstance(rec,dict):
                    rel=str(rec.get("relationship") or rec.get("notes") or "").strip()
                    lines.append(f"• {name}: {rel[:260] if rel else 'remembered contact'}")
            lines.append("")
        shared=memory.get("shared_with_players",{}) if isinstance(memory,dict) else {}
        if isinstance(shared,dict) and shared:
            lines += ["PREVIOUSLY SHARED WITH PLAYERS"]
            for person, entries in shared.items():
                facts=[str(x.get("fact") or "").strip() for x in entries if isinstance(x,dict) and str(x.get("fact") or "").strip()]
                if facts:
                    lines.append(f"{person}:")
                    lines.extend([f"  • {f}" for f in facts[-8:]])
            lines.append("")
        approved=memory.get("approved_development",[]) if isinstance(memory,dict) else []
        if approved:
            lines += ["APPROVED CHARACTER DEVELOPMENT"] + [f"• {x.get('statement','') if isinstance(x,dict) else x}" for x in approved[-6:]] + [""]
        return "\n".join(lines).strip()

    def _show_npc_briefing(self):
        meta=self._selected_cast_meta()
        if not meta:
            messagebox.showinfo("NPC Briefing","Select an NPC first.",parent=self.root); return
        try: self._briefing_window(f"NPC Briefing — {meta.get('name','NPC')}", self._npc_briefing_text(meta))
        except Exception as exc: messagebox.showerror("NPC Briefing",str(exc),parent=self.root)

    def _show_campaign_briefing(self):
        settings={**self.settings,"server_profile":self._selected_server_profile(),"campaign_id":self.campaign_var.get()}
        camp=core.load_campaign_memory(settings)
        meta=core.load_campaign_metadata(settings)
        rows=self._cast_profile_rows()
        members=[m for m,updated,member in rows if member]
        title=str(meta.get("name") or camp.get("name") or self.campaign_var.get())
        lines=[f"{title.upper()} — CAMPAIGN BRIEFING", ""]
        desc=str(meta.get("description") or "").strip()
        if desc: lines += ["CAMPAIGN", desc, ""]
        situation=str(meta.get("current_situation") or "").strip()
        if situation: lines += ["CURRENT SITUATION", situation, ""]
        active=[x for x in camp.get("story_beats",[]) if isinstance(x,dict) and str(x.get("status","Planned")).casefold() in ("active","planned")]
        if active:
            lines += ["STORYLINE — CURRENT / UPCOMING"]
            for x in active[:12]: lines.append(f"• [{x.get('status','Planned')}] {x.get('title','')}" + (f" — {x.get('description','')[:260]}" if x.get('description') else ""))
            lines.append("")
        objectives=[x for x in camp.get("objectives",[]) if isinstance(x,dict) and str(x.get("status","Open")).casefold() not in ("resolved","dropped")]
        if objectives:
            lines += ["OPEN QUESTIONS / OBJECTIVES"] + [f"• {x.get('title','')}" for x in objectives[:12]] + [""]
        sessions=[x for x in camp.get("session_log",[]) if isinstance(x,dict)]
        if sessions:
            lines += ["RECENT SESSION LOG"]
            for x in sessions[-3:]: lines.append(f"• {x.get('date','')}: {str(x.get('summary') or '')[:500]}")
            lines.append("")
        dm=str(camp.get("dm_notes") or "").strip()
        if dm: lines += ["DM CAMPAIGN NOTES", dm, ""]
        shared=str(camp.get("shared_memory") or "").strip()
        if shared: lines += ["SHARED CAMPAIGN CONTINUITY", shared, ""]
        player_notes=[x for x in camp.get("player_notes",[]) if isinstance(x,dict)]
        if player_notes:
            lines += ["PLAYER / PARTY DM NOTES"]
            for x in player_notes[:12]: lines.append(f"• {x.get('player','')}: {x.get('notes','')}")
            lines.append("")
        locations=[x for x in camp.get("locations",[]) if isinstance(x,dict) and str(x.get("status","Active")).casefold() != "inactive"]
        if locations:
            lines += ["IMPORTANT LOCATIONS"] + [f"• {x.get('name','')}: {x.get('notes','')}" for x in locations[:10]] + [""]
        lines += [f"CAMPAIGN NPCS ({len(members)})"]
        for m in members:
            ms={**self.settings,"server_profile":self._selected_server_profile(),"character_name":m.get("name") or "Unknown"}
            mem,summary=core.load_persistent_memory(ms)
            threads=[x for x in mem.get("story_threads",[]) if isinstance(x,dict) and str(x.get("status","active")).casefold() not in ("resolved","abandoned")]
            commits=[x for x in mem.get("commitments",[]) if isinstance(x,dict) and str(x.get("status","active")).casefold() not in ("fulfilled","cancelled","resolved")]
            lines.append(f"\n{m.get('name','Unknown')}")
            if summary: lines.append(f"  Recent: {summary[:420]}")
            for x in threads[-3:]: lines.append(f"  Thread: {x.get('summary','')}")
            for x in commits[-3:]: lines.append(f"  Commitment: {x.get('summary','')}")
        lines += ["", "DM planning data and NPC continuity do not modify Player Knowledge."]
        self._briefing_window(f"Campaign Briefing — {title}", "\n".join(lines))

    def _campaign_manager_settings(self):
        return {**self.settings, "server_profile": self._selected_server_profile(),
                "campaign_id": getattr(self, "campaign_var", tk.StringVar(value=self.settings.get("campaign_id", "default"))).get()}

    def _open_campaign_manager(self):
        if self.running:
            messagebox.showinfo("Campaign Manager", "Stop Role Weaver before editing campaign management data.", parent=self.root)
            return
        settings = self._campaign_manager_settings()
        meta = core.load_campaign_metadata(settings)
        memory = core.load_campaign_memory(settings)

        win = tk.Toplevel(self.root)
        win.title(f"Campaign Manager — {meta.get('name') or settings['campaign_id']}")
        win.geometry("980x760")
        win.minsize(820, 620)
        win.transient(self.root)

        header = ttk.Frame(win, padding=(10, 10, 10, 6)); header.pack(fill="x")
        ttk.Label(header, text="Campaign Manager", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Label(header, text="DM planning data never modifies Player Knowledge.", foreground="#949ba4").pack(side="left", padx=(12, 0))

        nb = ttk.Notebook(win); nb.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        overview = ttk.Frame(nb, padding=10); storyline = ttk.Frame(nb, padding=10)
        objectives = ttk.Frame(nb, padding=10); locations = ttk.Frame(nb, padding=10)
        players = ttk.Frame(nb, padding=10); sessions = ttk.Frame(nb, padding=10); roster = ttk.Frame(nb, padding=10)
        nb.add(overview, text="Overview"); nb.add(storyline, text="Storyline")
        nb.add(objectives, text="Objectives"); nb.add(locations, text="Locations")
        nb.add(players, text="Player Notes"); nb.add(sessions, text="Session Log"); nb.add(roster, text="NPC Roster")

        def text_widget(parent, height=5):
            return tk.Text(parent, height=height, wrap="word", bg="#1e1f22", fg="#dbdee1",
                           insertbackground="#dbdee1", selectbackground="#5865f2", selectforeground="#ffffff",
                           relief="flat", bd=0, padx=8, pady=7, font=("Segoe UI", 9))

        def save_state():
            core.save_campaign_memory(settings, memory)

        def save_overview():
            name = name_var.get().strip() or settings["campaign_id"]
            core.save_campaign_metadata(settings, {
                "name": name,
                "description": desc_text.get("1.0", "end-1c").strip(),
                "current_situation": situation_text.get("1.0", "end-1c").strip(),
            })
            memory["dm_notes"] = dm_text.get("1.0", "end-1c").strip()
            memory["shared_memory"] = shared_text.get("1.0", "end-1c").strip()
            save_state()
            self.campaign_status_var.set(name)
            self._load_campaign_memory_ui()
            self._append_log("[CAMPAIGN] Campaign Manager overview saved.")

        # Overview
        ttk.Label(overview, text="Campaign Identity", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        row = ttk.Frame(overview); row.pack(fill="x", pady=(6, 8))
        ttk.Label(row, text="Name:", width=16).pack(side="left")
        name_var = tk.StringVar(value=str(meta.get("name") or settings["campaign_id"]))
        ttk.Entry(row, textvariable=name_var).pack(side="left", fill="x", expand=True)
        ttk.Label(overview, text="Description").pack(anchor="w")
        desc_text = text_widget(overview, 4); desc_text.pack(fill="x", pady=(3, 8)); desc_text.insert("1.0", str(meta.get("description") or ""))
        ttk.Label(overview, text="Current Situation").pack(anchor="w")
        situation_text = text_widget(overview, 4); situation_text.pack(fill="x", pady=(3, 8)); situation_text.insert("1.0", str(meta.get("current_situation") or ""))
        split = ttk.PanedWindow(overview, orient="horizontal"); split.pack(fill="both", expand=True)
        left = ttk.Frame(split); right = ttk.Frame(split); split.add(left, weight=1); split.add(right, weight=1)
        ttk.Label(left, text="Shared Campaign Continuity").pack(anchor="w")
        shared_text = text_widget(left, 7); shared_text.pack(fill="both", expand=True, pady=(3,0)); shared_text.insert("1.0", str(memory.get("shared_memory") or ""))
        ttk.Label(right, text="DM-only Notes").pack(anchor="w", padx=(8,0))
        dm_text = text_widget(right, 7); dm_text.pack(fill="both", expand=True, pady=(3,0), padx=(8,0)); dm_text.insert("1.0", str(memory.get("dm_notes") or ""))
        ttk.Button(overview, text="Save Overview", command=save_overview, style="Accent.TButton").pack(anchor="e", pady=(8,0))

        def record_dialog(title, fields, initial=None):
            initial = dict(initial or {})
            dlg = tk.Toplevel(win); dlg.title(title); dlg.transient(win); dlg.grab_set(); dlg.geometry("600x520")
            body = ttk.Frame(dlg, padding=10); body.pack(fill="both", expand=True)
            controls = {}
            for spec in fields:
                key,label,kind,*rest = spec
                ttk.Label(body, text=label).pack(anchor="w", pady=(6,2))
                val = str(initial.get(key) or "")
                if kind == "text":
                    w = text_widget(body, rest[0] if rest else 5); w.pack(fill="both" if (rest and rest[0] >= 5) else "x", expand=bool(rest and rest[0] >= 5)); w.insert("1.0", val); controls[key]=(kind,w)
                elif kind == "combo":
                    var=tk.StringVar(value=val or (rest[0][0] if rest and rest[0] else "")); w=ttk.Combobox(body,textvariable=var,state="readonly",values=rest[0] if rest else []); w.pack(fill="x"); controls[key]=(kind,var)
                else:
                    var=tk.StringVar(value=val); ttk.Entry(body,textvariable=var).pack(fill="x"); controls[key]=(kind,var)
            result={}
            def ok():
                for key,(kind,obj) in controls.items():
                    result[key] = obj.get("1.0","end-1c").strip() if kind=="text" else obj.get().strip()
                dlg.destroy()
            bar=ttk.Frame(dlg,padding=(10,0,10,10)); bar.pack(fill="x")
            ttk.Button(bar,text="Cancel",command=dlg.destroy).pack(side="right")
            ttk.Button(bar,text="Save",command=ok,style="Accent.TButton").pack(side="right",padx=(0,6))
            dlg.wait_window()
            return result or None

        def ensure_id(rec):
            rec=dict(rec or {})
            rec.setdefault("id", __import__("uuid").uuid4().hex)
            rec["updated"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
            return rec

        # Generic CRUD builders
        def make_crud_tab(parent, key, columns, fields, add_label, extra_buttons=None):
            tree=ttk.Treeview(parent, columns=[c[0] for c in columns], show="headings", height=16)
            for cid,label,width in columns:
                tree.heading(cid,text=label); tree.column(cid,width=width,anchor="w",stretch=(cid==columns[-1][0]))
            tree.pack(fill="both",expand=True)
            def refresh():
                for i in tree.get_children(): tree.delete(i)
                for idx,rec in enumerate(memory.get(key, [])):
                    if not isinstance(rec,dict): continue
                    vals=[]
                    for cid,_,_ in columns:
                        vals.append(str(rec.get(cid) or ""))
                    tree.insert("","end",iid=str(idx),values=vals)
            def selected_index():
                sel=tree.selection()
                return int(sel[0]) if sel else None
            def add():
                rec=record_dialog(add_label,fields,{})
                if rec:
                    memory.setdefault(key,[]).append(ensure_id(rec)); save_state(); refresh()
            def edit(event=None):
                idx=selected_index()
                if idx is None: return
                current=memory[key][idx]
                rec=record_dialog(f"Edit {add_label}",fields,current)
                if rec:
                    rec["id"]=current.get("id") or __import__("uuid").uuid4().hex
                    memory[key][idx]=ensure_id(rec); save_state(); refresh()
            def delete():
                idx=selected_index()
                if idx is None: return
                if messagebox.askyesno("Delete", "Delete the selected campaign record?", parent=win):
                    memory[key].pop(idx); save_state(); refresh()
            bar=ttk.Frame(parent); bar.pack(fill="x",pady=(6,0))
            ttk.Button(bar,text="Add",command=add).pack(side="left")
            ttk.Button(bar,text="Edit",command=edit).pack(side="left",padx=(5,0))
            ttk.Button(bar,text="Delete",command=delete).pack(side="left",padx=(5,0))
            if extra_buttons: extra_buttons(bar,tree,refresh,selected_index)
            tree.bind("<Double-1>",edit); refresh()
            return tree,refresh

        story_fields=[("title","Story Beat","entry"),("status","Status","combo",["Planned","Active","Completed","Skipped"]),
                      ("importance","Importance","combo",["1","2","3","4","5"]),("description","Description / DM Notes","text",6),
                      ("npcs","NPCs Involved","entry"),("completion_notes","Completion Notes","text",3)]
        def story_extra(bar,tree,refresh,selected_index):
            def move(delta):
                i=selected_index()
                if i is None: return
                j=i+delta
                if 0<=j<len(memory["story_beats"]):
                    memory["story_beats"][i],memory["story_beats"][j]=memory["story_beats"][j],memory["story_beats"][i]
                    save_state(); refresh(); tree.selection_set(str(j)); tree.see(str(j))
            def complete():
                i=selected_index()
                if i is None:return
                memory["story_beats"][i]["status"]="Completed"; memory["story_beats"][i]["completed"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
                save_state(); refresh()
            ttk.Button(bar,text="Move Up",command=lambda:move(-1)).pack(side="left",padx=(12,0))
            ttk.Button(bar,text="Move Down",command=lambda:move(1)).pack(side="left",padx=(5,0))
            ttk.Button(bar,text="Mark Completed",command=complete,style="Accent.TButton").pack(side="right")
        make_crud_tab(storyline,"story_beats",[("status","Status",90),("title","Story Beat",300),("importance","Importance",80),("npcs","NPCs",220)],story_fields,"Story Beat",story_extra)

        obj_fields=[("title","Objective / Open Question","entry"),("status","Status","combo",["Open","Active","Resolved","Dropped"]),("notes","Notes / Resolution","text",7)]
        make_crud_tab(objectives,"objectives",[("status","Status",90),("title","Objective / Open Question",360),("notes","Notes",360)],obj_fields,"Objective / Open Question")
        loc_fields=[("name","Location","entry"),("status","Status","combo",["Active","Known","Inactive"]),("notes","DM Notes","text",8)]
        make_crud_tab(locations,"locations",[("name","Location",220),("status","Status",90),("notes","Notes",500)],loc_fields,"Important Location")
        player_fields=[("player","Player Character","entry"),("notes","DM Notes (does not modify Player Knowledge)","text",9)]
        make_crud_tab(players,"player_notes",[("player","Player Character",220),("notes","DM Notes",590)],player_fields,"Player Note")

        session_fields=[("date","Date / Session","entry"),("summary","Editable Session Summary","text",8),("npcs","NPCs Involved","entry"),("players","Players Involved","entry"),("story_progress","Story Progress","text",4)]
        def session_extra(bar,tree,refresh,selected_index):
            def generate():
                rows=self._cast_profile_rows(); members=[m for m,u,member in rows if member]
                parts=[]; npcs=[]
                for m in members:
                    ms={**self.settings,"server_profile":self._selected_server_profile(),"character_name":m.get("name") or "Unknown"}
                    mem,summ=core.load_persistent_memory(ms)
                    if summ:
                        npcs.append(m.get("name") or "Unknown"); parts.append(f"{m.get('name')}: {summ[:500]}")
                initial={"date":__import__("datetime").datetime.now().strftime("%Y-%m-%d"),"summary":"\n\n".join(parts),"npcs":", ".join(npcs),"players":"","story_progress":""}
                rec=record_dialog("Create Session Summary",session_fields,initial)
                if rec:
                    memory.setdefault("session_log",[]).append(ensure_id(rec)); save_state(); refresh()
            ttk.Button(bar,text="Create from NPC Continuity",command=generate,style="Accent.TButton").pack(side="right")
        make_crud_tab(sessions,"session_log",[("date","Date",120),("summary","Session Summary",520),("npcs","NPCs",180)],session_fields,"Session Log Entry",session_extra)

        # NPC roster with direct briefing access
        roster_tree=ttk.Treeview(roster,columns=("npc","member","last","outstanding"),show="headings",height=17)
        for cid,label,w in (("npc","NPC",220),("member","Campaign",90),("last","Memory Updated",150),("outstanding","Outstanding",320)):
            roster_tree.heading(cid,text=label); roster_tree.column(cid,width=w,anchor="w",stretch=(cid=="outstanding"))
        roster_tree.pack(fill="both",expand=True)
        roster_meta={}
        for m,updated,member in self._cast_profile_rows():
            if not member: continue
            ms={**self.settings,"server_profile":self._selected_server_profile(),"character_name":m.get("name") or "Unknown"}
            mem,_=core.load_persistent_memory(ms)
            threads=[x for x in mem.get("story_threads",[]) if isinstance(x,dict) and str(x.get("status","active")).casefold() not in ("resolved","abandoned")]
            commits=[x for x in mem.get("commitments",[]) if isinstance(x,dict) and str(x.get("status","active")).casefold() not in ("fulfilled","cancelled","resolved")]
            outstanding=f"{len(threads)} threads; {len(commits)} commitments"
            iid=roster_tree.insert("","end",values=(m.get("name","Unknown"),"Yes",updated[:16],outstanding)); roster_meta[iid]=m
        def roster_brief(event=None):
            sel=roster_tree.selection()
            if not sel:return
            m=roster_meta.get(sel[0]);
            if m:self._briefing_window(f"NPC Briefing — {m.get('name','NPC')}",self._npc_briefing_text(m))
        roster_tree.bind("<Double-1>",roster_brief)
        rb=ttk.Frame(roster); rb.pack(fill="x",pady=(6,0))
        ttk.Button(rb,text="NPC Briefing",command=roster_brief,style="Accent.TButton").pack(side="left")
        ttk.Label(rb,text="Double-click an NPC to open the briefing.",foreground="#949ba4").pack(side="left",padx=(10,0))

        footer=ttk.Frame(win,padding=(10,0,10,10)); footer.pack(fill="x")
        ttk.Button(footer,text="Campaign Briefing",command=self._show_campaign_briefing,style="Accent.TButton").pack(side="left")
        ttk.Button(footer,text="Close",command=lambda:(save_overview(),win.destroy())).pack(side="right")

    def _load_selected_cast_npc(self, event=None):
        if self.running:
            messagebox.showinfo("Stop Role Weaver first", "Stop the current character before switching NPCs.", parent=self.root)
            return
        meta = self._selected_cast_meta()
        if not meta:
            return
        filename = meta.get("filename", "")
        values = list(self.character_profile_combo["values"])
        if filename not in values:
            self._refresh_character_profiles(initial=False)
        self.character_profile_var.set(filename)
        self._load_selected_character_profile(save_setting=True)
        self._append_log(f"[CAST] Loaded NPC: {meta.get('name', filename)}")

    def _edit_selected_cast_npc(self):
        if self.running:
            return
        meta = self._selected_cast_meta()
        if not meta:
            return
        self.character_profile_var.set(meta.get("filename", ""))
        self._open_character_editor(edit_selected=True)

    def _load_campaign_memory_ui(self):
        if not hasattr(self, "campaign_shared_text"):
            return
        settings = dict(self.settings)
        settings["server_profile"] = self._selected_server_profile()
        settings["campaign_id"] = getattr(self, "campaign_var", tk.StringVar(value=settings.get("campaign_id","default"))).get()
        data = core.load_campaign_memory(settings)
        self.campaign_shared_text.delete("1.0", "end")
        self.campaign_shared_text.insert("1.0", str(data.get("shared_memory") or ""))
        self.campaign_dm_text.delete("1.0", "end")
        self.campaign_dm_text.insert("1.0", str(data.get("dm_notes") or ""))

    def _save_campaign_memory(self):
        settings = dict(self.settings)
        settings["server_profile"] = self._selected_server_profile()
        settings["campaign_id"] = getattr(self, "campaign_var", tk.StringVar(value=settings.get("campaign_id","default"))).get()
        self.settings["campaign_id"] = settings["campaign_id"]
        core.save_settings(self.settings)
        core.save_campaign_memory(settings, {
            "shared_memory": self.campaign_shared_text.get("1.0", "end-1c").strip(),
            "dm_notes": self.campaign_dm_text.get("1.0", "end-1c").strip(),
        })
        self._append_log("[CAMPAIGN] Saved shared Campaign Memory. DM-only notes remain outside AI character context.")

    def _export_campaign_pack(self):
        self._save_campaign_memory()
        server = self._selected_server_profile()
        target = filedialog.asksaveasfilename(
            parent=self.root, title="Export Role Weaver Campaign Pack",
            defaultextension=".zip", filetypes=[("Role Weaver Campaign Pack", "*.zip")],
            initialfile=f"RoleWeaver_Campaign_{self.settings.get('campaign_id','default')}.zip",
        )
        if not target:
            return
        try:
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                camp = core.campaign_dir({**self.settings, "server_profile": server, "campaign_id": getattr(self,"campaign_var",tk.StringVar(value="default")).get()})
                for file in camp.rglob("*"):
                    if file.is_file():
                        zf.write(file, Path("campaign") / file.relative_to(camp))
                for meta, _, member in self._cast_profile_rows():
                    if not member:
                        continue
                    path = Path(meta["path"])
                    zf.write(path, Path("characters") / path.name)
                    ai_settings = core.character_ai_settings_path(path)
                    if ai_settings.exists():
                        zf.write(ai_settings, Path("characters") / ai_settings.name)
                    mem_settings = {**self.settings, "server_profile": server, "character_name": meta.get("name", "Unknown")}
                    base, _, _, _ = core._memory_paths(mem_settings)
                    if base.exists():
                        safe_name = core._safe_filename(meta.get("name", "Unknown"))
                        for file in base.rglob("*"):
                            if file.is_file():
                                zf.write(file, Path("memory") / safe_name / file.relative_to(base))
                manifest = f"Role Weaver Campaign Pack\nServer: {server}\nCampaign: {self.settings.get('campaign_id','default')}\nFormat: 1\n"
                zf.writestr("MANIFEST.txt", manifest)
            self._append_log(f"[CAMPAIGN] Exported campaign pack: {target}")
            messagebox.showinfo("Campaign exported", "Campaign memory, NPC profiles, and NPC continuity data were exported.", parent=self.root)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc), parent=self.root)

    def _import_campaign_pack(self):
        if self.running:
            messagebox.showinfo("Stop Role Weaver first", "Stop Role Weaver before importing campaign data.", parent=self.root)
            return
        source = filedialog.askopenfilename(parent=self.root, title="Import Role Weaver Campaign Pack", filetypes=[("ZIP files", "*.zip")])
        if not source:
            return
        if not messagebox.askyesno("Import Campaign Pack", "Import this campaign pack into the selected server? Existing files with the same names will be replaced.\n\nA backup copy of replaced files is not created by this alpha build.", parent=self.root):
            return
        server = self._selected_server_profile()
        try:
            with zipfile.ZipFile(source, "r") as zf:
                names = zf.namelist()
                for name in names:
                    pp = Path(name)
                    if pp.is_absolute() or ".." in pp.parts:
                        raise ValueError("Campaign pack contains an unsafe path.")
                camp = core.campaign_dir({**self.settings, "server_profile": server, "campaign_id": getattr(self,"campaign_var",tk.StringVar(value="default")).get()})
                char_dir = core.character_profile_dir(server)
                for name in names:
                    pp = Path(name)
                    if name.endswith("/"):
                        continue
                    data = zf.read(name)
                    if pp.parts and pp.parts[0] == "campaign" and len(pp.parts) > 1:
                        dest = camp.joinpath(*pp.parts[1:])
                    elif pp.parts and pp.parts[0] == "characters" and len(pp.parts) == 2:
                        dest = char_dir / pp.name
                    elif pp.parts and pp.parts[0] == "memory" and len(pp.parts) > 2:
                        npc_folder = pp.parts[1]
                        base = core.ROLEWEAVER_DATA_DIR / core._safe_filename(server) / npc_folder
                        dest = base.joinpath(*pp.parts[2:])
                    else:
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
            self._refresh_character_profiles(initial=False)
            self._refresh_dm_cast()
            self._append_log(f"[CAMPAIGN] Imported campaign pack: {source}")
            messagebox.showinfo("Campaign imported", "Campaign data imported. Review the Cast Manager before starting play.", parent=self.root)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc), parent=self.root)

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

        model = char_ai.get("model") or core.AI_PROVIDERS[provider]["default_model"]
        lm_url = char_ai.get("lm_studio_base_url", "http://127.0.0.1:1234/v1")
        response_length = char_ai.get("response_length_mode", "Auto")

        # Keep the backing settings object synchronized with the values shown
        # in the UI. Previously only the StringVars were updated here, leaving
        # self.settings["ai_provider"] stale until the first manual switch.
        self.settings["ai_provider"] = provider
        self.settings["model"] = model
        self.settings["lm_studio_base_url"] = lm_url
        self.settings["response_length_mode"] = response_length
        self.settings["candidate_count"] = int(char_ai.get("candidate_count", 3))

        self.provider_var.set(provider)
        self.model_var.set(model)
        self.lm_url_var.set(lm_url)
        self.length_mode_var.set(response_length)
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
        # Check immediately when a Player profile is selected. Previously this
        # check happened only when Start was pressed, and detection depended on
        # a fragile join-message pattern. Immediate feedback makes an accidental
        # profile switch visible before any RP session is started.
        self._check_selected_player_identity(allow_switch=True)

    def _check_selected_player_identity(self, allow_switch=True):
        if not self.settings.get("character_mismatch_check", True):
            return "ok"
        if core.extract_profile_type_from_prompt(self.character_prompt) != "Player":
            return "ok"
        loaded = self.character_var.get().strip()
        if not loaded or loaded in ("Unknown", "Profile error", "No profile found"):
            return "ok"
        log_path = self.log_path_var.get().strip() or core.get_server_log_path(self.settings, self._selected_server_profile())
        detected = core.detect_recent_nwn_character(log_path)
        if not detected:
            self._append_log("[IDENTITY] Could not determine the active NWN character from the current log; no mismatch decision was made.")
            return "unknown"
        if core.strip_identity_title(detected).casefold() == core.strip_identity_title(loaded).casefold():
            self._append_log(f"[IDENTITY] NWN character matches Player profile: {loaded}")
            return "ok"
        matching = self._find_profile_for_character_name(detected) if allow_switch else ""
        action = self._confirm_character_mismatch(detected, loaded, matching)
        if action == "switch" and matching:
            self.character_profile_var.set(matching)
            self._load_selected_character_profile(save_setting=True, load_ai_settings=True)
            self._append_log(f"[IDENTITY] Switched to matching Player profile: {self.character_var.get().strip()}")
            return "switched"
        if action == "keep":
            self._append_log(f"[IDENTITY WARNING] User kept profile {loaded} while NWN appears to be {detected}.")
            return "keep"
        return "cancel"

    def _server_profile_items(self):
        items = [(key, value["display_name"]) for key, value in core.SERVER_PROFILES.items()]
        discovered = self.settings.get("discovered_servers", {}) or {}
        for key, value in sorted(discovered.items(), key=lambda kv: str(kv[1].get("display_name", kv[0])).casefold()):
            name = str(value.get("display_name") or key)
            if not any(existing_key == key for existing_key, _ in items):
                items.append((key, name))
        return items

    def _refresh_server_combo(self, select_profile=None):
        items = self._server_profile_items()
        self.server_combo["values"] = [name for _, name in items]
        profile = select_profile or self.settings.get("server_profile", "AUTO")
        self.server_var.set(core.server_display_name(self.settings, profile))

    def _selected_server_profile(self):
        selected = self.server_var.get() if hasattr(self, "server_var") else ""
        for key, name in self._server_profile_items():
            if name == selected:
                return key
        return self.settings.get("server_profile", "AUTO")

    def _on_server_changed(self, event=None):
        if self.running:
            return
        profile = self._selected_server_profile()
        current = core.load_settings()
        current["server_profile"] = profile
        current["log_path"] = core.get_server_log_path(current, profile)
        core.save_settings(current)
        self.settings = current
        self.log_path_var.set(current["log_path"])
        self._refresh_character_profiles(initial=False)
        self._refresh_campaigns(select="default")
        self._refresh_dm_cast()
        self._append_log(
            f"[WORLD] Selected {core.server_display_name(self.settings, profile)}; "
            "character, lore, campaign, and memory scope updated."
        )

    def _rescan_server_logs(self):
        if self.running:
            return
        self.settings = core.refresh_discovered_servers(core.load_settings())
        selected = self.settings.get("server_profile", "AUTO")
        core.save_settings(self.settings)
        self._refresh_server_combo(select_profile=selected)
        count = len(self.settings.get("discovered_servers", {}) or {})
        self._append_log(f"[WORLD] Log scan complete: {count} local world profile(s) available.")

    def _browse_log_file(self):
        filename = filedialog.askopenfilename(
            title="Select Neverwinter Nights client log",
            filetypes=[("Text logs", "*.txt"), ("All files", "*.*")],
        )
        if not filename:
            return
        self.log_path_var.set(filename)
        self.settings = core.load_settings()
        detected = core.detect_world_from_log(filename)
        if detected:
            core.register_discovered_server(self.settings, detected)
            profile = detected["id"]
            self.settings["server_profile"] = profile
            self.settings["log_path"] = filename
            core.save_settings(self.settings)
            self._refresh_server_combo(select_profile=profile)
            self.server_var.set(core.server_display_name(self.settings, profile))
            self._refresh_character_profiles(initial=False)
            self._refresh_campaigns(select="default")
            self._refresh_dm_cast()
            self._append_log(
                f"[WORLD] Detected {detected['display_name']} from the selected log "
                f"(format: {detected.get('parser_profile', 'adaptive')})."
            )

    def _apply_server_settings(self):
        profile = self._selected_server_profile()
        path = self.log_path_var.get().strip()
        if not path:
            path = core.get_server_log_path(self.settings, profile)
            self.log_path_var.set(path)
        settings = core.load_settings()
        # Re-detect the selected log at Start. This lets AUTO follow a different
        # server/log without requiring a bundled compatibility entry.
        detected = core.detect_world_from_log(path)
        if detected and profile == "AUTO":
            core.register_discovered_server(settings, detected)
            profile = detected["id"]
            settings["server_profile"] = profile
            self.settings = settings
            self._refresh_server_combo(select_profile=profile)
            self.server_var.set(core.server_display_name(settings, profile))
        paths = dict(settings.get("server_log_paths", {}) or {})
        paths[profile] = path
        settings["server_profile"] = profile
        settings["server_log_paths"] = paths
        settings["log_path"] = path
        if detected:
            core.register_discovered_server(settings, detected)
            settings["parser_profile"] = detected.get("parser_profile", "adaptive")
        else:
            item = (settings.get("discovered_servers", {}) or {}).get(profile, {})
            settings["parser_profile"] = item.get("parser_profile", settings.get("parser_profile", "adaptive"))
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
        provider = self.provider_var.get() or "OpenAI"
        if provider not in core.AI_PROVIDERS:
            provider = "OpenAI"
            self.provider_var.set(provider)

        # A model identifier is provider-specific. When the user explicitly
        # changes provider, start with that provider's known-safe default rather
        # than carrying a Gemini model into OpenAI (or vice versa).
        model = core.AI_PROVIDERS[provider]["default_model"]
        self.model_var.set(model)
        self.settings["ai_provider"] = provider
        self.settings["model"] = model
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

    def _find_profile_for_character_name(self, detected_name):
        target=core.strip_identity_title(detected_name).casefold()
        matches=[]
        for path in core.list_character_profiles(self._selected_server_profile()):
            try:
                text,name=core.load_character_profile(path)
                if core.extract_profile_type_from_prompt(text)!="Player": continue
                if core.strip_identity_title(name).casefold()==target:
                    matches.append(path.name)
            except Exception: pass
        return matches[0] if len(matches)==1 else ""

    def _confirm_character_mismatch(self, detected, loaded, matching_profile=""):
        result={"action":"cancel"}
        win=tk.Toplevel(self.root); win.title("Character Profile Mismatch"); win.transient(self.root); win.grab_set(); win.resizable(False,False)
        frame=ttk.Frame(win,padding=16); frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="Character Profile Mismatch",font=("Segoe UI",11,"bold")).pack(anchor="w")
        ttk.Label(frame,text=f"NWN appears to be using:  {detected}\nRole Weaver profile:       {loaded}\n\nContinuing with the wrong Player profile can store voice and RP memory under the wrong character.",wraplength=520).pack(anchor="w",pady=(8,12))
        row=ttk.Frame(frame); row.pack(fill="x")
        def choose(action): result["action"]=action; win.destroy()
        if matching_profile:
            ttk.Button(row,text=f"Switch to {detected}",command=lambda:choose("switch"),style="Accent.TButton").pack(side="left")
        ttk.Button(row,text="Keep Current Profile",command=lambda:choose("keep")).pack(side="left",padx=(7,0))
        ttk.Button(row,text="Cancel Start",command=lambda:choose("cancel")).pack(side="right")
        win.protocol("WM_DELETE_WINDOW",lambda:choose("cancel")); self.root.wait_window(win)
        return result["action"]

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
                    "The selected character profile must contain a line like 'Name: Example Character' or 'Character Name: Example Character'.",
                )
                return

            profile, log_path = self._apply_server_settings()

            # Player profiles are checked against the beginning of the current NWN
            # log session. NPC profiles intentionally skip this check because a DM
            # normally portrays an NPC while logged into a different NWN character.
            profile_type = core.extract_profile_type_from_prompt(self.character_prompt)
            if profile_type == "Player" and self.settings.get("character_mismatch_check", True):
                identity_action = self._check_selected_player_identity(allow_switch=True)
                if identity_action == "cancel":
                    self._append_log(f"[IDENTITY] Start cancelled for Player profile {character_name}.")
                    return
                if identity_action == "switched":
                    character_name = self.character_var.get().strip()
                    filename = self.character_profile_var.get().strip()

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
            self.rescan_logs_btn.configure(state="disabled")
            self._append_log(f"[START] AI: {provider} / {self.settings['model']}")
            self._append_log(f"[START] World / Server: {core.server_display_name(self.settings, profile)}")
            self._append_log(f"[START] Watching: {self.settings['log_path']}")
            memory_base, _, _, _ = core._memory_paths(self.settings)
            self._append_log(f"[MEMORY] Persistent RP memory: {memory_base}")
            lore_path = core.lore_dir(profile)
            lore_count = len(list(lore_path.glob("*.txt")))
            self._append_log(f"[LORE] Reference folder: {lore_path} ({lore_count} .txt file(s))")
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
                    self.settings.get("server_profile", "AUTO"),
                    self.settings.get("parser_profile", "adaptive"),
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
        self.new_character_btn.configure(state="normal")
        self.edit_character_btn.configure(state="normal")
        self.lore_editor_btn.configure(state="normal")
        self.provider_combo.configure(state="readonly")
        self.model_entry.configure(state="normal")
        self.api_entry.configure(state="normal")
        self.lm_url_entry.configure(state="normal")
        self.test_ai_btn.configure(state="normal")
        self._update_provider_ui()
        self.server_combo.configure(state="readonly")
        self.log_path_entry.configure(state="normal")
        self.browse_btn.configure(state="normal")
        self.rescan_logs_btn.configure(state="normal")
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
            self.bot._publish_draft(text)
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
        names = tuple(self.bot.relationship_character_names())
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
        _, item = self.bot._find_character_record(name)
        if not isinstance(item, dict):
            item = {"notes": str(item or "")}

        self.relationship_text.delete("1.0", "end")
        self.relationship_text.insert("1.0", item.get("relationship", "") or "")
        self.relationship_memory_text.delete("1.0", "end")
        self.relationship_memory_text.insert("1.0", item.get("notes", "") or "")

        history = item.get("interaction_history", []) if isinstance(item, dict) else []
        lines = []
        if isinstance(history, list):
            for interaction in history[-20:]:
                if not isinstance(interaction, dict):
                    continue
                stamp = str(interaction.get("timestamp") or "")[:10]
                importance = interaction.get("importance")
                summary = str(interaction.get("summary") or "").strip()
                if summary:
                    label = f"{stamp} — " if stamp else ""
                    if importance:
                        label += f"[{importance}/10] "
                    if interaction.get("private"):
                        label += "[Private Tell] "
                    lines.append(label + summary)
        self.relationship_history_text.configure(state="normal")
        self.relationship_history_text.delete("1.0", "end")
        self.relationship_history_text.insert(
            "1.0", "\n".join(lines) if lines else "No structured interactions recorded yet."
        )
        self.relationship_history_text.configure(state="disabled")

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
            self.last_relationship_names = None
            self._refresh_relationship_list()
            self._load_relationship_record()
            self._append_log(f"[MEMORY] Saved relationship/memory for {name}.")

    def _add_relationship_alias(self):
        if not self.bot: return
        name=self.relationship_character_var.get().strip()
        if not name: return
        alias=simpledialog.askstring("Add Character Alias",f"Alias/title for {name}:",parent=self.root)
        if alias and self.bot.add_character_alias(name,alias):
            self._append_log(f"[IDENTITY] Added alias '{alias}' -> {name}")
            self.last_relationship_names=None; self._refresh_relationship_list()

    def _merge_relationship_record(self):
        if not self.bot: return
        source=self.relationship_character_var.get().strip()
        names=[n for n in self.bot.relationship_character_names() if n.casefold()!=source.casefold()]
        if not source or not names:
            messagebox.showinfo("Nothing to merge","At least two remembered character records are required.",parent=self.root); return
        target=simpledialog.askstring("Merge Character Records",f"Merge '{source}' INTO which canonical character?\n\nAvailable:\n"+"\n".join(names[:30]),parent=self.root)
        if not target: return
        actual=next((n for n in names if n.casefold()==target.strip().casefold()),None)
        if not actual:
            messagebox.showerror("Character not found","Type one of the canonical names shown in the list.",parent=self.root); return
        if messagebox.askyesno("Confirm Merge",f"Merge all memory for '{source}' into '{actual}'?\n\n'{source}' will be retained as an alias.",parent=self.root):
            if self.bot.merge_character_records(source,actual):
                self.relationship_character_var.set(actual); self.last_relationship_names=None
                self._refresh_relationship_list(); self._load_relationship_record()
                self._append_log(f"[IDENTITY] Merged {source} -> {actual}")

    def _delete_relationship_record(self):
        if not self.bot:
            return
        name = self.relationship_character_var.get().strip()
        if not name:
            return
        if not messagebox.askyesno(
            "Delete Relationship Character",
            f"Delete the relationship/memory record for '{name}'?\n\n"
            "This removes the character from Relationships, including its relationship notes and interaction history. "
            "Character Knowledge and Continuity records are not deleted.",
            parent=self.root,
        ):
            return
        if self.bot.delete_character_record(name):
            self.relationship_character_var.set("")
            self.last_relationship_names = None
            self._refresh_relationship_list()
            self._append_log(f"[MEMORY] Deleted relationship/memory entity: {name}")

    def _refresh_memory_overview(self):
        if not self.bot or not hasattr(self, "memory_overview_text"):
            return
        self._refresh_knowledge_manager()
        self._refresh_continuity()
        self._refresh_adaptive()
        voice = self.bot.learned_voice_text() or "No learned voice yet. Roleplay normally and Role Weaver will learn recurring speaking patterns from lines you actually send."
        threads = self.bot.memory_data.get("story_threads", [])
        thread_lines = []
        if isinstance(threads, list):
            for item in threads:
                if not isinstance(item, dict):
                    continue
                summary = str(item.get("summary") or "").strip()
                if not summary:
                    continue
                status = str(item.get("status") or "open").title()
                importance = item.get("importance", "")
                private = " [Private]" if item.get("private") else ""
                thread_lines.append(f"- [{status} {importance}/10]{private} {summary}")
        emotional = self.bot.emotional_state_text() or "No persistent emotional state recorded yet."
        knowledge_lines = []
        for item in self.bot.character_knowledge_items(include_dm_only=True):
            privacy = str(item.get("privacy") or "character").upper()
            confidence = str(item.get("confidence") or "known").title()
            knowledge_lines.append(f"- [{privacy} | {confidence}] {item.get('fact', '')}")
        text = (
            "OBSERVED CHARACTER VOICE\n" + voice
            + "\n\nCURRENT EMOTIONAL STATE\n" + emotional
            + "\n\nCHARACTER KNOWLEDGE\n"
            + ("\n".join(knowledge_lines) if knowledge_lines else "No structured character knowledge recorded yet.")
            + "\n\nSTORY THREADS / UNRESOLVED MATTERS\n"
            + ("\n".join(thread_lines) if thread_lines else "No structured story threads recorded yet.")
        )
        signature = text
        if signature == self.last_memory_overview_signature:
            return
        self.last_memory_overview_signature = signature
        self.memory_overview_text.configure(state="normal")
        self.memory_overview_text.delete("1.0", "end")
        self.memory_overview_text.insert("1.0", text)
        self.memory_overview_text.configure(state="disabled")

    def _refresh_adaptive(self):
        if not self.bot or not hasattr(self,"development_tree"):
            return
        prefs=self.bot.correction_preferences_text() or "No stable correction preferences learned yet. Edit an AI draft, send the edited line in NWN, and Role Weaver can learn recurring differences over time."
        examples=self.bot.memory_data.get("correction_examples",[])
        if isinstance(examples,list) and examples:
            prefs += f"\n\nRecorded edit examples: {len(examples)} (most recent {min(len(examples),40)} retained)."
        self.correction_text.configure(state="normal"); self.correction_text.delete("1.0","end"); self.correction_text.insert("1.0",prefs); self.correction_text.configure(state="disabled")
        for tree in (self.development_tree,self.approved_development_tree):
            for iid in tree.get_children(): tree.delete(iid)
        for item in self.bot.development_proposals():
            iid=str(item.get("id") or "")
            self.development_tree.insert("","end",iid=iid,values=(str(item.get("area") or "general").replace("_"," ").title(),item.get("confidence",5),item.get("statement","")))
        for item in self.bot.approved_development_items():
            iid=str(item.get("id") or "")
            self.approved_development_tree.insert("","end",iid=iid,values=(str(item.get("area") or "general").replace("_"," ").title(),item.get("statement","")))

    def _approve_development(self):
        if not self.bot: return
        sel=self.development_tree.selection()
        if not sel:
            messagebox.showinfo("Select Development","Select a pending development proposal first.",parent=self.root); return
        item=next((x for x in self.bot.development_proposals() if str(x.get("id"))==sel[0]),None)
        if not item: return
        evidence=str(item.get("evidence") or "").strip()
        msg=f"Approve this as part of the character's ongoing portrayal?\n\n{item.get('statement','')}"
        if evidence: msg += f"\n\nObserved evidence: {evidence}"
        if messagebox.askyesno("Approve Character Development",msg,parent=self.root):
            if self.bot.approve_development(sel[0]):
                self._refresh_adaptive(); self._append_log("[ADAPTIVE] Character development approved by player.")

    def _reject_development(self):
        if not self.bot: return
        sel=self.development_tree.selection()
        if not sel:
            messagebox.showinfo("Select Development","Select a pending development proposal first.",parent=self.root); return
        if messagebox.askyesno("Reject Character Development","Reject this proposal? Role Weaver will remember the rejection so it does not keep proposing the same development.",parent=self.root):
            if self.bot.reject_development(sel[0]):
                self._refresh_adaptive(); self._append_log("[ADAPTIVE] Character development proposal rejected.")

    def _remove_approved_development(self):
        if not self.bot: return
        sel=self.approved_development_tree.selection()
        if not sel:
            messagebox.showinfo("Select Development","Select an approved development entry first.",parent=self.root); return
        if messagebox.askyesno("Remove Approved Development","Remove this approved development from the character's active portrayal? This does not change the original profile file.",parent=self.root):
            if self.bot.delete_approved_development(sel[0]):
                self._refresh_adaptive(); self._append_log("[ADAPTIVE] Removed approved character development.")

    def _refresh_knowledge_manager(self):
        if not self.bot or not hasattr(self, "knowledge_tree"):
            return
        selected = self.knowledge_tree.selection()
        selected_id = selected[0] if selected else None
        for iid in self.knowledge_tree.get_children():
            self.knowledge_tree.delete(iid)
        if self.bot._ensure_knowledge_ids():
            self.bot.save_character_intelligence()
        for item in self.bot.character_knowledge_items(include_dm_only=True):
            kid = str(item.get("id") or "")
            if not kid:
                continue
            self.knowledge_tree.insert(
                "", "end", iid=kid,
                values=(
                    str(item.get("privacy") or "character").upper(),
                    str(item.get("confidence") or "known").title(),
                    str(item.get("fact") or ""),
                ),
            )
        if selected_id and self.knowledge_tree.exists(selected_id):
            self.knowledge_tree.selection_set(selected_id)

    def _knowledge_editor(self, title, item=None):
        item = item or {}
        win = tk.Toplevel(self.root)
        win.title(title)
        win.transient(self.root)
        win.grab_set()
        win.geometry("620x330")
        body = ttk.Frame(win, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Knowledge / fact:").pack(anchor="w")
        fact_text = tk.Text(
            body, height=7, wrap="word", bg="#1e1f22", fg="#dbdee1",
            insertbackground="#dbdee1", selectbackground="#5865f2",
            selectforeground="#ffffff", relief="flat", bd=0, padx=8, pady=6,
            font=("Segoe UI", 10),
        )
        fact_text.pack(fill="both", expand=True, pady=(4, 8))
        fact_text.insert("1.0", str(item.get("fact") or ""))
        row = ttk.Frame(body)
        row.pack(fill="x")
        ttk.Label(row, text="Privacy:").pack(side="left")
        privacy_var = tk.StringVar(value=str(item.get("privacy") or "character").upper())
        privacy = ttk.Combobox(
            row, textvariable=privacy_var, state="readonly", width=13,
            values=("PUBLIC", "SHARED", "CHARACTER", "PRIVATE", "DM_ONLY"),
        )
        privacy.pack(side="left", padx=(5, 14))
        ttk.Label(row, text="Confidence:").pack(side="left")
        confidence_var = tk.StringVar(value=str(item.get("confidence") or "known").title())
        confidence = ttk.Combobox(
            row, textvariable=confidence_var, state="readonly", width=12,
            values=("Known", "Believed", "Uncertain", "Rumor"),
        )
        confidence.pack(side="left", padx=(5, 14))
        ttk.Label(row, text="Source:").pack(side="left")
        source_var = tk.StringVar(value=str(item.get("source") or "manual"))
        ttk.Entry(row, textvariable=source_var, width=22).pack(side="left", padx=(5, 0), fill="x", expand=True)
        result = {}
        def save():
            fact = fact_text.get("1.0", "end").strip()
            if not fact:
                messagebox.showerror("Knowledge required", "Enter the fact or knowledge to store.", parent=win)
                return
            result.update({
                "fact": fact,
                "privacy": privacy_var.get().casefold(),
                "confidence": confidence_var.get().casefold(),
                "source": source_var.get().strip() or "manual",
            })
            win.destroy()
        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", command=save, style="Accent.TButton").pack(side="right", padx=(0, 6))
        fact_text.focus_set()
        win.wait_window()
        return result or None

    def _selected_knowledge_item(self):
        if not self.bot or not hasattr(self, "knowledge_tree"):
            return None
        selected = self.knowledge_tree.selection()
        if not selected:
            return None
        kid = selected[0]
        return next((x for x in self.bot.character_knowledge_items(include_dm_only=True) if str(x.get("id")) == kid), None)

    def _add_knowledge_item(self):
        if not self.bot:
            messagebox.showinfo("Start Role Weaver", "Start Role Weaver before editing persistent character knowledge.", parent=self.root)
            return
        values = self._knowledge_editor("Add Character Knowledge")
        if not values:
            return
        kid = self.bot.add_character_knowledge(**values)
        self.last_memory_overview_signature = None
        self._refresh_memory_overview()
        if kid and self.knowledge_tree.exists(kid):
            self.knowledge_tree.selection_set(kid)
        self._append_log("[MEMORY] Added manual character knowledge.")

    def _edit_knowledge_item(self):
        item = self._selected_knowledge_item()
        if not item:
            messagebox.showinfo("Select Knowledge", "Select a knowledge entry to edit.", parent=self.root)
            return
        values = self._knowledge_editor("Edit Character Knowledge", item)
        if not values:
            return
        if self.bot.update_character_knowledge(item.get("id"), **values):
            self.last_memory_overview_signature = None
            self._refresh_memory_overview()
            self._append_log("[MEMORY] Updated character knowledge.")

    def _delete_knowledge_item(self):
        item = self._selected_knowledge_item()
        if not item:
            messagebox.showinfo("Select Knowledge", "Select a knowledge entry to delete.", parent=self.root)
            return
        fact = str(item.get("fact") or "")
        preview = fact if len(fact) <= 160 else fact[:157] + "..."
        if not messagebox.askyesno("Delete Character Knowledge", f"Delete this knowledge entry?\n\n{preview}", parent=self.root):
            return
        if self.bot.delete_character_knowledge(item.get("id")):
            self.last_memory_overview_signature = None
            self._refresh_memory_overview()
            self._append_log("[MEMORY] Deleted character knowledge.")

    def _refresh_continuity(self):
        if not self.bot or not hasattr(self,"continuity_trees"): return
        self.bot._ensure_continuity_ids()
        for kind,tree in self.continuity_trees.items():
            selected=tree.selection(); sid=selected[0] if selected else None
            for iid in tree.get_children(): tree.delete(iid)
            items=self.bot.continuity_items(kind,include_private=True)
            if kind=="event": items=sorted(items,key=lambda x:str(x.get("timestamp","")),reverse=True)
            else: items=sorted(items,key=lambda x:(str(x.get("status","")) not in ("active","open","waiting"),-int(x.get("importance",5) or 5)))
            for item in items:
                iid=str(item.get("id") or "");
                if not iid: continue
                summary=("[Private] " if item.get("private") else "")+str(item.get("summary") or "")
                if kind=="thread": vals=(str(item.get("status","active")).title(),item.get("importance",5),summary)
                elif kind=="commitment": vals=(str(item.get("status","active")).title(),str(item.get("due") or ""),summary)
                else: vals=(str(item.get("timestamp") or "")[:16].replace("T"," "),item.get("importance",5),summary)
                tree.insert("","end",iid=iid,values=vals)
            if sid and tree.exists(sid): tree.selection_set(sid)

    def _continuity_editor(self, kind, item=None):
        item=item or {}; win=tk.Toplevel(self.root); win.title(("Edit " if item else "Add ")+kind.title()); win.transient(self.root); win.grab_set(); win.geometry("650x430")
        body=ttk.Frame(win,padding=12); body.pack(fill="both",expand=True)
        ttk.Label(body,text="Summary:").pack(anchor="w")
        text=tk.Text(body,height=6,wrap="word",bg="#1e1f22",fg="#dbdee1",insertbackground="#dbdee1",relief="flat",padx=8,pady=6); text.pack(fill="both",expand=True,pady=(4,8)); text.insert("1.0",str(item.get("summary") or ""))
        row=ttk.Frame(body); row.pack(fill="x",pady=3)
        statuses={"thread":("Active","Waiting","Resolved","Abandoned"),"commitment":("Active","Waiting","Fulfilled","Cancelled"),"event":("Recorded",)}
        ttk.Label(row,text="Status:").pack(side="left"); sv=tk.StringVar(value=str(item.get("status") or statuses[kind][0]).title()); ttk.Combobox(row,textvariable=sv,state="readonly",values=statuses[kind],width=12).pack(side="left",padx=(4,12))
        ttk.Label(row,text="Importance 1-10:").pack(side="left"); iv=tk.StringVar(value=str(item.get("importance",5))); ttk.Spinbox(row,from_=1,to=10,textvariable=iv,width=4).pack(side="left",padx=(4,12))
        pv=tk.BooleanVar(value=bool(item.get("private",False))); ttk.Checkbutton(row,text="Private",variable=pv).pack(side="left")
        ttk.Label(body,text="Participants (comma separated):").pack(anchor="w",pady=(7,0)); part=tk.StringVar(value=", ".join(item.get("participants") or [])); ttk.Entry(body,textvariable=part).pack(fill="x")
        due=tk.StringVar(value=str(item.get("due") or "")); direction=tk.StringVar(value=str(item.get("direction") or ""))
        if kind=="commitment":
            rr=ttk.Frame(body); rr.pack(fill="x",pady=(7,0)); ttk.Label(rr,text="Due:").pack(side="left"); ttk.Entry(rr,textvariable=due,width=24).pack(side="left",padx=(4,12)); ttk.Label(rr,text="Direction:").pack(side="left"); ttk.Combobox(rr,textvariable=direction,values=("owed_by_me","owed_to_me","mutual","other"),width=16).pack(side="left",padx=(4,0))
        ttk.Label(body,text="Notes:").pack(anchor="w",pady=(7,0)); notes=tk.StringVar(value=str(item.get("notes") or "")); ttk.Entry(body,textvariable=notes).pack(fill="x")
        result={}
        def save():
            summary=text.get("1.0","end").strip()
            if not summary: messagebox.showerror("Summary required","Enter a continuity summary.",parent=win); return
            result.update(summary=summary,status=sv.get().casefold(),importance=iv.get(),participants=[x.strip() for x in part.get().split(",") if x.strip()],private=pv.get(),due=due.get().strip(),direction=direction.get().strip(),notes=notes.get().strip()); win.destroy()
        buttons=ttk.Frame(body); buttons.pack(fill="x",pady=(10,0)); ttk.Button(buttons,text="Cancel",command=win.destroy).pack(side="right"); ttk.Button(buttons,text="Save",command=save,style="Accent.TButton").pack(side="right",padx=(0,6)); win.wait_window(); return result or None

    def _selected_continuity(self,kind):
        if not self.bot or not hasattr(self,"continuity_trees"): return None
        sel=self.continuity_trees[kind].selection()
        if not sel: return None
        return next((x for x in self.bot.continuity_items(kind,True) if str(x.get("id"))==sel[0]),None)

    def _add_continuity(self,kind):
        if not self.bot: messagebox.showinfo("Start Role Weaver","Start Role Weaver before editing continuity.",parent=self.root); return
        values=self._continuity_editor(kind)
        if values: self.bot.add_continuity_item(kind,**values); self._refresh_continuity(); self.last_memory_overview_signature=None; self._refresh_memory_overview(); self._append_log(f"[CONTINUITY] Added {kind}.")

    def _edit_continuity(self,kind):
        item=self._selected_continuity(kind)
        if not item: messagebox.showinfo("Select item",f"Select a {kind} to edit.",parent=self.root); return
        values=self._continuity_editor(kind,item)
        if values: self.bot.update_continuity_item(kind,item.get("id"),**values); self._refresh_continuity(); self.last_memory_overview_signature=None; self._refresh_memory_overview(); self._append_log(f"[CONTINUITY] Updated {kind}.")

    def _delete_continuity(self,kind):
        item=self._selected_continuity(kind)
        if not item: messagebox.showinfo("Select item",f"Select a {kind} to delete.",parent=self.root); return
        if messagebox.askyesno("Delete continuity",f"Delete this {kind}?\n\n{item.get('summary','')}",parent=self.root): self.bot.delete_continuity_item(kind,item.get("id")); self._refresh_continuity(); self.last_memory_overview_signature=None; self._refresh_memory_overview()

    def summarize_memory_now(self):
        if not self.bot:
            return
        if self.bot.summary_in_progress:
            self._append_log("[MEMORY] A memory summary is already running.")
            return
        if not self.bot.summary_event_buffer:
            self._append_log("[MEMORY] No new IC conversation is waiting to be summarized.")
            return
        self._append_log("[MEMORY] Summarizing current IC conversation now...")
        threading.Thread(target=self.bot.flush_memory_summary, daemon=True).start()

    def reset_learned_voice(self):
        if not self.bot:
            return
        if not messagebox.askyesno(
            "Reset learned voice",
            "Clear Role Weaver's observed speaking-style and vocabulary learning for this character?\n\nThe character profile, relationships, memories, and conversation history will not be changed.",
            parent=self.root,
        ):
            return
        self.bot.reset_learned_voice()
        self.last_memory_overview_signature = None
        self._refresh_memory_overview()
        self._append_log("[MEMORY] Learned character voice reset.")

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
        self.bot.prepare_correction_candidate(self.bot.last_draft or text, text)
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
            self._append_log("[F9] Generating. When the reply is ready, click NWN during the 2-second countdown.")
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
                        self.rescan_logs_btn.configure(state="normal")
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
                self._refresh_memory_overview()

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
