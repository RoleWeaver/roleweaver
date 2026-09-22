"""Shared Tk update controls for the Windows and Linux clients."""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .update_install import prepare_fresh_install
from .updates import RELEASES_URL, Release, can_download, check_latest, is_newer, stage_release


class UpdatePanel:
    def __init__(
        self,
        parent,
        root,
        *,
        platform: str,
        prepare_install,
        installed: bool = False,
        on_available=None,
        data_root: Path,
        prepare_data=None,
    ):
        self.root = root
        self.platform = platform
        self.prepare_install = prepare_install
        self.installed = installed
        self.on_available = on_available
        self.data_root = Path(data_root)
        self.prepare_data = prepare_data
        self.portable = platform == "win32" and not installed
        self.events = queue.Queue()
        self.release: Release | None = None
        self.staged_archive: Path | None = None
        self.busy = False

        ttk.Label(parent, text=f"Installed version: {__version__}").pack(anchor="w", pady=(5, 10))
        self.status = ttk.Label(parent, text="No update check has run yet.", wraplength=650)
        self.status.pack(anchor="w", fill="x", pady=(0, 10))
        controls = ttk.Frame(parent)
        controls.pack(fill="x")
        self.check_button = ttk.Button(controls, text="Check for Updates", command=self.check)
        self.check_button.pack(side="left")
        self.download_button = ttk.Button(
            controls, text="Download Update", command=self.download, state="disabled"
        )
        self.download_button.pack(side="left", padx=8)
        self.prepare_button = ttk.Button(
            controls, text="Prepare New Folder", command=self.prepare, state="disabled"
        )
        if not installed:
            self.prepare_button.pack(side="left")
        ttk.Button(
            controls, text="View Releases", command=lambda: webbrowser.open(RELEASES_URL)
        ).pack(side="left")
        ttk.Label(
            parent,
            text=(
                "Downloads are verified against SHA-256 checksums published with each release. "
                "Windows installed builds can launch the updater after closing Role Weaver. "
                "Portable and Linux builds can prepare a fresh folder with a copy of saved data."
            ),
            wraplength=650,
        ).pack(anchor="w", fill="x", pady=(14, 8))
        self.notes = ttk.Label(parent, text="", wraplength=650, justify="left")
        self.notes.pack(anchor="w", fill="x")
        self.root.after(100, self._poll)
        self.root.after(2500, self.check)

    def _work(self, kind, action):
        self.busy = True
        self.check_button.configure(state="disabled")
        self.download_button.configure(state="disabled")
        self.prepare_button.configure(state="disabled")

        def run():
            try:
                self.events.put((kind, action(), None))
            except Exception as exc:
                self.events.put((kind, None, exc))

        threading.Thread(target=run, daemon=True).start()

    def check(self):
        if self.busy:
            return
        self.status.configure(text="Checking the latest stable release…")
        self._work("check", check_latest)

    def download(self):
        if self.busy or self.release is None:
            return
        if not messagebox.askyesno(
            "Download Role Weaver update",
            f"Download Role Weaver {self.release.version} and verify its SHA-256 checksum?",
            parent=self.root,
        ):
            return
        self.status.configure(text="Downloading and verifying the update…")
        release = self.release
        destination = Path.home() / "Downloads" / "RoleWeaver Updates"
        self._work(
            "download",
            lambda: stage_release(release, self.platform, destination, portable=self.portable),
        )

    def prepare(self):
        if self.busy or self.staged_archive is None or self.release is None:
            return
        if self.prepare_data is None or not self.prepare_data():
            return
        parent = filedialog.askdirectory(
            parent=self.root,
            title="Choose parent folder for the new Role Weaver copy",
            initialdir=str(self.data_root.parent),
        )
        if not parent:
            return
        archive = self.staged_archive
        version = self.release.version
        self.status.configure(text="Preparing a new folder and copying saved data…")
        self._work(
            "prepare",
            lambda: prepare_fresh_install(
                archive, self.data_root, Path(parent), version, self.platform
            ),
        )

    def _poll(self):
        while True:
            try:
                kind, result, error = self.events.get_nowait()
            except queue.Empty:
                break
            self.busy = False
            self.check_button.configure(state="normal")
            if error:
                self.status.configure(text=f"Update {kind} failed: {error}")
                continue
            if kind == "check":
                self.release = result
                self.staged_archive = None
                if is_newer(result.version):
                    if can_download(result, self.platform, portable=self.portable):
                        self.status.configure(text=f"Role Weaver {result.version} is available.")
                        self.download_button.configure(state="normal")
                        if self.on_available:
                            self.on_available(result.version)
                    else:
                        self.status.configure(
                            text=f"Version {result.version} is published, but no verified "
                            f"{self.platform} download is available."
                        )
                else:
                    self.status.configure(
                        text=f"You are up to date (latest stable: {result.version})."
                    )
                self.notes.configure(text=(result.notes[:1800] or "No release notes provided."))
            elif kind == "download":
                self.staged_archive = result
                self.status.configure(text=f"Verified update saved to {result}")
                if self.platform == "win32" and self.installed and getattr(sys, "frozen", False):
                    if (
                        messagebox.askyesno(
                            "Install Role Weaver update",
                            "Close Role Weaver and launch the verified Windows installer now? "
                            "Stop any active game session first. "
                            "Your profiles and settings will be kept.",
                            parent=self.root,
                        )
                        and self.prepare_install()
                    ):
                        subprocess.Popen([str(result), "/CLOSEAPPLICATIONS"])
                        return
                else:
                    messagebox.showinfo(
                        "Update ready",
                        f"The verified update is saved at:\n{result}\n\n"
                        "Press Prepare New Folder to create a new copy with your saved data. "
                        "The current installation will not be overwritten.",
                        parent=self.root,
                    )
            elif kind == "prepare":
                self.status.configure(text=f"New Role Weaver copy is ready at {result}")
                if self.platform == "linux":
                    instructions = (
                        "Close Role Weaver, then run bash install-linux.sh and "
                        "bash start-role-weaver.sh from the new folder."
                    )
                else:
                    instructions = "Close Role Weaver, then run RoleWeaver.exe from the new folder."
                messagebox.showinfo(
                    "Update prepared",
                    f"New copy: {result}\n\n{instructions}\n\n"
                    "Your previous installation remains unchanged for rollback.",
                    parent=self.root,
                )
            if (
                self.release
                and is_newer(self.release.version)
                and can_download(self.release, self.platform, portable=self.portable)
                and not self.busy
            ):
                self.download_button.configure(state="normal")
            if self.staged_archive and not self.installed and not self.busy:
                self.prepare_button.configure(state="normal")
        try:
            self.root.after(100, self._poll)
        except Exception:
            pass
