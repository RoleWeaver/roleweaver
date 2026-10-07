"""Local edit recovery. Never sends text to NWN or an AI provider."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid
import roleweaver_storage as storage


class DraftStore:
    def __init__(self, root):
        self.directory = Path(root) / "RoleWeaver_Data" / "Recovery_Drafts"

    def save(self, key, text, context):
        path = self.directory / (hashlib.sha256(key.encode()).hexdigest() + ".json")
        storage.atomic_write_text(path, json.dumps({"version": 1, "text": text,
            "context": context, "updated": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
        return path

    def records(self):
        result = []
        for path in self.directory.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") != 1 or not isinstance(data.get("text"), str):
                raise ValueError(f"Invalid recovered draft: {path.name}")
            result.append((path, data))
        return sorted(result, key=lambda item: item[1]["updated"], reverse=True)

    @storage.synchronized
    def discard(self, path):
        path = Path(path)
        if path.parent.resolve() != self.directory.resolve():
            raise ValueError("Draft is outside recovery storage")
        path.unlink(missing_ok=True)


class DraftRecovery:
    """Capture user changes only in explicitly registered text editors.

    A bounded timer writes the latest captured value even during continuous
    typing. Changes are retained until explicit dismissal, including saved edits.
    """
    def __init__(self, app, root):
        self.app, self.root = app, app.root
        self.store = DraftStore(root)
        self.session = uuid.uuid4().hex
        self.baselines, self.pending = {}, {}
        self.timer = None
        self.viewer = None
        self.tracked = {}

    def track(self, widget, label, source=None):
        """Bind only the designated editor, never global/internal Tk events."""
        self.tracked[widget] = (label, source)
        for event in ("<FocusIn>", "<KeyRelease>", "<<Paste>>", "<<Cut>>", "<FocusOut>"):
            widget.bind(event, lambda e, kind=event, target=widget: self.capture(target, kind), add="+")
        widget.bind("<Destroy>", lambda e, target=widget: self.tracked.pop(target, None), add="+")

    def eligible(self, widget):
        if isinstance(widget, str) or widget not in getattr(self, "tracked", {}):
            return False
        if widget is getattr(self.app, "api_entry", None):
            return False
        return widget.winfo_class() == "Text" and str(widget.cget("state")) != "disabled"

    def capture(self, widget, event):
        try:
            if not self.eligible(widget):
                return
            value = widget.get("1.0", "end-1c") if widget.winfo_class() == "Text" else widget.get()
            context = dict(self.app.settings)
            # Store only identity metadata, never provider settings or keys.
            context = {k: str(context.get(k, "")) for k in ("server_profile", "character_name", "campaign_id")}
            context["window"] = widget.winfo_toplevel().title()
            context["field"] = str(widget)
            for attr in ("character_profile_var", "relationship_character_var"):
                var = getattr(self.app, attr, None)
                if var is not None:
                    context[attr] = str(var.get())
            label, source = self.tracked[widget]
            context["label"] = label
            if source is not None:
                context["source_file"] = str(source())
            key = self.session + json.dumps(context, sort_keys=True)
            if event == "<FocusIn>":
                self.baselines[key] = value
                return
            if value != self.baselines.get(key, ""):
                self.baselines[key] = value
                self.pending[key] = (value, context)
                if self.timer is None:
                    self.timer = self.root.after(750, self.flush)
            if event == "<FocusOut>":
                self.flush()
        except Exception as exc:
            self.app._append_log(f"[DRAFT RECOVERY ERROR] {exc}")

    def flush(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        for key, (value, context) in list(self.pending.items()):
            try:
                self.store.save(key, value, context)
                del self.pending[key]
            except Exception as exc:
                self.app._append_log(f"[DRAFT RECOVERY ERROR] Could not save edits: {exc}")
        if self.pending and self.root.winfo_exists():
            self.timer = self.root.after(1000, self.flush)
        return not self.pending

    def show(self):
        import tkinter as tk
        from tkinter import ttk, messagebox
        self.flush()
        if self.viewer is not None and self.viewer.winfo_exists():
            self.viewer.lift()
            return
        try:
            records = self.store.records()
        except Exception as exc:
            messagebox.showerror("Recovery failed", str(exc), parent=self.root)
            return
        win = self.viewer = tk.Toplevel(self.root)
        win.title("Recovered edits")
        width = min(850, max(360, win.winfo_screenwidth() - 80))
        height = min(550, max(300, win.winfo_screenheight() - 120))
        win.geometry(f"{width}x{height}+20+20")
        win.minsize(min(480, width), min(340, height))
        win.columnconfigure(0, weight=1)
        win.rowconfigure(2, weight=1)
        ttk.Label(win, text="Select an edit to review and copy back into its editor. Nothing is sent to the game. Saved edits remain here until discarded.", wraplength=width - 40).grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        listing = tk.Listbox(win, height=5, exportselection=False)
        listing.grid(row=1, column=0, sticky="ew", padx=10)
        detail = tk.Text(win, height=6, width=30, wrap="word", state="disabled", exportselection=False)
        detail.grid(row=2, column=0, sticky="nsew", padx=(10, 0), pady=8)
        scroll = ttk.Scrollbar(win, orient="vertical", command=detail.yview)
        scroll.grid(row=2, column=1, sticky="ns", padx=(0, 10), pady=8)
        detail.configure(yscrollcommand=scroll.set)
        def refresh():
            listing.delete(0, "end")
            for _, data in records:
                c = data["context"]
                listing.insert("end", f"{data['updated'][:19]} | {c.get('server_profile', '')} / {c.get('character_name', '')} | {c.get('window', '')} | {c.get('label', c.get('field', ''))}")
        def selected(event=None):
            detail.configure(state="normal")
            detail.delete("1.0", "end")
            if listing.curselection():
                data = records[listing.curselection()[0]][1]
                detail.insert("1.0", data["text"])
            detail.configure(state="disabled")
        def copy_text(event=None):
            if detail.tag_ranges("sel"):
                value = detail.get("sel.first", "sel.last")
            else:
                value = detail.get("1.0", "end-1c")
            if value:
                self.copy_text(value)
            return "break"
        detail.bind("<Control-c>", copy_text)
        detail.bind("<Control-C>", copy_text)
        def clear_all():
            if messagebox.askyesno("Clear recovered edits", "Remove all previously recovered edits? Saved character and lore files will not be changed.", parent=win):
                try:
                    self.clear_all()
                except Exception as exc:
                    messagebox.showerror("Could not clear edits", str(exc), parent=win)
                    return
                records.clear()
                refresh()
                detail.configure(state="normal")
                detail.delete("1.0", "end")
                detail.configure(state="disabled")
        def discard():
            if listing.curselection() and messagebox.askyesno("Discard recovered edit", "Permanently discard this recovered edit?", parent=win):
                index = listing.curselection()[0]
                self.store.discard(records[index][0])
                records.pop(index)
                refresh()
                detail.configure(state="normal")
                detail.delete("1.0", "end")
                detail.configure(state="disabled")
        listing.bind("<<ListboxSelect>>", selected)
        row = ttk.Frame(win)
        row.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
        ttk.Button(row, text="Copy text", command=copy_text).pack(side="left")
        ttk.Button(row, text="Discard selected edit", command=discard).pack(side="right")
        ttk.Button(row, text="Clear all", command=clear_all).pack(side="right", padx=8)
        refresh()

    def copy_text(self, value):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update_idletasks()

    def clear_all(self):
        self.pending.clear()
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        with storage.LOCK:
            for path in self.store.directory.glob("*.json"):
                self.store.discard(path)
