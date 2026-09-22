"""Portable, validated backups of Role Weaver user data (standard library only)."""

import hashlib
import json
import os
import shutil
import stat
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from . import atomic as storage

DIRECTORIES = {"Characters", "Lore", "Campaigns", "RoleplayRules", "RoleWeaver_Data"}
FILES = {"settings.json", "character_prompt.txt", "next_guidance.txt"}
MAX_BYTES = 1024 * 1024 * 1024
MAX_FILES = 20000


def _safe_name(name):
    parts = PurePosixPath(name).parts
    if (
        not parts
        or name != "/".join(parts)
        or "\\" in name
        or any(
            p in {".", ".."}
            or p.endswith((".", " "))
            or any(ord(c) < 32 or c in ':<>"|?*' for c in p)
            or p.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *[f"COM{i}" for i in range(10)],
                *[f"LPT{i}" for i in range(10)],
            }
            for p in parts
        )
        or not ((len(parts) == 1 and name in FILES) or (len(parts) > 1 and parts[0] in DIRECTORIES))
    ):
        raise ValueError(f"Unsupported backup path: {name}")
    return parts


def _target(root, name):
    path = root
    for part in _safe_name(name):
        path = path / part
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError(f"Linked paths are not supported: {name}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes the application directory")
    return path


@storage.synchronized
def create_backup(root, destination, validate_json=False):
    """Snapshot saved files. Caller must ensure the application is idle."""
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if any(destination.is_relative_to(root / d) for d in DIRECTORIES) or destination in [
        root / f for f in FILES
    ]:
        raise ValueError("Save backups outside the data being backed up")
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": "roleweaver-backup",
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }
    total = 0
    seen = set()
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        archive = Path(temp) / "backup.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for entry in sorted(FILES | DIRECTORIES):
                base = (
                    _target(root, entry + "/placeholder").parent
                    if entry in DIRECTORIES
                    else _target(root, entry)
                )
                if not base.exists():
                    continue
                if entry in DIRECTORIES and not base.is_dir():
                    raise ValueError(f"Expected a data directory: {entry}")
                candidates = sorted(base.rglob("*")) if base.is_dir() else [base]
                for path in candidates:
                    name = path.relative_to(root).as_posix()
                    if path.name.startswith(".rw-save-") and path.name.endswith(".tmp"):
                        continue
                    _target(root, name)
                    if path.is_dir() or not path.exists():
                        continue
                    if name.casefold() in seen:
                        raise ValueError(f"Backup paths differ only by case: {name}")
                    seen.add(name.casefold())
                    total += path.stat().st_size
                    if total > MAX_BYTES or len(manifest["files"]) >= MAX_FILES:
                        raise ValueError("Backup exceeds the 1 GiB or 20,000 file limit")
                    data = path.read_bytes()
                    if validate_json and path.suffix.lower() == ".json":
                        check_json(name, data)
                    manifest["files"][name] = hashlib.sha256(data).hexdigest()
                    z.writestr(name, data)
            z.writestr("manifest.json", json.dumps(manifest))
        with archive.open("r+b") as stream:
            os.fsync(stream.fileno())
        os.replace(archive, destination)
        storage.sync_directory(destination.parent)
    return destination


@storage.synchronized
def restore_backup(root, archive, validate_only=False, preserve_recovery_work=False):
    """Validate and stage everything, save a recovery ZIP, then overlay saved files.

    Files absent from the archive are preserved. Failed writes roll back all
    touched files; the recovery ZIP remains available even if rollback fails.
    """
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(dir=root) as temp:
        staging = Path(temp) / "staged"
        old = Path(temp) / "old"
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist()
            names = [i.filename for i in infos]
            if len(infos) > MAX_FILES + 1 or len(set(n.casefold() for n in names)) != len(names):
                raise ValueError("Too many files or duplicate archive paths")
            if (
                sum(i.file_size for i in infos) > MAX_BYTES
                or z.getinfo("manifest.json").file_size > 4 * 1024 * 1024
            ):
                raise ValueError("Backup exceeds size limits")
            manifest = json.loads(z.read("manifest.json"))
            if (
                not isinstance(manifest, dict)
                or manifest.get("format") != "roleweaver-backup"
                or manifest.get("version") != 1
            ):
                raise ValueError("Unsupported backup format")
            files = manifest.get("files")
            if not isinstance(files, dict) or set(names) != set(files) | {"manifest.json"}:
                raise ValueError("Backup file list does not match its manifest")
            for name, digest in files.items():
                dest = _target(root, name)
                if dest.exists() and not dest.is_file():
                    raise ValueError(f"Destination is not a file: {name}")
                if stat.S_ISLNK(z.getinfo(name).external_attr >> 16):
                    raise ValueError("Archive links are not supported")
                data = z.read(name)
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f"Checksum mismatch: {name}")
                if name.lower().endswith(".json"):
                    check_json(name, data)
                staged = staging / name
                staged.parent.mkdir(parents=True, exist_ok=True)
                with staged.open("wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
        if validate_only:
            return manifest
        recovery = create_backup(root, root / "Backups" / f"before-restore-{uuid.uuid4().hex}.zip")
        touched = []
        try:
            for name in files:
                dest = _target(root, name)
                if (
                    preserve_recovery_work
                    and (
                        name.startswith("RoleWeaver_Data/Recovery_Drafts/")
                        or name.endswith("/pending_summaries.json")
                    )
                    and dest.exists()
                ):
                    try:
                        check_json(name, dest.read_bytes())
                    except (ValueError, OSError):
                        pass
                    else:
                        continue
                previous = old / name
                if dest.exists():
                    previous.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest, previous)
                dest.parent.mkdir(parents=True, exist_ok=True)
                touched.append((dest, previous))
                os.replace(staging / name, dest)
                storage.sync_directory(dest.parent)
        except Exception as error:
            try:
                for dest, previous in reversed(touched):
                    if previous.exists():
                        os.replace(previous, dest)
                    else:
                        dest.unlink(missing_ok=True)
            except Exception as rollback_error:
                raise RuntimeError(
                    f"Restore and rollback failed. Recovery backup: {recovery}"
                ) from rollback_error
            raise RuntimeError(
                f"Restore failed; original files restored. Recovery backup: {recovery}"
            ) from error
        return recovery


def check_json(name, data):
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Invalid JSON in {name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {name}")


def validate_backup(root, archive):
    return restore_backup(root, archive, validate_only=True)


@storage.synchronized
def validate_saved_data(root):
    root = Path(root)
    paths = [root / "settings.json"]
    for directory in DIRECTORIES:
        paths.extend((root / directory).rglob("*.json"))
    for path in paths:
        if path.exists():
            _target(root, path.relative_to(root).as_posix())
            check_json(path.relative_to(root).as_posix(), path.read_bytes())
