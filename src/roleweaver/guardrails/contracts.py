"""Replaceable guardrail backend contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class GuardrailAction(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"
    REPLACE = "replace"


@dataclass(frozen=True)
class GuardrailResult:
    action: GuardrailAction = GuardrailAction.PASS
    reason: str = ""
    text: str = ""
    backend: str = ""

    @property
    def allowed(self) -> bool:
        return self.action in {GuardrailAction.PASS, GuardrailAction.WARN}


class GuardrailBackend(Protocol):
    name: str

    def validate_input(self, text: str, context: dict[str, Any]) -> GuardrailResult: ...

    def validate_output(self, text: str, context: dict[str, Any]) -> GuardrailResult: ...

    def status(self) -> dict[str, Any]: ...


class GuardrailViolation(RuntimeError):
    """A request or result was rejected by the configured guardrail backend."""

