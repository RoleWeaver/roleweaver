"""Verify that the release's developer ZIP is useful and free of runtime data."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path, PurePosixPath

REQUIRED = frozenset(
    {
        "README.md",
        "DEVELOPMENT.md",
        "DEVELOPER_PACKAGE.md",
        "CONTRIBUTING.md",
        "ARCHITECTURE.md",
        "TRANSLATION.md",
        "UPDATES.md",
        "PUBLIC_RELEASE_CHECKLIST.md",
        "pyproject.toml",
        "LICENSE",
        "VERSION",
        "nwn_ai_bot.py",
        "nwn_ai_gui.py",
        "linux/nwn_ai_bot.py",
        "linux/nwn_ai_gui.py",
        "linux/install-linux.sh",
        "linux/CONTRIBUTING.md",
        "src/roleweaver/ai/contracts.py",
        "src/roleweaver/translation/service.py",
        "src/roleweaver/update_install.py",
        "tests/test_source_integrity.py",
        "tests/test_updates.py",
        "scripts/check_source_integrity.py",
        "scripts/check_developer_package.py",
    }
)
PRIVATE_PARTS = frozenset({".venv", "venv", "roleweaver_data", "backups", "__pycache__"})
PRIVATE_FILES = frozenset({"settings.json", ".env"})
PRIVATE_SUFFIXES = (".log", ".sqlite3", ".pyc", ".pem", ".key", ".p12")


def check_developer_package(archive: Path) -> list[str]:
    """Return errors for a developer source archive built with git archive."""
    prefix = archive.stem + "/"
    errors = []
    try:
        with zipfile.ZipFile(archive) as source:
            names = source.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        return [f"Could not read developer ZIP: {exc}"]
    if not archive.stem.startswith("RoleWeaver-Developer-v"):
        errors.append("Developer ZIP must use the RoleWeaver-Developer-vVERSION name.")
    unexpected = [name for name in names if not name.startswith(prefix)]
    if unexpected:
        errors.append(f"Files outside the archive root: {unexpected[:3]}")
    members = {name[len(prefix) :] for name in names if name.startswith(prefix)}
    for missing in sorted(REQUIRED - members):
        errors.append(f"Missing developer package file: {missing}")
    for name in sorted(members):
        parts = PurePosixPath(name).parts
        if (
            any(part.casefold() in PRIVATE_PARTS for part in parts)
            or PurePosixPath(name).name.casefold() in PRIVATE_FILES
            or name.lower().endswith(PRIVATE_SUFFIXES)
        ):
            errors.append(f"Runtime or private data in developer ZIP: {name}")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/check_developer_package.py path/to/developer.zip")
    findings = check_developer_package(Path(sys.argv[1]))
    for finding in findings:
        print(finding)
    if findings:
        raise SystemExit(1)
    print("Developer source ZIP contains the required files and no known runtime data.")
