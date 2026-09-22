"""Shared translation contracts, languages, and service."""

from .contracts import (
    ProtectedTermError,
    TranslatedMessage,
    TranslationDirection,
    TranslationError,
    TranslationMessage,
    TranslationRequest,
    TranslationResponseError,
    TranslationResult,
)
from .languages import SUPPORTED_LANGUAGES, Language, language_choices, resolve_language
from .service import TranslationService

__all__ = [
    "Language",
    "ProtectedTermError",
    "SUPPORTED_LANGUAGES",
    "TranslatedMessage",
    "TranslationDirection",
    "TranslationError",
    "TranslationMessage",
    "TranslationRequest",
    "TranslationResponseError",
    "TranslationResult",
    "TranslationService",
    "language_choices",
    "resolve_language",
]
