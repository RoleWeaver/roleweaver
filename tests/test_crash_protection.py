import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import zipfile

import roleweaver_backup as backups
import roleweaver_crash as crash
import roleweaver_storage as storage


class CrashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = self.root / "settings.json"
        self.settings.write_text('{"character_name":"Hero"}', encoding="utf-8")
        self.frozen = patch.object(storage, "_frozen", False)
        self.frozen.start()
        self.addCleanup(self.frozen.stop)

    def guard(self, **kwargs):
        guard = crash.CrashProtection(self.root, **kwargs)
        self.addCleanup(guard.release)
        return guard

    def child(self, source):
        return subprocess.run([sys.executable, "-c", source, str(self.root)], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=15)

    def test_interrupted_replace_keeps_old_data(self):
        result = self.child("import os,sys; from pathlib import Path; import roleweaver_storage as s; s.os.replace=lambda *a: os._exit(23); s.atomic_write_text(Path(sys.argv[1])/'settings.json', '{}')")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(json.loads(self.settings.read_text())["character_name"], "Hero")
        archive = backups.create_backup(self.root, self.root / "copy.zip")
        with zipfile.ZipFile(archive) as z:
            self.assertFalse(any(".rw-save-" in name for name in z.namelist()))

    def test_fsync_failure_preserves_original(self):
        with patch.object(storage.os, "fsync", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                storage.atomic_write_text(self.settings, "{}")
        self.assertIn("Hero", self.settings.read_text())
        self.assertFalse(list(self.root.glob(".rw-save-*.tmp")))

    def test_append_failure_preserves_complete_history(self):
        history = self.root / "history.txt"
        history.write_text("first\n")
        with patch.object(storage.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                storage.append_text(history, "second\n")
        self.assertEqual(history.read_text(), "first\n")

    def test_shutdown_blocks_late_saves(self):
        storage.freeze()
        with self.assertRaises(RuntimeError):
            storage.atomic_write_text(self.settings, "{}")
        self.assertIn("Hero", self.settings.read_text())

    def test_crash_leaves_marker_and_os_releases_lock(self):
        result = self.child("import os,sys; from roleweaver_crash import CrashProtection; g=CrashProtection(sys.argv[1]); g.acquire(); os._exit(23)")
        self.assertEqual(result.returncode, 23, result.stderr)
        guard = self.guard()
        guard.acquire()
        self.assertTrue(guard.unclean)

    def test_second_process_cannot_write_same_installation(self):
        guard = self.guard()
        guard.acquire()
        result = self.child("import sys; from roleweaver_crash import CrashProtection; g=CrashProtection(sys.argv[1]); g.acquire()")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Another Role Weaver client", result.stderr)

    def test_clean_close_saves_and_clears_marker(self):
        guard = self.guard()
        guard.acquire()
        guard.close(clean=True)
        self.assertFalse(guard.marker.exists())
        self.assertEqual(len(guard.snapshots()), 1)

    def test_failed_close_retains_crash_marker(self):
        guard = self.guard()
        guard.acquire()
        with patch.object(guard, "snapshot", side_effect=OSError("disk full")):
            guard.close(clean=True)
        self.assertTrue(guard.marker.exists())

    def test_rotating_snapshots_leave_manual_backups(self):
        guard = self.guard(keep=2)
        manual = self.root / "Backups" / "manual.zip"
        backups.create_backup(self.root, manual)
        for number in range(4):
            storage.atomic_write_text(self.settings, json.dumps({"number": number}))
            guard.snapshot()
        self.assertEqual(len(guard.snapshots()), 2)
        self.assertTrue(manual.exists())
        with zipfile.ZipFile(guard.latest_valid()) as z:
            self.assertEqual(json.loads(z.read("settings.json"))["number"], 3)

    def test_bad_snapshot_does_not_prune_good_backups(self):
        guard = self.guard(keep=1)
        good = guard.snapshot()
        self.settings.write_text("{truncated")
        with self.assertRaises(ValueError):
            guard.snapshot()
        self.assertEqual(guard.snapshots(), [good])

    def test_falls_back_from_corrupt_latest_archive(self):
        guard = self.guard()
        good = guard.snapshot()
        bad = guard.directory / "auto-zzzz.zip"
        bad.write_bytes(b"corrupt")
        self.assertEqual(guard.latest_valid(), good)

    def test_periodic_worker_is_silent_on_success(self):
        guard = self.guard(interval=0.02)
        done = threading.Event()
        calls = []
        snapshot = guard.snapshot
        def record_snapshot():
            result = snapshot()
            calls.append(result)
            if len(calls) >= 2:
                done.set()
            return result
        report = Mock()
        try:
            with patch.object(guard, "snapshot", side_effect=record_snapshot):
                guard.start(report)
                self.assertTrue(done.wait(5))
                guard.stop.set()
                guard.worker.join(timeout=5)
        finally:
            guard.stop.set()
            guard.worker.join(timeout=5)
        self.assertGreaterEqual(len(guard.snapshots()), 2)
        report.assert_not_called()

    def test_snapshot_waits_for_grouped_save(self):
        guard = self.guard()
        finished = threading.Event()
        with storage.LOCK:
            worker = threading.Thread(target=lambda: (guard.snapshot(), finished.set()))
            worker.start()
            self.assertFalse(finished.wait(0.05))
            storage.atomic_write_text(self.settings, '{"saved":true}')
        worker.join(timeout=5)
        self.assertTrue(finished.is_set())
        with zipfile.ZipFile(guard.latest_valid()) as z:
            self.assertTrue(json.loads(z.read("settings.json"))["saved"])

    def test_recovery_precedes_settings_load(self):
        source = (Path(__file__).resolve().parents[1] / "nwn_ai_gui.py").read_text(encoding="utf-8")
        main = source[source.index("def main():"):]
        self.assertLess(main.index("prepare_gui("), main.index("NWNAIApp(root)"))

    def test_no_direct_saved_file_writes_remain(self):
        for filename in ["nwn_ai_bot.py", "nwn_ai_gui.py"]:
            tree = ast.parse((Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, {"write_text", "write_bytes"}, filename)

    def test_startup_recovers_before_loading_corrupt_settings(self):
        guard = self.guard()
        good = guard.snapshot()
        self.settings.write_text("{damaged")
        # Mock only dialogs; run the actual validation, restore and disk writes.
        with patch("tkinter.messagebox.askyesnocancel", return_value=True), patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showerror") as error:
            started = crash.prepare_gui(None, self.root)
        self.assertIsNotNone(started)
        self.addCleanup(started.release)
        error.assert_not_called()
        self.assertIn("Hero", self.settings.read_text())
        self.assertTrue(good.exists())
        recovery = list((self.root / "Backups").glob("before-restore-*.zip"))
        with zipfile.ZipFile(recovery[0]) as z:
            self.assertEqual(z.read("settings.json"), b"{damaged")

    def test_invalid_data_without_backup_is_not_overwritten(self):
        self.settings.write_text("{damaged")
        with patch("tkinter.messagebox.showerror") as error:
            self.assertIsNone(crash.prepare_gui(None, self.root))
        self.assertEqual(self.settings.read_text(), "{damaged")
        error.assert_called_once()

    def test_cancel_recovery_keeps_original_files(self):
        guard = self.guard()
        guard.snapshot()
        guard.marker.write_text("previous crash")
        with patch("tkinter.messagebox.askyesnocancel", return_value=None):
            self.assertIsNone(crash.prepare_gui(None, self.root))
        self.assertIn("Hero", self.settings.read_text())
        guard.acquire()  # Cancel released the lock.


if __name__ == "__main__":
    unittest.main()
