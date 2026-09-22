"""Provider-neutral translation request and result contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from roleweaver.ai import AIResult, AIUsage

from .languages import Language

MAX_TRANSLATION_MESSAGES = 50
MAX_PROTECTED_TERMS = 200
MAX_PROTECTED_TERM_CHARACTERS = 100


class TranslationDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class TranslationError(RuntimeError):
    """Base error for a translation request that could not be completed safely."""


class TranslationResponseError(TranslationError):
    """The provider returned an invalid or incomplete structured translation."""


class ProtectedTermError(TranslationResponseError):
    """A protected name or term was lost, duplicated, or changed."""


@dataclass(frozen=True, slots=True)
class TranslationMessage:
    id: str
    text: str
    speaker: str = ""
    channel: str = ""

    def __post_init__(self) -> None:
        identifier = str(self.id or "").strip()
        text = str(self.text or "")
        if not identifier or len(identifier) > 128 or re.search(r"[\x00-\x1f\x7f]", identifier):
            raise ValueError("Translation message IDs must be 1-128 printable characters.")
        if not text.strip():
            raise ValueError("Translation messages cannot be empty.")
        object.__setattr__(self, "id", identifier)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "speaker", str(self.speaker or ""))
        object.__setattr__(self, "channel", str(self.channel or ""))


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    source_language: str | Language
    target_language: str | Language
    messages: tuple[TranslationMessage, ...]
    direction: TranslationDirection = TranslationDirection.INCOMING
    protected_terms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        messages = tuple(self.messages)
        terms = tuple(str(term).strip() for term in self.protected_terms if str(term).strip())
        try:
            direction = TranslationDirection(self.direction)
        except ValueError as exc:
            raise ValueError("Translation direction must be incoming or outgoing.") from exc
        if not messages:
            raise ValueError("At least one translation message is required.")
        if not all(isinstance(message, TranslationMessage) for message in messages):
            raise TypeError("Every translation message must be a TranslationMessage.")
        if len(messages) > MAX_TRANSLATION_MESSAGES:
            raise ValueError(
                f"At most {MAX_TRANSLATION_MESSAGES} messages can be translated at once."
            )
        identifiers = [message.id for message in messages]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Translation message IDs must be unique within a request.")
        if len(terms) > MAX_PROTECTED_TERMS:
            raise ValueError(f"At most {MAX_PROTECTED_TERMS} protected terms are allowed.")
        if any(len(term) > MAX_PROTECTED_TERM_CHARACTERS for term in terms):
            raise ValueError(
                f"Protected terms cannot exceed {MAX_PROTECTED_TERM_CHARACTERS} characters."
            )
        if any(
            re.search(r"[\x00-\x1f\x7f]", term) or "__RW_PROTECTED_TERM_" in term
            for term in terms
        ):
            raise ValueError("Protected terms must be printable text without reserved tokens.")
        object.__setattr__(self, "messages", messages)
        object.__setattr__(self, "protected_terms", terms)
        object.__setattr__(self, "direction", direction)


@dataclass(frozen=True, slots=True)
class TranslatedMessage:
    id: str
    original_text: str
    translated_text: str
    speaker: str = ""
    channel: str = ""
    detected_source_language: Language | None = None


@dataclass(frozen=True, slots=True)
class TranslationResult:
    source_language: Language | None
    target_language: Language
    detected_source_language: Language | None
    direction: TranslationDirection
    messages: tuple[TranslatedMessage, ...]
    ai_result: AIResult | None = None
    passthrough: bool = False
    _by_id: dict[str, TranslatedMessage] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "_by_id", {message.id: message for message in self.messages})

    def message(self, identifier: str) -> TranslatedMessage:
        return self._by_id[identifier]

    @property
    def provider(self) -> str:
        return self.ai_result.provider if self.ai_result else ""

    @property
    def model(self) -> str:
        return self.ai_result.model if self.ai_result else ""

    @property
    def usage(self) -> AIUsage:
        return self.ai_result.usage if self.ai_result else AIUsage()
