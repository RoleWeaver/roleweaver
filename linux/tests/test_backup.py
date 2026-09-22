import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import roleweaver_backup as backup


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "app"
        self.root.mkdir()
        (self.root / "settings.json").write_text('{"character_name":"Original"}')
        (self.root / "next_response_seed.txt").write_text("A saved opening line")
        (self.root / "Characters").mkdir()
        (self.root / "Characters" / "hero.txt").write_text("Original hero")
        self.archive = Path(self.temp.name) / "backup.zip"

    def test_round_trip_and_recovery(self):
        backup.create_backup(self.root, self.archive)
        (self.root / "Characters" / "hero.txt").write_text("Changed")
        (self.root / "next_response_seed.txt").write_text("Changed seed")
        (self.root / "Characters" / "new.txt").write_text("Keep me")
        recovery = backup.restore_backup(self.root, self.archive)
        self.assertEqual((self.root / "Characters" / "hero.txt").read_text(), "Original hero")
        self.assertEqual((self.root / "Characters" / "new.txt").read_text(), "Keep me")
        self.assertEqual(
            (self.root / "next_response_seed.txt").read_text(),
            "A saved opening line",
        )
        with zipfile.ZipFile(recovery) as z:
            self.assertEqual(z.read("Characters/hero.txt"), b"Changed")
        backup.restore_backup(self.root, recovery)
        self.assertEqual((self.root / "Characters" / "hero.txt").read_text(), "Changed")

    def make_archive(self, name, data=b"bad", digest=None):
        with zipfile.ZipFile(self.archive, "w") as z:
            z.writestr(name, data)
            z.writestr("manifest.json", json.dumps({"format": "roleweaver-backup", "version": 1, "files": {name: digest or hashlib.sha256(data).hexdigest()}}))

    def test_unsafe_paths_rejected_before_writes(self):
        for name in ["../outside", "Characters/../../outside", "Characters/C:evil", "/Characters/hero", "Characters/CON.txt", "nwn_ai_gui.py", "Characters/x\\evil"]:
            with self.subTest(name=name):
                self.make_archive(name)
                with self.assertRaises(ValueError):
                    backup.restore_backup(self.root, self.archive)
                self.assertFalse((self.root / "Backups").exists())

    def test_corruption_rejected(self):
        self.make_archive("Characters/hero.txt", digest="wrong")
        with self.assertRaises(ValueError):
            backup.restore_backup(self.root, self.archive)
        self.assertEqual((self.root / "Characters" / "hero.txt").read_text(), "Original hero")

    def test_invalid_settings_rejected(self):
        self.make_archive("settings.json", b"[]")
        with self.assertRaises(ValueError):
            backup.restore_backup(self.root, self.archive)

    def test_rollback_on_write_failure(self):
        backup.create_backup(self.root, self.archive)
        (self.root / "Characters" / "hero.txt").write_text("Changed")
        (self.root / "settings.json").write_text("{}")
        replace = backup.os.replace
        def fail_settings(src, dest):
            if Path(src).parent.name == "staged" and Path(dest).name == "settings.json":
                raise OSError("simulated disk failure")
            return replace(src, dest)
        with patch.object(backup.os, "replace", side_effect=fail_settings):
            with self.assertRaisesRegex(RuntimeError, "original files restored"):
                backup.restore_backup(self.root, self.archive)
        self.assertEqual((self.root / "Characters" / "hero.txt").read_text(), "Changed")
        self.assertEqual((self.root / "settings.json").read_text(), "{}")

    def test_backup_cannot_include_itself(self):
        with self.assertRaises(ValueError):
            backup.create_backup(self.root, self.root / "Characters" / "backup.zip")

    def test_case_collisions_rejected(self):
        self.make_archive("Characters/hero.txt")
        with zipfile.ZipFile(self.archive, "a") as z:
            z.writestr("Characters/HERO.txt", b"other")
        with self.assertRaises(ValueError):
            backup.restore_backup(self.root, self.archive)
        self.assertFalse((self.root / "Backups").exists())

    def test_gui_callbacks_exist(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / "nwn_ai_gui.py").read_text(encoding="utf-8"))
        app = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "NWNAIApp")
        methods = {n.name for n in app.body if isinstance(n, ast.FunctionDef)}
        for node in ast.walk(app):
            if isinstance(node, ast.keyword) and node.arg == "command" and isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) and node.value.value.id == "self":
                self.assertIn(node.value.attr, methods)


class BackupGuiTests(unittest.TestCase):
    def setUp(self):
        # Exercise the actual callbacks without desktop/provider dependencies.
        tree = ast.parse((Path(__file__).resolve().parents[1] / "nwn_ai_gui.py").read_text(encoding="utf-8"))
        app = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "NWNAIApp")
        methods = [n for n in app.body if isinstance(n, ast.FunctionDef) and n.name in {"_backup_ready", "_create_backup", "_restore_backup"}]
        self.env = {"messagebox": unittest.mock.Mock(), "filedialog": unittest.mock.Mock(), "backups": unittest.mock.Mock(), "core": unittest.mock.Mock(), "time": __import__("time")}
        exec(compile(ast.Module(body=methods, type_ignores=[]), "callbacks", "exec"), self.env)
        self.app = unittest.mock.Mock(running=False, bot=None)
        self.app._backup_ready.side_effect = lambda: self.env["_backup_ready"](self.app)

    def test_guard_blocks_stopped_session(self):
        self.app.bot = object()
        self.assertFalse(self.env["_backup_ready"](self.app))

    def test_cancel_does_not_restore(self):
        self.env["filedialog"].askopenfilename.return_value = ""
        self.env["_restore_backup"](self.app)
        self.env["backups"].restore_backup.assert_not_called()
        self.app.root.destroy.assert_not_called()

    def test_success_closes_client(self):
        self.env["messagebox"].askyesno.return_value = True
        self.env["_restore_backup"](self.app)
        self.env["backups"].restore_backup.assert_called_once()
        self.app.root.destroy.assert_called_once()

    def test_failure_keeps_client_open(self):
        self.env["messagebox"].askyesno.return_value = True
        self.env["backups"].restore_backup.side_effect = ValueError("Invalid archive")
        self.env["_restore_backup"](self.app)
        self.env["messagebox"].showerror.assert_called_once()
        self.app.root.destroy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
