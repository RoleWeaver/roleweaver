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
_SDK_COMPONENTS: tuple[Any, Any, str] | None = None
_ACTION_PRIORITY = {"warn": 1, "replace": 2, "block": 3}


def _load_sdk() -> tuple[Any, Any, str]:
    """Load Guardrails once per process without enabling remote telemetry."""

    global _SDK_COMPONENTS
    with _SDK_LOCK:
        if _SDK_COMPONENTS is None:
            from guardrails import Guard
            from guardrails_ai.regex_match import RegexMatch

            _SDK_COMPONENTS = (Guard, RegexMatch, version("guardrails-ai"))
        return _SDK_COMPONENTS


class GuardrailsAIBackend:
    name = "Guardrails AI"

    def __init__(
        self,
        input_limit: int = 50000,
        output_limit: int = 10000,
        settings: dict[str, Any] | None = None,
    ) -> None:
        self.settings = settings or {}
        self.input_limit = max(1, int(input_limit))
        self.output_limit = max(1, int(output_limit))
        self.local = threading.local()
        self.error = ""
        try:
            self.Guard, self.RegexMatch, self.version = _load_sdk()
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
                )
            )
            setattr(self.local, direction, guard)
        return guard

    def _validate(self, text: str, direction: str, context: dict[str, Any]) -> GuardrailResult:
        sdk_format_failed = False
        if not self.error:
            try:
                outcome = self._guard(direction).validate(text, num_reasks=0)
                sdk_format_failed = not outcome.validation_passed
            finally:
                guard = getattr(self.local, direction, None)
                if guard is not None:
                    guard.history.clear()

        matches = policy.evaluate(
            text,
            direction,
            instructions=context.get("instructions", ""),
            input_limit=self.input_limit,
            output_limit=self.output_limit,
            custom_terms=self.settings.get("guardrail_custom_terms", ""),
            custom_regex=self.settings.get("guardrail_custom_regex", ""),
        )
        if sdk_format_failed and not any(match.category == "size_format" for match in matches):
            matches.insert(
                0,
                policy.PolicyMatch("size_format", "Guardrails AI rejected the text format"),
            )

        purpose = str(context.get("purpose", "reply"))
        active = [
            (match, policy.resolve_action(self.settings, purpose, match.category))
            for match in matches
        ]
        active = [(match, action) for match, action in active if action != "off"]
        backend = self.name if not self.error else "Built-in safety fallback"
        if not active:
            return GuardrailResult(text=text, backend=backend, direction=direction)

        selected_action = max(active, key=lambda item: _ACTION_PRIORITY[item[1]])[1]
        action = GuardrailAction(selected_action)
        categories = tuple(dict.fromkeys(match.category for match, _action in active))
        reasons = "; ".join(dict.fromkeys(match.reason for match, _action in active))
        replacement = text
        if action == GuardrailAction.REPLACE:
            replacement_matches = [
                match for match, match_action in active if match_action == "replace"
            ]
            if direction == "input":
                replacement = policy.redact(text, replacement_matches)
            else:
                replacement = str(
                    self.settings.get("guardrail_replacement_text", policy.FALLBACK)
                    or policy.FALLBACK
                )
        return GuardrailResult(
            action=action,
            reason=reasons,
            text=replacement,
            backend=backend,
            categories=categories,
            category_actions=tuple((match.category, action) for match, action in active),
            direction=direction,
        )

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
