"""Guarded, observable execution of provider-neutral AI requests."""

from __future__ import annotations

import time
import uuid
from dataclasses import replace
from typing import Any

from roleweaver.guardrails import (
    GuardrailAction,
    GuardrailResult,
    GuardrailsAIBackend,
    GuardrailViolation,
)

from .contracts import AIRequest, AIResult, AIUsage, coerce_ai_result
from .usage import UsageStore

_ACTION_PRIORITY = {"pass": 0, "warn": 1, "replace": 2, "block": 3, "error": 4}


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
            settings=settings,
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
        strongest_action = "pass"
        provider_calls = 0
        try:
            input_check = self.guardrails.validate_input(request.prompt, context)
            strongest_action = _stronger(strongest_action, input_check.action.value)
            self._record_guardrail(request, input_check)
            if not input_check.allowed:
                raise GuardrailViolation(input_check.reason)
            effective_request = (
                replace(request, prompt=input_check.text)
                if input_check.action == GuardrailAction.REPLACE
                else request
            )

            provider_calls += 1
            result = self._provider_result(effective_request, provider, model, started)
            output_check = self.guardrails.validate_output(result.text, context)
            strongest_action = _stronger(strongest_action, output_check.action.value)
            self._record_guardrail(request, output_check)

            if (
                output_check.action in {GuardrailAction.BLOCK, GuardrailAction.REPLACE}
                and self.settings.get("guardrail_retry_output_once", True)
            ):
                provider_calls += 1
                result, output_check = self._retry_output(
                    effective_request,
                    result,
                    output_check,
                    provider,
                    model,
                    context,
                )
                strongest_action = _stronger(strongest_action, output_check.action.value)
                self._record_guardrail(request, output_check)

            if not output_check.allowed:
                raise GuardrailViolation(output_check.reason)
            if output_check.action == GuardrailAction.REPLACE:
                result = replace(result, text=output_check.text)

            self.usage.record(
                request,
                session=self.session,
                result=result,
                guardrail_action=strongest_action,
                input_rate=_rate(self.settings.get("usage_input_cost_per_million")),
                output_rate=_rate(self.settings.get("usage_output_cost_per_million")),
                provider_calls=provider_calls,
            )
            return result
        except Exception as exc:
            action = "block" if isinstance(exc, GuardrailViolation) else "error"
            self.usage.record(
                request,
                session=self.session,
                status="error",
                result=result,
                duration_seconds=time.perf_counter() - started,
                guardrail_action=_stronger(strongest_action, action),
                error=exc,
                provider=provider,
                model=model,
                input_rate=_rate(self.settings.get("usage_input_cost_per_million")),
                output_rate=_rate(self.settings.get("usage_output_cost_per_million")),
                provider_calls=provider_calls,
            )
            raise

    def _provider_result(
        self,
        request: AIRequest,
        provider: str,
        model: str,
        started: float,
    ) -> AIResult:
        raw = self.provider.generate(request)
        return coerce_ai_result(
            raw,
            provider=provider,
            model=model,
            purpose=request.purpose,
            duration_seconds=time.perf_counter() - started,
        )

    def _retry_output(
        self,
        request: AIRequest,
        first: AIResult,
        failed: GuardrailResult,
        provider: str,
        model: str,
        context: dict[str, Any],
    ) -> tuple[AIResult, GuardrailResult]:
        categories = ", ".join(failed.categories) or "policy"
        retry_request = replace(
            request,
            instructions=(
                request.instructions
                + "\n\nThe previous draft was rejected by Role Weaver's "
                + categories
                + " guardrail. Produce a fresh answer that follows the original task while "
                "avoiding the rejected material. Do not mention this retry or the guardrail."
            ),
        )
        retry_started = time.perf_counter()
        second = self._provider_result(retry_request, provider, model, retry_started)
        combined = _combine_results(first, second)
        retry_context = {**context, "instructions": retry_request.instructions, "retry": True}
        return combined, self.guardrails.validate_output(second.text, retry_context)

    def _record_guardrail(self, request: AIRequest, result: GuardrailResult) -> None:
        self.usage.record_guardrail(
            session=self.session,
            purpose=request.purpose.value,
            direction=result.direction,
            categories=result.categories,
            action=result.action.value,
            backend=result.backend,
            category_actions=result.category_actions,
        )

    def status(self) -> dict[str, Any]:
        return self.guardrails.status()


def _combine_results(first: AIResult, second: AIResult) -> AIResult:
    usage = AIUsage(
        input_tokens=_sum_known(first.usage.input_tokens, second.usage.input_tokens),
        output_tokens=_sum_known(first.usage.output_tokens, second.usage.output_tokens),
        total_tokens=_sum_known(first.usage.total_tokens, second.usage.total_tokens),
        source=(
            "provider"
            if first.usage.source == "provider" and second.usage.source == "provider"
            else "unavailable"
        ),
    )
    return replace(
        second,
        usage=usage,
        duration_seconds=first.duration_seconds + second.duration_seconds,
    )


def _sum_known(first: int | None, second: int | None) -> int | None:
    return first + second if first is not None and second is not None else None


def _stronger(first: str, second: str) -> str:
    return second if _ACTION_PRIORITY.get(second, 0) > _ACTION_PRIORITY.get(first, 0) else first


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
