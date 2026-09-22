"""Stable conversation event types shared by all Role Weaver clients."""

from __future__ import annotations

from typing import TypedDict


class ChatEvent(TypedDict, total=False):
    """A normalized chat message produced by a supported game-log parser.

    ``total=False`` keeps the contract compatible with older extensions that
    construct partial event dictionaries while documenting the fields the
    built-in client may provide.
    """

    speaker_id: str
    speaker: str
    channel: str
    message: str
    self: bool
    server_profile: str
    recipient: str
