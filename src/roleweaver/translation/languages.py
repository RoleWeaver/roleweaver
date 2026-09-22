"""Supported language identifiers for Role Weaver translation workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Language:
    code: str
    name: str


SUPPORTED_LANGUAGES = (
    Language("en", "English"),
    Language("de", "German"),
    Language("fr", "French"),
    Language("es", "Spanish"),
    Language("it", "Italian"),
    Language("pt", "Portuguese"),
    Language("nl", "Dutch"),
    Language("pl", "Polish"),
    Language("cs", "Czech"),
    Language("sk", "Slovak"),
    Language("hu", "Hungarian"),
    Language("ro", "Romanian"),
    Language("bg", "Bulgarian"),
    Language("hr", "Croatian"),
    Language("sr", "Serbian"),
    Language("sl", "Slovenian"),
    Language("sv", "Swedish"),
    Language("no", "Norwegian"),
    Language("da", "Danish"),
    Language("fi", "Finnish"),
    Language("tr", "Turkish"),
    Language("ru", "Russian"),
    Language("uk", "Ukrainian"),
    Language("el", "Greek"),
    Language("ar", "Arabic"),
    Language("he", "Hebrew"),
    Language("id", "Indonesian"),
    Language("vi", "Vietnamese"),
    Language("th", "Thai"),
    Language("ja", "Japanese"),
    Language("ko", "Korean"),
    Language("zh-Hans", "Chinese (Simplified)"),
    Language("zh-Hant", "Chinese (Traditional)"),
)

_ALIASES = {
    "eng": "en",
    "deu": "de",
    "ger": "de",
    "fra": "fr",
    "fre": "fr",
    "spa": "es",
    "ita": "it",
    "por": "pt",
    "dut": "nl",
    "nld": "nl",
    "pol": "pl",
    "cze": "cs",
    "ces": "cs",
    "slk": "sk",
    "hun": "hu",
    "rum": "ro",
    "ron": "ro",
    "bul": "bg",
    "hrv": "hr",
    "srp": "sr",
    "slv": "sl",
    "swe": "sv",
    "nor": "no",
    "dan": "da",
    "fin": "fi",
    "tur": "tr",
    "rus": "ru",
    "ukr": "uk",
    "gre": "el",
    "ell": "el",
    "ara": "ar",
    "heb": "he",
    "ind": "id",
    "vie": "vi",
    "tha": "th",
    "jpn": "ja",
    "kor": "ko",
    "zh-cn": "zh-Hans",
    "zh-sg": "zh-Hans",
    "simplified chinese": "zh-Hans",
    "chinese simplified": "zh-Hans",
    "zh-tw": "zh-Hant",
    "zh-hk": "zh-Hant",
    "traditional chinese": "zh-Hant",
    "chinese traditional": "zh-Hant",
}


def resolve_language(value: str | Language, *, allow_auto: bool = False) -> Language | None:
    """Resolve a supported code, name, or common alias; ``None`` represents auto."""

    if isinstance(value, Language):
        value = value.code
    key = " ".join(str(value or "").strip().replace("_", "-").split()).casefold()
    if allow_auto and key in {"auto", "automatic", "detect", "auto-detect"}:
        return None
    if not key:
        raise ValueError("A language is required.")

    by_code = {language.code.casefold(): language for language in SUPPORTED_LANGUAGES}
    by_name = {language.name.casefold(): language for language in SUPPORTED_LANGUAGES}
    alias_code = _ALIASES.get(key)
    language = by_code.get(key) or by_name.get(key)
    if language is None and alias_code:
        language = by_code.get(alias_code.casefold())
    if language is None:
        names = ", ".join(item.name for item in SUPPORTED_LANGUAGES)
        raise ValueError(f"Unsupported language '{value}'. Supported languages: {names}.")
    return language


def language_choices(*, include_auto: bool = False) -> tuple[str, ...]:
    choices = tuple(language.name for language in SUPPORTED_LANGUAGES)
    return ("Auto-detect", *choices) if include_auto else choices
