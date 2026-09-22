"""Cross-platform game-log following."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from pathlib import Path
from threading import Event


class LogFollower:
    """Follow a file that a game may truncate or replace while running."""

    def __init__(self, path: str | Path, poll_interval: float = 0.1) -> None:
        self.path = Path(path)
        self.poll_interval = poll_interval
        self.file = None
        self.identity = None
        self.position = 0
        self.pending_line = ""

    @staticmethod
    def _identity_from_stat(stat_result: os.stat_result) -> tuple[int | None, int | None]:
        return (getattr(stat_result, "st_ino", None), getattr(stat_result, "st_dev", None))

    def _close(self) -> None:
        if self.file:
            try:
                self.file.close()
            except Exception:
                pass
        self.file = None
        self.identity = None
        self.position = 0
        self.pending_line = ""

    def _open_at_end(self) -> None:
        self.file = self.path.open("r", encoding="utf-8", errors="replace")
        stat_result = os.fstat(self.file.fileno())
        self.identity = self._identity_from_stat(stat_result)
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()

    def _open_at_start(self) -> None:
        self.file = self.path.open("r", encoding="utf-8", errors="replace")
        stat_result = os.fstat(self.file.fileno())
        self.identity = self._identity_from_stat(stat_result)
        self.file.seek(0)
        self.position = 0

    def lines(self, stop_event: Event) -> Iterator[str]:
        first_open = True
        while not stop_event.is_set():
            try:
                if self.file is None:
                    if not self.path.exists():
                        time.sleep(0.5)
                        continue
                    if first_open:
                        self._open_at_end()
                        first_open = False
                    else:
                        self._open_at_start()

                fragment = self.file.readline()
                if fragment:
                    self.position = self.file.tell()
                    self.pending_line += fragment
                    if self.pending_line.endswith("\n"):
                        line = self.pending_line.rstrip("\r\n")
                        self.pending_line = ""
                        yield line
                    continue

                try:
                    path_stat = self.path.stat()
                    handle_stat = os.fstat(self.file.fileno())
                    path_identity = self._identity_from_stat(path_stat)
                    handle_identity = self._identity_from_stat(handle_stat)
                    replaced = (
                        path_identity != (None, None)
                        and handle_identity != (None, None)
                        and path_identity != handle_identity
                    )
                    truncated = path_stat.st_size < self.position
                    if replaced or truncated:
                        self._close()
                        continue
                except FileNotFoundError:
                    self._close()
                    continue

                time.sleep(self.poll_interval)
            except (PermissionError, OSError) as exc:
                print(f"[LOG] Waiting for readable log file: {exc}")
                self._close()
                time.sleep(0.5)
        self._close()
