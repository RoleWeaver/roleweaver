"""Public conversation parsing and log-following API."""

from .follower import LogFollower
from .models import ChatEvent
from .parsing import (
    GENERIC_AREA_PATTERNS,
    clean_nwn_text,
    detect_log_format,
    parse_chat_line,
    strip_chat_window_prefix,
)

__all__ = [
    "ChatEvent",
    "GENERIC_AREA_PATTERNS",
    "LogFollower",
    "clean_nwn_text",
    "detect_log_format",
    "parse_chat_line",
    "strip_chat_window_prefix",
]
