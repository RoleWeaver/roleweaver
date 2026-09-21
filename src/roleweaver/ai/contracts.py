"""Stable request and result types used by every Role Weaver AI provider."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AIRequestPurpose(str, Enum):
    """Why Role Weaver is contacting an AI provider."""

    REPLY = "reply"
    CANDIDATES = "candidates"
    SUMMARY = "summary"
    AFK = "afk"
    TRANSLATION = "translation"
    CONNECTION_TEST = "connection_test"


@dataclass(frozen=True)
class AIRequest:
    """Provider-independent text-generation request."""

    instructions: str
    prompt: str
    purpose: AIRequestPurpose = AIRequestPurpose.REPLY
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def coerce(
        cls,
        value: AIRequest | str,
        prompt: str | None = None,
        *,
        purpose: AIRequestPurpose = AIRequestPurpose.REPLY,
    ) -> AIRequest:
        if isinstance(value, cls):
            return value
        if prompt is None:
            raise TypeError("A prompt is required when instructions are passed as text.")
        return cls(instructions=str(value), prompt=str(prompt), purpose=purpose)


@dataclass(frozen=True)
class AIUsage:
    """Token counts reported by a provider, when available."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    source: str = "unavailable"

    @property
    def available(self) -> bool:
        return any(
            value is not None
            for value in (self.input_tokens, self.output_tokens, self.total_tokens)
        )


@dataclass(frozen=True)
class AIResult:
    """Normalized response returned by every built-in AI provider."""

    text: str
    provider: str
    model: str
    purpose: AIRequestPurpose
    usage: AIUsage = field(default_factory=AIUsage)
    duration_seconds: float = 0.0
    provider_request_id: str = ""

    def __str__(self) -> str:
        return self.text


def coerce_ai_result(
    value: AIResult | str | None,
    *,
    provider: str = "",
    model: str = "",
    purpose: AIRequestPurpose = AIRequestPurpose.REPLY,
    duration_seconds: float = 0.0,
) -> AIResult:
    """Normalize legacy/custom provider text into the structured contract."""

    if isinstance(value, AIResult):
        return value
    return AIResult(
        text=str(value or "").strip(),
        provider=provider,
        model=model,
        purpose=purpose,
        duration_seconds=max(0.0, float(duration_seconds or 0.0)),
    )
