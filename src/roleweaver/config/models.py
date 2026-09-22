"""Typed settings contract and defaults for the desktop clients."""

from __future__ import annotations

from typing import Any, TypedDict

GUARDRAIL_POLICY_VERSION = 2
GUARDRAIL_INPUT_MAX_CHARACTERS = 50000
GUARDRAIL_OUTPUT_MAX_CHARACTERS = 10000
GUARDRAIL_REPLACEMENT_TEXT = (
    "*They steer the conversation toward less troubling matters.*"
)
PG_GUARDRAIL_ACTIONS = {
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
SUMMARY_GUARDRAIL_OVERRIDES = {
    "toxicity": "warn",
    "harassment": "warn",
    "sexual_content": "warn",
    "graphic_violence": "warn",
}
LEGACY_GUARDRAIL_ACTIONS = {
    **PG_GUARDRAIL_ACTIONS,
    "pii": "warn",
    "toxicity": "warn",
    "harassment": "warn",
    "sexual_content": "warn",
    "graphic_violence": "warn",
    "custom": "block",
}


class RoleWeaverSettings(TypedDict, total=False):
    """Documented built-in settings; extensions may preserve additional keys."""

    game_version: str
    game_profiles: dict[str, dict[str, Any]]
    server_profile: str
    server_log_paths: dict[str, str]
    discovered_servers: dict[str, dict[str, Any]]
    parser_profile: str
    log_path: str
    character_name: str
    ai_provider: str
    model: str
    lm_studio_base_url: str
    window_title_contains: str
    poll_interval_seconds: float
    context_messages: int
    max_reply_characters: int
    auto_reply_delay_seconds: float
    auto_reply_cooldown_seconds: float
    auto_reply_channels: list[str]
    start_paused: bool
    auto_reply_on_start: bool
    focus_game_before_typing: bool
    keyboard_method: str
    focus_delay_seconds: float
    chat_open_delay_seconds: float
    before_send_delay_seconds: float
    memory_enabled: bool
    summary_interval_messages: int
    memory_max_characters_per_person: int
    interaction_history_limit: int
    memory_relevant_events_per_person: int
    story_thread_limit: int
    learned_voice_enabled: bool
    learned_voice_sample_limit: int
    tell_context_messages: int
    generation_timing: bool
    ignore_ooc_for_ai: bool
    response_length_mode: str
    candidate_count: int
    campaign_id: str
    character_mismatch_check: bool
    guardrail_backend: str
    guardrail_policy_version: int
    guardrail_input_max_characters: int
    guardrail_output_max_characters: int
    guardrail_default_policies: dict[str, str]
    guardrail_purpose_policies: dict[str, dict[str, str]]
    guardrail_custom_terms: str
    guardrail_custom_regex: str
    guardrail_replacement_text: str
    guardrail_retry_output_once: bool
    usage_input_cost_per_million: float | None
    usage_output_cost_per_million: float | None
    user_language: str
    game_language: str
    translation_auto_detect: bool
    translation_continuous: bool
    translation_protected_terms: str


def default_settings(default_log_path: str, *, keyboard_method: str) -> RoleWeaverSettings:
    """Create independent defaults with the few platform values injected."""

    return {
        "game_version": "nwn_ee",
        "server_profile": "AUTO",
        "server_log_paths": {"AUTO": default_log_path},
        "discovered_servers": {},
        "parser_profile": "adaptive",
        "log_path": default_log_path,
        "character_name": "Example NPC",
        "ai_provider": "Google Gemini",
        "model": "gemini-3.7-flash",
        "lm_studio_base_url": "http://127.0.0.1:1234",
        "window_title_contains": "Neverwinter Nights",
        "poll_interval_seconds": 0.10,
        "context_messages": 30,
        "max_reply_characters": 430,
        "auto_reply_delay_seconds": 2.5,
        "auto_reply_cooldown_seconds": 8.0,
        "auto_reply_channels": ["Talk", "Whisper"],
        "start_paused": False,
        "auto_reply_on_start": False,
        "focus_game_before_typing": True,
        "keyboard_method": keyboard_method,
        "focus_delay_seconds": 0.60,
        "chat_open_delay_seconds": 0.45,
        "before_send_delay_seconds": 0.35,
        "memory_enabled": True,
        "summary_interval_messages": 18,
        "memory_max_characters_per_person": 1600,
        "interaction_history_limit": 60,
        "memory_relevant_events_per_person": 6,
        "story_thread_limit": 30,
        "learned_voice_enabled": True,
        "learned_voice_sample_limit": 80,
        "tell_context_messages": 20,
        "generation_timing": True,
        "ignore_ooc_for_ai": True,
        "response_length_mode": "Auto",
        "candidate_count": 3,
        "campaign_id": "default",
        "character_mismatch_check": True,
        "guardrail_backend": "guardrails_ai",
        "guardrail_policy_version": GUARDRAIL_POLICY_VERSION,
        "guardrail_input_max_characters": GUARDRAIL_INPUT_MAX_CHARACTERS,
        "guardrail_output_max_characters": GUARDRAIL_OUTPUT_MAX_CHARACTERS,
        "guardrail_default_policies": dict(PG_GUARDRAIL_ACTIONS),
        "guardrail_purpose_policies": {
            "summary": dict(SUMMARY_GUARDRAIL_OVERRIDES),
        },
        "guardrail_custom_terms": "",
        "guardrail_custom_regex": "",
        "guardrail_replacement_text": GUARDRAIL_REPLACEMENT_TEXT,
        "guardrail_retry_output_once": True,
        "usage_input_cost_per_million": None,
        "usage_output_cost_per_million": None,
        "user_language": "English",
        "game_language": "English",
        "translation_auto_detect": True,
        "translation_continuous": False,
        "translation_protected_terms": "",
    }


def restore_guardrail_defaults(settings: dict[str, Any]) -> dict[str, Any]:
    """Restore the shipped guardrail profile without changing usage pricing."""

    settings.update(
        guardrail_backend="guardrails_ai",
        guardrail_policy_version=GUARDRAIL_POLICY_VERSION,
        guardrail_input_max_characters=GUARDRAIL_INPUT_MAX_CHARACTERS,
        guardrail_output_max_characters=GUARDRAIL_OUTPUT_MAX_CHARACTERS,
        guardrail_default_policies=dict(PG_GUARDRAIL_ACTIONS),
        guardrail_purpose_policies={
            "summary": dict(SUMMARY_GUARDRAIL_OVERRIDES),
        },
        guardrail_custom_terms="",
        guardrail_custom_regex="",
        guardrail_replacement_text=GUARDRAIL_REPLACEMENT_TEXT,
        guardrail_retry_output_once=True,
    )
    return settings


def migrate_guardrail_policy(settings: dict[str, Any]) -> dict[str, Any]:
    """Apply the PG defaults once without overwriting later user choices."""

    try:
        version = int(settings.get("guardrail_policy_version", 0))
    except (TypeError, ValueError):
        version = 0
    if version >= GUARDRAIL_POLICY_VERSION:
        return settings

    current = settings.get("guardrail_default_policies")
    if not isinstance(current, dict) or current == LEGACY_GUARDRAIL_ACTIONS:
        settings["guardrail_default_policies"] = dict(PG_GUARDRAIL_ACTIONS)

    purpose_policies = settings.get("guardrail_purpose_policies")
    if not isinstance(purpose_policies, dict):
        purpose_policies = {}
    if "summary" not in purpose_policies:
        purpose_policies["summary"] = dict(SUMMARY_GUARDRAIL_OVERRIDES)
    settings["guardrail_purpose_policies"] = purpose_policies

    old_replacement = "Let us keep to matters of this world. What do you need?"
    replacement = settings.get("guardrail_replacement_text")
    if replacement is None or replacement == "" or replacement == old_replacement:
        settings["guardrail_replacement_text"] = GUARDRAIL_REPLACEMENT_TEXT
    settings["guardrail_retry_output_once"] = bool(
        settings.get("guardrail_retry_output_once", True)
    )
    settings["guardrail_policy_version"] = GUARDRAIL_POLICY_VERSION
    return settings
