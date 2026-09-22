"""Cross-platform game-log following."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event

_LEGACY_ENCODING_BY_LANGUAGE = {
    "polish": "cp1250",
    "pl": "cp1250",
    "russian": "cp1251",
    "ru": "cp1251",
}


class LogFollower:
    """Follow a file that a game may truncate or replace while running."""

    def __init__(
        self,
        path: str | Path,
        poll_interval: float = 0.1,
        *,
        game_language: str | Callable[[], str] = "English",
    ) -> None:
        self.path = Path(path)
        self.poll_interval = poll_interval
        self.game_language = game_language
        self.file = None
        self.identity = None
        self.position = 0
        self.pending_line = b""

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
        self.pending_line = b""

    def _open_at_end(self) -> None:
        self.file = self.path.open("rb")
        stat_result = os.fstat(self.file.fileno())
        self.identity = self._identity_from_stat(stat_result)
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()

    def _open_at_start(self) -> None:
        self.file = self.path.open("rb")
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
                    if self.pending_line.endswith(b"\n"):
                        line = self.pending_line.rstrip(b"\r\n")
                        self.pending_line = b""
                        language = (
                            self.game_language()
                            if callable(self.game_language)
                            else self.game_language
                        )
                        yield self._decode_line(line, game_language=language)
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

    @staticmethod
    def _decode_line(line: bytes, *, game_language: str = "English") -> str:
        """Decode UTF-8 first, then the legacy code page for the game language."""

        legacy_encoding = _LEGACY_ENCODING_BY_LANGUAGE.get(
            str(game_language or "").strip().casefold(), "cp1252"
        )
        for encoding in ("utf-8", legacy_encoding):
            try:
                return line.decode(encoding).lstrip("\ufeff")
            except UnicodeDecodeError:
                continue
        return line.decode("latin-1").lstrip("\ufeff")
