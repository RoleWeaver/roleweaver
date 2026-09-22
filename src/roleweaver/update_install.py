"""Prepare a separate, rollback-friendly portable/Linux installation."""

from __future__ import annotations

import os
import re
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from .storage.backups import create_backup, restore_backup
from .updates import UpdateError

MAX_FILES = 20_000
MAX_UNPACKED_BYTES = 2 * 1024 * 1024 * 1024
WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}


def _parts(name: str) -> tuple[str, ...]:
    clean = name.rstrip("/")
    parts = PurePosixPath(clean).parts
    if (
        not parts
        or clean != "/".join(parts)
        or clean.startswith("/")
        or "\\" in clean
        or any(
            part in {".", ".."}
            or part.endswith((".", " "))
            or part.split(".")[0].upper() in WINDOWS_DEVICES
            or any(ord(char) < 32 or char in ':<>"|?*' for char in part)
            for part in parts
        )
    ):
        raise UpdateError(f"Unsafe path in update archive: {name!r}")
    return parts


def _copy_member(stream, target: Path, size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        raise UpdateError(f"Duplicate path in update archive: {target.name}")
    remaining = size
    with target.open("xb") as output:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise UpdateError("The update archive ended before a file was complete.")
            output.write(chunk)
            remaining -= len(chunk)


def _extract_zip(archive: Path, destination: Path) -> None:
    seen = set()
    total = 0
    with zipfile.ZipFile(archive) as source:
        infos = source.infolist()
        if len(infos) > MAX_FILES:
            raise UpdateError("The update archive contains too many files.")
        for info in infos:
            parts = _parts(info.filename)
            key = "/".join(parts).casefold()
            if key in seen:
                raise UpdateError("The update archive contains duplicate paths.")
            seen.add(key)
            mode = info.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if file_type not in {0, stat.S_IFDIR, stat.S_IFREG} or (
                file_type == stat.S_IFDIR and not info.is_dir()
            ):
                raise UpdateError("Update archive links and special files are not supported.")
            total += info.file_size
            if total > MAX_UNPACKED_BYTES:
                raise UpdateError("The expanded update exceeds the size limit.")
            target = destination.joinpath(*parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                with source.open(info) as input_file:
                    _copy_member(input_file, target, info.file_size)


def _extract_tar(archive: Path, destination: Path, version: str) -> None:
    expected_root = f"RoleWeaver-v{version}-Linux"
    seen = set()
    total = 0
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if len(members) > MAX_FILES:
            raise UpdateError("The update archive contains too many files.")
        for member in members:
            parts = _parts(member.name)
            if parts[0] != expected_root:
                raise UpdateError("The Linux archive has an unexpected top-level folder.")
            if len(parts) == 1:
                if not member.isdir():
                    raise UpdateError("The Linux archive root is not a folder.")
                continue
            key = "/".join(parts[1:]).casefold()
            if key in seen:
                raise UpdateError("The update archive contains duplicate paths.")
            seen.add(key)
            if not (member.isfile() or member.isdir()):
                raise UpdateError("Update archive links and special files are not supported.")
            total += member.size
            if total > MAX_UNPACKED_BYTES:
                raise UpdateError("The expanded update exceeds the size limit.")
            target = destination.joinpath(*parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                input_file = source.extractfile(member)
                if input_file is None:
                    raise UpdateError("The update archive contains an unreadable file.")
                with input_file:
                    _copy_member(input_file, target, member.size)
                target.chmod(member.mode & 0o777)


def prepare_fresh_install(
    archive: Path, current_root: Path, parent: Path, version: str, platform: str
) -> Path:
    """Extract verified code and migrate saved data without touching the old install."""
    archive = Path(archive).resolve(strict=True)
    current_root = Path(current_root).resolve(strict=True)
    parent = Path(parent).resolve(strict=True)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise UpdateError("The release version is invalid.")
    if not parent.is_dir():
        raise UpdateError("Select an existing destination folder.")
    if parent == current_root or parent.is_relative_to(current_root):
        raise UpdateError("Choose a folder outside the current Role Weaver installation.")
    if platform == "linux":
        folder_name = f"RoleWeaver-v{version}-Linux"
    elif platform == "win32":
        folder_name = f"RoleWeaver-Portable-v{version}"
    else:
        raise UpdateError(f"Unsupported update platform: {platform}")
    target = parent / folder_name
    if target.exists() or target.is_symlink():
        raise UpdateError(f"The destination already exists: {target}")
    try:
        with tempfile.TemporaryDirectory(prefix=".roleweaver-update-", dir=parent) as temp:
            staging = Path(temp) / "app"
            staging.mkdir()
            if platform == "linux":
                _extract_tar(archive, staging, version)
                launch_file = staging / "start-role-weaver.sh"
            else:
                _extract_zip(archive, staging)
                launch_file = staging / "RoleWeaver.exe"
            marker = staging / "VERSION"
            if not launch_file.is_file() or not marker.is_file():
                raise UpdateError("The update archive is missing its launcher or version file.")
            if marker.read_text(encoding="utf-8").strip() != version:
                raise UpdateError("The update archive version does not match the release.")
            snapshot = Path(temp) / "personal-data.zip"
            create_backup(current_root, snapshot, validate_json=True)
            restore_backup(staging, snapshot)
            if target.exists() or target.is_symlink():
                raise UpdateError(f"The destination already exists: {target}")
            os.rename(staging, target)
            return target
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        raise UpdateError(f"Could not prepare the new installation: {exc}") from exc
