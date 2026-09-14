"""Automatic snapshots and startup recovery for the desktop clients."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import uuid

import roleweaver_backup as backups
import roleweaver_storage as storage

INTERVAL_SECONDS = 300
KEEP_SNAPSHOTS = 10


class CrashProtection:
    def __init__(self, root, interval=INTERVAL_SECONDS, keep=KEEP_SNAPSHOTS):
        self.root = Path(root).resolve()
        self.directory = self.root / "Backups" / "Automatic"
        self.marker = self.root / ".roleweaver-session.json"
        self.interval, self.keep = interval, keep
        self.lock_file = None
        self.worker = None
        self.stop = threading.Event()
        self.unclean = False
        self.report = lambda message: None

    def acquire(self):
        """The OS releases the lock on a crash; the session marker survives."""
        self.lock_file = (self.root / ".roleweaver.lock").open("a+b")
        try:
            if self.lock_file.seek(0, os.SEEK_END) == 0:
                self.lock_file.write(b"0")
                self.lock_file.flush()
            self.lock_file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.lock_file.close()
            self.lock_file = None
            raise RuntimeError("Another Role Weaver client is using this installation. Close it before continuing.") from exc
        self.unclean = self.marker.exists()
        try:
            storage.atomic_write_text(self.marker, json.dumps({"pid": os.getpid(), "started": datetime.now(timezone.utc).isoformat()}))
        except Exception:
            self.release()
            raise

    def release(self):
        if self.lock_file is not None:
            self.lock_file.close()
            self.lock_file = None

    def snapshots(self):
        return sorted(self.directory.glob("auto-*.zip"), reverse=True)

    def latest_valid(self):
        for path in self.snapshots():
            try:
                backups.validate_backup(self.root, path)
                return path
            except Exception:
                continue
        return None

    def snapshot(self):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.directory / f"auto-{stamp}-{uuid.uuid4().hex[:8]}.zip"
        backups.create_backup(self.root, path, validate_json=True)
        try:
            backups.validate_backup(self.root, path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        # Never prune previous copies until a new, verified copy is available.
        for old in self.snapshots()[self.keep:]:
            old.unlink()
        return path

    def start(self, report):
        self.report = report
        # Initial backup is completed before the client can start a session.
        self._try_snapshot()
        self.worker = threading.Thread(target=self._run, name="RoleWeaver automatic backup", daemon=True)
        self.worker.start()

    def _try_snapshot(self):
        try:
            self.last_backup = self.snapshot()
            return True
        except Exception as exc:
            self.report(f"[BACKUP ERROR] Automatic backup failed: {exc}. Previous backups were retained.")
            return False

    def _run(self):
        while not self.stop.wait(self.interval):
            self._try_snapshot()

    def close(self, clean=False):
        self.stop.set()
        if self.worker:
            self.worker.join()
        try:
            # Wait for an active atomic save and prohibit late daemon writes.
            storage.freeze()
            if clean and self._try_snapshot():
                self.marker.unlink(missing_ok=True)
                storage.sync_directory(self.root)
        finally:
            self.release()


def prepare_gui(root, app_directory):
    """Run before settings/profile loading can overwrite damaged data."""
    from tkinter import messagebox
    guard = CrashProtection(app_directory)
    try:
        guard.acquire()
        problem = None
        try:
            backups.validate_saved_data(guard.root)
        except Exception as exc:
            problem = str(exc)
        if guard.unclean or problem:
            candidate = guard.latest_valid()
            reason = "Role Weaver did not close cleanly last time."
            if problem:
                reason += f"\nSaved data could not be read: {problem}"
            if candidate:
                choice = messagebox.askyesnocancel(
                    "Crash recovery", reason + f"\n\nRestore the latest verified automatic backup?\n{candidate.name}\n\nYes: restore matching files and keep a recovery copy of current files.\nNo: keep current data. Cancel: exit. Changes since the backup are not recovered.", parent=root)
                if choice is None:
                    guard.release()
                    return None
                if choice:
                    recovery = backups.restore_backup(guard.root, candidate, preserve_recovery_work=True)
                    backups.validate_saved_data(guard.root)
                    messagebox.showinfo("Recovery complete", f"Saved data was restored. Previous files are preserved in:\n{recovery}", parent=root)
                elif problem:
                    raise RuntimeError("Startup stopped to preserve damaged data. Restore a valid backup or repair the reported file before relaunching.")
            elif problem:
                raise RuntimeError(reason + "\n\nNo valid automatic backup is available. Existing data has been preserved. Restore a manual backup or repair the reported file before relaunching.")
            else:
                if not messagebox.askokcancel("Crash recovery", reason + "\n\nNo verified automatic backup is available. Continue with the saved files?", parent=root):
                    guard.release()
                    return None
        return guard
    except Exception as exc:
        guard.release()
        messagebox.showerror("Role Weaver could not start", str(exc), parent=root)
        return None
