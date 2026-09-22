"""Platform-neutral Neverwinter Nights conversation parsing."""

from __future__ import annotations

import re

from roleweaver.games import parse_nwn2

from .models import ChatEvent

COLOR_TAG_RE = re.compile(r"</?c[^>]*>", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

STRUCTURED_CHAT_RE = re.compile(
    r"^(?:\[(?P<speaker_id>[^\]]+)\]\s+)?"
    r"(?P<speaker>.*?):\s*"
    r"\[(?P<channel>Talk|Whisper|Party|Tell|Shout|DM)\]\s*"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)

GENERIC_AREA_PATTERNS = [
    re.compile(r"\*Now Entering (?P<area>.+?)\*\s*$", re.IGNORECASE),
    re.compile(r"<<\s*You have entered the area:\s*(?P<area>.+?)\.?\s*>>", re.IGNORECASE),
]

ALT_CHANNEL_FIRST_RE = re.compile(
    r"^\[(?P<channel>Talk|Whisper|Party|Tell|Shout|DM)\]\s*"
    r"(?P<speaker>[^:]{1,120}):\s*(?P<message>.*)$",
    re.IGNORECASE,
)
ALT_SPEAKER_CHANNEL_RE = re.compile(
    r"^(?P<speaker>[^\[]+?)\s*\[(?P<channel>Talk|Whisper|Party|Tell|Shout|DM)\]\s*:\s*"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)
CHAT_WINDOW_CHANNEL_RE = re.compile(
    r"^(?P<speaker>[^:]{1,120}):\s*"
    r"\[(?P<channel>Talk|Whisper|Party|Tell|Shout|DM)\]\s*"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)
CHAT_WINDOW_PLAIN_RE = re.compile(
    r"^(?P<speaker>[^:]{1,100}):\s*(?P<message>.+)$",
    re.IGNORECASE,
)
GENERIC_SYSTEM_SPEAKERS = {
    "loading screen",
    "server",
    "area setting",
    "public message board",
    "system",
    "combat log",
    "debug",
}


def clean_nwn_text(text: str) -> str:
    """Remove NWN color tags and non-printing control characters."""

    text = COLOR_TAG_RE.sub("", str(text or ""))
    text = CONTROL_RE.sub("", text)
    return text.strip()


def strip_chat_window_prefix(line: str) -> str:
    """Remove the NWN ``CHAT WINDOW TEXT`` header and optional timestamp."""

    return re.sub(
        r"^\[CHAT WINDOW TEXT\]\s*(?:\[[^\]]+\]\s*)?",
        "",
        str(line or "").strip(),
        flags=re.IGNORECASE,
    )


def build_chat_event(
    speaker: str,
    message: str,
    channel: str,
    character_name: str,
    server_profile: str,
    speaker_id: str = "",
) -> ChatEvent | None:
    """Normalize parser output into the public conversation contract."""

    speaker = clean_nwn_text(speaker)
    message = clean_nwn_text(message)
    channel = str(channel or "Talk").title()
    speaker_id = clean_nwn_text(speaker_id)
    if not speaker or not message:
        return None
    if speaker.casefold() in GENERIC_SYSTEM_SPEAKERS or "message board" in speaker.casefold():
        return None
    if message.startswith("[") and message.endswith("]"):
        return None
    return {
        "speaker_id": speaker_id,
        "speaker": speaker,
        "channel": channel,
        "message": message,
        "self": speaker.casefold() == character_name.casefold(),
        "server_profile": server_profile,
    }


def _parse_standard_structured_chat(
    raw: str, character_name: str, server_profile: str
) -> ChatEvent | None:
    match = STRUCTURED_CHAT_RE.match(raw)
    if not match:
        return None
    return build_chat_event(
        match.group("speaker"),
        match.group("message"),
        match.group("channel"),
        character_name,
        server_profile,
        match.group("speaker_id") or "",
    )


def _looks_like_plain_chat(speaker: str, message: str) -> bool:
    speaker = clean_nwn_text(speaker)
    message = clean_nwn_text(message)
    if not speaker or not message or len(speaker) > 80:
        return False
    lower_speaker = speaker.casefold()
    if lower_speaker in GENERIC_SYSTEM_SPEAKERS:
        return False
    system_prefixes = (
        "experience points",
        "acquired item",
        "lost item",
        "your journal",
        "current module",
        "loading screen",
        "area setting",
        "server",
        "messages for",
        "the date is",
        "the time is",
        "food",
        "rest",
        "piety",
    )
    if lower_speaker.startswith(system_prefixes) or len(speaker.split()) > 8:
        return False
    lead = message.lstrip()[:1]
    return lead in {'"', "'", "*", "[", "("} or len(message.split()) <= 30


def _parse_adaptive_chat(raw: str, character_name: str, server_profile: str) -> ChatEvent | None:
    if raw.startswith("[CHAT WINDOW TEXT]"):
        cleaned = clean_nwn_text(strip_chat_window_prefix(raw))
        match = CHAT_WINDOW_CHANNEL_RE.match(cleaned)
        if match:
            return build_chat_event(
                match.group("speaker"),
                match.group("message"),
                match.group("channel"),
                character_name,
                server_profile,
            )
        match = CHAT_WINDOW_PLAIN_RE.match(cleaned)
        if match and _looks_like_plain_chat(match.group("speaker"), match.group("message")):
            return build_chat_event(
                match.group("speaker"),
                match.group("message"),
                "Talk",
                character_name,
                server_profile,
            )
        return None

    event = _parse_standard_structured_chat(raw, character_name, server_profile)
    if event:
        return event
    for pattern in (ALT_CHANNEL_FIRST_RE, ALT_SPEAKER_CHANNEL_RE):
        match = pattern.match(raw)
        if match:
            return build_chat_event(
                match.group("speaker"),
                match.group("message"),
                match.group("channel"),
                character_name,
                server_profile,
            )
    return None


def detect_log_format(text: str) -> str:
    """Classify the dominant chat representation for diagnostics and caching."""

    counts = {"structured": 0, "channel_first": 0, "speaker_channel": 0, "chat_window": 0}
    for raw in str(text or "").splitlines()[-2500:]:
        line = raw.strip()
        if not line:
            continue
        if STRUCTURED_CHAT_RE.match(line):
            counts["structured"] += 1
        elif ALT_CHANNEL_FIRST_RE.match(line):
            counts["channel_first"] += 1
        elif ALT_SPEAKER_CHANNEL_RE.match(line):
            counts["speaker_channel"] += 1
        elif line.startswith("[CHAT WINDOW TEXT]"):
            cleaned = clean_nwn_text(strip_chat_window_prefix(line))
            if CHAT_WINDOW_CHANNEL_RE.match(cleaned) or CHAT_WINDOW_PLAIN_RE.match(cleaned):
                counts["chat_window"] += 1
    for name in ("structured", "channel_first", "speaker_channel", "chat_window"):
        if counts[name]:
            return name
    return "adaptive"


def parse_chat_line(
    line: str,
    character_name: str,
    server_profile: str = "AUTO",
    parser_profile: str = "adaptive",
    game_version: str = "nwn_ee",
) -> ChatEvent | None:
    """Parse one supported NWN/NWN2 log line into a normalized event."""

    raw = str(line or "").strip()
    if not raw:
        return None
    if str(game_version).startswith("nwn2"):
        return parse_nwn2(raw, character_name, server_profile, build_chat_event)
    mode = str(parser_profile or "adaptive").casefold()
    if mode == "structured":
        if raw.startswith("[CHAT WINDOW TEXT]"):
            return None
        return _parse_standard_structured_chat(raw, character_name, server_profile)
    if mode == "channel_first":
        if raw.startswith("[CHAT WINDOW TEXT]"):
            return None
        match = ALT_CHANNEL_FIRST_RE.match(raw)
        return (
            build_chat_event(
                match.group("speaker"),
                match.group("message"),
                match.group("channel"),
                character_name,
                server_profile,
            )
            if match
            else None
        )
    if mode == "speaker_channel":
        if raw.startswith("[CHAT WINDOW TEXT]"):
            return None
        match = ALT_SPEAKER_CHANNEL_RE.match(raw)
        return (
            build_chat_event(
                match.group("speaker"),
                match.group("message"),
                match.group("channel"),
                character_name,
                server_profile,
            )
            if match
            else None
        )
    if mode == "chat_window":
        if not raw.startswith("[CHAT WINDOW TEXT]"):
            return None
        return _parse_adaptive_chat(raw, character_name, server_profile)
    return _parse_adaptive_chat(raw, character_name, server_profile)
