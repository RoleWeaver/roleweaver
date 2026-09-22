"""Configurable, content-free dialogue policy evaluation."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

FALLBACK = "*They steer the conversation toward less troubling matters.*"

CATEGORY_LABELS = {
    "size_format": "Size and control characters",
    "instruction_override": "Prompt and persona override",
    "secret_request": "Secret or credential requests",
    "instruction_leak": "Instruction leakage",
    "model_disclosure": "Out-of-character AI disclosure",
    "pii": "Personal information",
    "toxicity": "Toxic language",
    "harassment": "Harassment and threats",
    "sexual_content": "Explicit sexual content",
    "graphic_violence": "Graphic violence",
    "custom": "Custom terms and expressions",
}

DEFAULT_ACTIONS = {
    "size_format": "block",
    "instruction_override": "block",
    "secret_request": "block",
    "instruction_leak": "block",
    "model_disclosure": "replace",
    "pii": "replace",
    "toxicity": "replace",
    "harassment": "replace",
    "sexual_content": "replace",
    "graphic_violence": "replace",
    "custom": "replace",
}

ACTION_VALUES = ("off", "warn", "block", "replace")

INSTRUCTION_OVERRIDE_PATTERNS = [
    r"\b(?:ignore|discard|abandon|forget)\b.{0,30}\b(?:your|the)\s+"
    r"(?:persona|character|roleplay|role-playing)\b",
    r"\b(?:ignore|disregard|override|forget)\b.{0,60}"
    r"\b(?:system|developer|previous|prior|above|all)\b.{0,35}"
    r"\b(?:instructions?|prompts?|rules)\b",
    r"\b(?:you are now|act as|answer as|become)\s+"
    r"(?:chatgpt|an? ai|an? language model|an? assistant|dan)\b",
    r"(?:<\|(?:im_start|system|developer)\|>|\[/?inst\]|</?(?:system|developer)>)",
]

SECRET_REQUEST_PATTERNS = [
    r"\b(?:reveal|print|show|output|send|give)\b.{0,60}"
    r"\b(?:api[ _-]?keys?|passwords?|tokens?|environment variables|credentials?)\b",
    r"\bsk-(?:proj-)?[a-z0-9_-]{20,}\b",
    r"\bAIza[0-9A-Za-z_-]{30,}\b",
]

INSTRUCTION_LEAK_PATTERNS = [
    r"\b(?:my|the|your)\s+(?:system|developer)\s+(?:prompt|instructions?)\b",
    r"(?:<\|im_start\|>|</?(?:system|developer)>|\[/?inst\])",
    r"\bsk-(?:proj-)?[a-z0-9_-]{20,}\b",
    r"\bAIza[0-9A-Za-z_-]{30,}\b",
]

MODEL_DISCLOSURE_PATTERNS = [r"\bas (?:an? )?(?:ai|language model|chatgpt)\b"]

PII_PATTERNS = [
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)",
    r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)",
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
]

HARASSMENT_PATTERNS = [
    r"\b(?:i(?:'ll| will)|we(?:'ll| will))\s+(?:find|hurt|kill|destroy)\s+you\b",
    r"\byou(?:'re| are)\s+(?:worthless|disgusting|pathetic|subhuman)\b",
]

TOXICITY_PATTERNS = [
    r"\b(?:fuck you|go die|piece of (?:shit|garbage))\b",
    r"\b(?:worthless|disgusting|pathetic)\s+(?:idiot|moron|vermin)\b",
]

SEXUAL_PATTERNS = [
    r"\b(?:explicit sex|sexual assault|rape|nonconsensual sex)\b",
    r"\b(?:pornographic|genitals?)\b",
]

GRAPHIC_VIOLENCE_PATTERNS = [
    r"\b(?:disembowel(?:ed|ing)?|decapitat(?:ed|ing)|dismember(?:ed|ing)?)\b",
    r"\b(?:entrails|gore)\b.{0,35}\b(?:spill|spray|strewn|hang)\w*\b",
]


@dataclass(frozen=True)
class PolicyMatch:
    category: str
    reason: str
    patterns: tuple[str, ...] = ()


def normalized(text: str) -> str:
    return " ".join(
        "".join(
            character
            for character in unicodedata.normalize("NFKC", str(text or ""))
            if unicodedata.category(character) != "Cf"
        )
        .lower()
        .split()
    )


def resolve_action(settings: dict[str, Any], purpose: str, category: str) -> str:
    defaults = settings.get("guardrail_default_policies", {})
    defaults = defaults if isinstance(defaults, Mapping) else {}
    purpose_policies = settings.get("guardrail_purpose_policies", {})
    purpose_policies = purpose_policies if isinstance(purpose_policies, Mapping) else {}
    overrides = purpose_policies.get(purpose, {})
    overrides = overrides if isinstance(overrides, Mapping) else {}
    action = overrides.get(category, defaults.get(category, DEFAULT_ACTIONS[category]))
    return action if action in ACTION_VALUES else DEFAULT_ACTIONS[category]


def validate_custom_patterns(value: str) -> list[str]:
    errors = []
    for line_number, expression in enumerate(_lines(value), 1):
        if line_number > 100:
            errors.append("At most 100 custom expressions are allowed")
            break
        if len(expression) > 256:
            errors.append(f"Custom expression {line_number}: maximum length is 256 characters")
            continue
        if re.search(r"\([^)]*(?:\.\*|\.\+|\[[^]]+\][+*])[^)]*\)[+*{]", expression):
            errors.append(
                f"Custom expression {line_number}: nested repetition is not allowed"
            )
            continue
        try:
            re.compile(expression, re.IGNORECASE)
        except re.error as exc:
            errors.append(f"Custom expression {line_number}: {exc}")
    return errors


def evaluate(
    text: str,
    direction: str,
    *,
    instructions: str = "",
    input_limit: int = 50000,
    output_limit: int = 10000,
    custom_terms: str = "",
    custom_regex: str = "",
) -> list[PolicyMatch]:
    raw = str(text or "")
    value = normalized(raw)
    limit = input_limit if direction == "input" else output_limit
    matches: list[PolicyMatch] = []
    if (
        not raw.strip()
        or len(raw) > limit
        or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", raw)
    ):
        matches.append(
            PolicyMatch("size_format", "Empty, oversized, or invalidly formatted text")
        )

    if direction == "input":
        _append_match(
            matches,
            value,
            "instruction_override",
            "Instruction or persona override attempt",
            INSTRUCTION_OVERRIDE_PATTERNS,
        )
        _append_match(
            matches,
            value,
            "secret_request",
            "Secret or credential disclosure request",
            SECRET_REQUEST_PATTERNS,
        )
    else:
        _append_match(
            matches,
            value,
            "instruction_leak",
            "Possible secret or instruction leakage",
            INSTRUCTION_LEAK_PATTERNS,
        )
        _append_match(
            matches,
            value,
            "model_disclosure",
            "Out-of-character AI disclosure",
            MODEL_DISCLOSURE_PATTERNS,
        )
        protected = normalized(instructions)
        if len(protected) >= 60 and protected[:60] in value:
            matches.append(PolicyMatch("instruction_leak", "Instruction text appeared in output"))

    for category, reason, patterns in (
        ("pii", "Possible personal information", PII_PATTERNS),
        ("toxicity", "Possible toxic language", TOXICITY_PATTERNS),
        ("harassment", "Possible harassment or direct threat", HARASSMENT_PATTERNS),
        ("sexual_content", "Possible explicit sexual content", SEXUAL_PATTERNS),
        ("graphic_violence", "Possible graphic violence", GRAPHIC_VIOLENCE_PATTERNS),
    ):
        _append_match(matches, raw, category, reason, patterns)

    terms = [term for term in _lines(custom_terms)[:100] if len(term) <= 100]
    custom_patterns = [rf"\b{re.escape(term)}\b" for term in terms]
    expressions = _lines(custom_regex)[:100]
    custom_patterns.extend(
        expression
        for expression in expressions
        if not validate_custom_patterns(expression)
    )
    _append_match(
        matches,
        raw,
        "custom",
        "Custom policy expression matched",
        custom_patterns,
    )
    return matches


def redact(text: str, matches: list[PolicyMatch]) -> str:
    value = str(text or "")
    original = value
    for match in matches:
        for pattern in match.patterns:
            try:
                value = re.sub(pattern, "[removed by Role Weaver]", value, flags=re.IGNORECASE)
            except re.error:
                continue
    if value == original and matches:
        return FALLBACK
    return value if value.strip() else FALLBACK


def input_reason(text: str) -> str:
    """Compatibility helper for extensions using the original fixed policy."""

    matches = evaluate(text, "input")
    return matches[0].reason if matches else ""


def output_reason(text: str, instructions: str = "") -> str:
    """Compatibility helper for extensions using the original fixed policy."""

    matches = evaluate(text, "output", instructions=instructions)
    return matches[0].reason if matches else ""


def _append_match(
    matches: list[PolicyMatch],
    value: str,
    category: str,
    reason: str,
    patterns: list[str],
) -> None:
    matched = tuple(pattern for pattern in patterns if re.search(pattern, value, re.IGNORECASE))
    if matched:
        matches.append(PolicyMatch(category, reason, matched))


def _lines(value: Any) -> list[str]:
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]
