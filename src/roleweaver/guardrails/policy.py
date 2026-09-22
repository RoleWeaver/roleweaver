"""Client-side instruction and secret-leak policy."""

from __future__ import annotations

import re
import unicodedata

FALLBACK = "Let us keep to matters of this world. What do you need?"
INPUT_PATTERNS = [
    r"\b(?:ignore|discard|abandon|forget)\b.{0,30}\b(?:your|the)\s+(?:persona|character|roleplay|role-playing)\b",
    r"\b(?:reveal|print|show|output)\b.{0,50}\b(?:api[ _-]?keys?|environment variables)\b",
    r"\b(?:ignore|disregard|override|forget)\b.{0,60}\b(?:system|developer|previous|prior|above|all)\b.{0,35}\b(?:instructions?|prompts?|rules)\b",
    r"\b(?:reveal|print|repeat|show|quote|output)\b.{0,65}\b(?:system|developer|hidden|internal)\s+(?:prompt|instructions?)\b",
    (
        r"\b(?:you are now|act as|answer as|become)\s+"
        r"(?:chatgpt|an? ai|an? language model|an? assistant|dan)\b"
    ),
    r"(?:<\|(?:im_start|system|developer)\|>|\[/?inst\]|</?(?:system|developer)>)",
]
OUTPUT_PATTERNS = [
    r"\bsk-(?:proj-)?[a-z0-9_-]{20,}\b",
    r"\bas (?:an? )?(?:ai|language model|chatgpt)\b",
    r"\b(?:my|the|your)\s+(?:system|developer)\s+(?:prompt|instructions?)\b",
    r"(?:<\|im_start\|>|</?(?:system|developer)>|\[/?inst\])",
]


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


def input_reason(text: str) -> str:
    value = normalized(text)
    if any(re.search(pattern, value) for pattern in INPUT_PATTERNS):
        return "Instruction override attempt"
    return ""


def output_reason(text: str, instructions: str = "") -> str:
    value = normalized(text)
    if any(re.search(pattern, value) for pattern in OUTPUT_PATTERNS):
        return "Out-of-character or instruction-leaking reply"
    protected = normalized(instructions)
    if len(protected) >= 60 and protected[:60] in value:
        return "Instruction text appeared in the reply"
    return ""
