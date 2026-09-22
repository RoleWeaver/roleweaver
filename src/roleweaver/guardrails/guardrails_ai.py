"""Guardrails AI implementation of the client guardrail contract."""

from __future__ import annotations

import os
import threading
from importlib.metadata import version
from typing import Any

from . import policy
from .contracts import GuardrailAction, GuardrailResult

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

_SDK_LOCK = threading.Lock()
_SDK_COMPONENTS: tuple[Any, Any, Any, str] | None = None


def _load_sdk() -> tuple[Any, Any, Any, str]:
    """Load Guardrails and register Role Weaver's validator once per process."""

    global _SDK_COMPONENTS
    with _SDK_LOCK:
        if _SDK_COMPONENTS is not None:
            return _SDK_COMPONENTS

        from guardrails import Guard
        from guardrails.validators import FailResult, PassResult, Validator, register_validator
        from guardrails_ai.regex_match import RegexMatch

        @register_validator(name="roleweaver/client-dialogue-policy", data_type="string")
        class DialoguePolicy(Validator):
            def _validate(self, value, metadata):
                if metadata["direction"] == "input":
                    reason = policy.input_reason(value)
                else:
                    reason = policy.output_reason(value, metadata.get("instructions", ""))
                return FailResult(error_message=reason) if reason else PassResult()

        _SDK_COMPONENTS = (Guard, RegexMatch, DialoguePolicy, version("guardrails-ai"))
        return _SDK_COMPONENTS


class GuardrailsAIBackend:
    name = "Guardrails AI"

    def __init__(self, input_limit: int = 50000, output_limit: int = 10000) -> None:
        self.input_limit = max(1, int(input_limit))
        self.output_limit = max(1, int(output_limit))
        self.local = threading.local()
        self.error = ""
        try:
            self.Guard, self.RegexMatch, self.DialoguePolicy, self.version = _load_sdk()
        except Exception as exc:
            self.error = f"Guardrails AI is unavailable: {type(exc).__name__}: {exc}"
            self.version = ""

    def _guard(self, direction: str):
        if self.error:
            raise RuntimeError(self.error)
        guard = getattr(self.local, direction, None)
        if guard is None:
            limit = self.input_limit if direction == "input" else self.output_limit
            guard = self.Guard(use_server=False, history_max_length=1)
            guard.configure(allow_metrics_collection=False)
            guard.use(
                self.RegexMatch(
                    regex=rf"\A(?=[\s\S]*\S)[^\x00-\x08\x0b\x0c\x0e-\x1f\x7f]{{1,{limit}}}\Z",
                    on_fail="noop",
                ),
                self.DialoguePolicy(on_fail="noop"),
            )
            setattr(self.local, direction, guard)
        return guard

    def _validate(self, text: str, direction: str, context: dict[str, Any]) -> GuardrailResult:
        if self.error:
            limit = self.input_limit if direction == "input" else self.output_limit
            reason = (
                policy.input_reason(text)
                if direction == "input"
                else policy.output_reason(text, context.get("instructions", ""))
            )
            if not str(text or "").strip() or len(text) > limit or reason:
                return GuardrailResult(
                    GuardrailAction.BLOCK,
                    reason or f"{direction.title()} exceeds the configured size limit.",
                    backend="Built-in safety fallback",
                )
            return GuardrailResult(text=text, backend="Built-in safety fallback")
        try:
            guard = self._guard(direction)
            outcome = guard.validate(
                text,
                metadata={"direction": direction, **context},
                num_reasks=0,
            )
            if outcome.validation_passed:
                return GuardrailResult(text=text, backend=self.name)
            return GuardrailResult(
                GuardrailAction.BLOCK,
                f"Guardrails AI declined {direction} dialogue.",
                backend=self.name,
            )
        finally:
            guard = getattr(self.local, direction, None)
            if guard is not None:
                guard.history.clear()

    def validate_input(self, text: str, context: dict[str, Any]) -> GuardrailResult:
        return self._validate(text, "input", context)

    def validate_output(self, text: str, context: dict[str, Any]) -> GuardrailResult:
        return self._validate(text, "output", context)

    def status(self) -> dict[str, Any]:
        return {
            "backend": self.name,
            "available": not self.error,
            "degraded": bool(self.error),
            "version": self.version,
            "error": self.error,
        }
