"""Serialized, durable replacement of saved client files."""
from functools import wraps
import os
from pathlib import Path
import stat
import tempfile
import threading

LOCK = threading.RLock()
_frozen = False


def synchronized(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with LOCK:
            return function(*args, **kwargs)
    return wrapped


def sync_directory(path):
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


@synchronized
def freeze():
    """Reject late daemon-thread saves after the GUI has closed."""
    global _frozen
    _frozen = True


@synchronized
def atomic_write_bytes(path, data):
    if _frozen:
        raise RuntimeError("Role Weaver is closing; saved data is now read-only")
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"Refusing to replace a symbolic link: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".rw-save-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return len(data)


def atomic_write_text(path, text, encoding="utf-8"):
    atomic_write_bytes(path, text.encode(encoding))
    return len(text)


@synchronized
def append_text(path, text, encoding="utf-8"):
    """Replace history as a whole so an interrupted append cannot leave half a line."""
    path = Path(path)
    existing = path.read_bytes() if path.exists() else b""
    atomic_write_bytes(path, existing + text.encode(encoding))
