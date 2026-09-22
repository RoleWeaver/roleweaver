"""Guarded, observable execution of provider-neutral AI requests."""

from __future__ import annotations

import time
import uuid
from typing import Any

from roleweaver.guardrails import GuardrailsAIBackend, GuardrailViolation

from .contracts import AIRequest, AIResult, coerce_ai_result
from .usage import UsageStore


class AIExecutionService:
    def __init__(
        self,
        provider: Any,
        settings: dict[str, Any],
        usage_store: UsageStore,
        guardrail_backend: Any | None = None,
    ) -> None:
        self.provider = provider
        self.settings = settings
        self.usage = usage_store
        self.guardrails = guardrail_backend or GuardrailsAIBackend(
            settings.get("guardrail_input_max_characters", 50000),
            settings.get("guardrail_output_max_characters", 10000),
        )
        self.session = uuid.uuid4().hex

    def generate(self, request: AIRequest) -> AIResult:
        started = time.perf_counter()
        provider = _label(
            getattr(self.provider, "provider_name", None),
            self.settings.get("ai_provider", ""),
        )
        model = _label(getattr(self.provider, "model", None), self.settings.get("model", ""))
        context = {"purpose": request.purpose.value, "instructions": request.instructions}
        result = None
        try:
            checked = self.guardrails.validate_input(request.prompt, context)
            if not checked.allowed:
                raise GuardrailViolation(checked.reason)
            raw = self.provider.generate(request)
            result = coerce_ai_result(
                raw,
                provider=provider,
                model=model,
                purpose=request.purpose,
                duration_seconds=time.perf_counter() - started,
            )
            checked = self.guardrails.validate_output(result.text, context)
            if not checked.allowed:
                raise GuardrailViolation(checked.reason)
            self.usage.record(
                request,
                session=self.session,
                result=result,
                guardrail_action=checked.action.value,
                input_rate=_rate(self.settings.get("usage_input_cost_per_million")),
                output_rate=_rate(self.settings.get("usage_output_cost_per_million")),
            )
            return result
        except Exception as exc:
            self.usage.record(
                request,
                session=self.session,
                status="error",
                result=result,
                duration_seconds=time.perf_counter() - started,
                guardrail_action="block" if isinstance(exc, GuardrailViolation) else "error",
                error=exc,
                provider=provider,
                model=model,
                input_rate=_rate(self.settings.get("usage_input_cost_per_million")),
                output_rate=_rate(self.settings.get("usage_output_cost_per_million")),
            )
            raise

    def status(self) -> dict[str, Any]:
        return self.guardrails.status()


def _rate(value: Any) -> float | None:
    try:
        rate = float(value)
        return rate if 0 <= rate <= 10000 else None
    except (TypeError, ValueError):
        return None


def _label(value: Any, fallback: Any) -> str:
    """Keep dynamic/mock provider metadata out of persistent usage rows."""

    selected = value if isinstance(value, str) else fallback
    return selected if isinstance(selected, str) else ""
