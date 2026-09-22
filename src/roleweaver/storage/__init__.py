"""Durable, platform-neutral persistence services."""

from .atomic import LOCK, append_text, atomic_write_bytes, atomic_write_text, freeze, synchronized
from .backups import create_backup, restore_backup, validate_backup, validate_saved_data
from .recovery import CrashProtection, prepare_gui

__all__ = [
    "CrashProtection",
    "LOCK",
    "append_text",
    "atomic_write_bytes",
    "atomic_write_text",
    "create_backup",
    "freeze",
    "prepare_gui",
    "restore_backup",
    "synchronized",
    "validate_backup",
    "validate_saved_data",
]
