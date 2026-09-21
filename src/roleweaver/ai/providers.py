"""Built-in AI providers shared by the Windows and Linux clients."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

from openai import OpenAI

try:
    from google import genai
except Exception:  # pragma: no cover - exercised when the optional SDK is absent
    genai = None

from .contracts import AIRequest, AIRequestPurpose, AIResult, AIUsage

AI_PROVIDERS = {
    "LM Studio": {
        "requires_key": False,
        "default_model": "auto",
        "default_base_url": "http://127.0.0.1:1234",
        "env_key": "",
    },
    "OpenAI": {
        "requires_key": True,
        "default_model": "gpt-5.6-luna",
        "default_base_url": "",
        "env_key": "OPENAI_API_KEY",
    },
    "Google Gemini": {
        "requires_key": True,
        "default_model": "gemini-3.7-flash",
        "default_base_url": "",
        "env_key": "GEMINI_API_KEY",
    },
}


def normalize_lm_studio_base_url(url: str) -> str:
    """Accept either a server root or an OpenAI-compatible ``/v1`` URL."""

    normalized = (url or "http://127.0.0.1:1234").strip().rstrip("/")
    if not normalized.lower().endswith("/v1"):
        normalized += "/v1"
    return normalized


def _integer(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _openai_usage(response: Any) -> AIUsage:
    usage = getattr(response, "usage", None)
    if usage is None:
        return AIUsage()
    input_value = getattr(usage, "input_tokens", None)
    if input_value is None:
        input_value = getattr(usage, "prompt_tokens", None)
    output_value = getattr(usage, "output_tokens", None)
    if output_value is None:
        output_value = getattr(usage, "completion_tokens", None)
    input_tokens = _integer(input_value)
    output_tokens = _integer(output_value)
    total_tokens = _integer(getattr(usage, "total_tokens", None))
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    source = (
        "provider"
        if any(value is not None for value in (input_tokens, output_tokens, total_tokens))
        else "unavailable"
    )
    return AIUsage(input_tokens, output_tokens, total_tokens, source)


def _gemini_usage(response: Any) -> AIUsage:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return AIUsage()
    input_tokens = _integer(getattr(usage, "prompt_token_count", None))
    output_tokens = _integer(getattr(usage, "candidates_token_count", None))
    total_tokens = _integer(getattr(usage, "total_token_count", None))
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    source = (
        "provider"
        if any(value is not None for value in (input_tokens, output_tokens, total_tokens))
        else "unavailable"
    )
    return AIUsage(input_tokens, output_tokens, total_tokens, source)


class OpenAICompatibleProvider:
    provider_name = "OpenAI"

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        auto_model: bool = False,
        use_chat_completions: bool = False,
    ) -> None:
        kwargs = {"api_key": api_key or "lm-studio"}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = (model or "").strip()
        self.use_chat_completions = bool(use_chat_completions)
        if auto_model or not self.model or self.model.casefold() == "auto":
            models = self._list_model_ids()
            if not models:
                raise RuntimeError(
                    "Connected to the AI server, but no loaded models were reported. "
                    "In LM Studio, load a model and make sure the Local Server is running."
                )
            self.model = models[0]

    def _list_model_ids(self) -> list[str]:
        response = self.client.models.list()
        data = getattr(response, "data", None)
        if data is None:
            try:
                data = list(response)
            except (TypeError, AttributeError):
                data = []
        return [str(item.id) for item in data or [] if getattr(item, "id", None)]

    def generate(
        self,
        request: AIRequest | str,
        prompt: str | None = None,
        *,
        purpose: AIRequestPurpose = AIRequestPurpose.REPLY,
    ) -> AIResult:
        normalized = AIRequest.coerce(request, prompt, purpose=purpose)
        started = time.perf_counter()
        if self.use_chat_completions:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": normalized.instructions},
                    {"role": "user", "content": normalized.prompt},
                ],
            )
            choices = getattr(response, "choices", None) or []
            message = getattr(choices[0], "message", None) if choices else None
            text = (getattr(message, "content", "") or "").strip()
        else:
            response = self.client.responses.create(
                model=self.model,
                instructions=normalized.instructions,
                input=normalized.prompt,
            )
            text = (getattr(response, "output_text", "") or "").strip()
        return AIResult(
            text=text,
            provider=self.provider_name,
            model=self.model,
            purpose=normalized.purpose,
            usage=_openai_usage(response),
            duration_seconds=time.perf_counter() - started,
            provider_request_id=str(getattr(response, "id", "") or ""),
        )

    def test(self) -> str:
        models = self._list_model_ids()
        if models:
            return f"Connected. {len(models)} model(s) available. Using {self.model}."
        if self.model and self.model.casefold() != "auto" and self.use_chat_completions:
            result = self.generate(
                AIRequest(
                    instructions="",
                    prompt="Reply with exactly: OK",
                    purpose=AIRequestPurpose.CONNECTION_TEST,
                )
            )
            if result.text:
                return f"Connected. Using {self.model}."
        raise RuntimeError(
            "The server responded, but no models were available. "
            "Load a model in LM Studio and start the Local Server."
        )


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio provider with native REST model discovery/loading."""

    provider_name = "LM Studio"

    def __init__(self, model: str, base_url: str) -> None:
        self.server_root = (base_url or "http://127.0.0.1:1234").strip().rstrip("/")
        if self.server_root.lower().endswith("/v1"):
            self.server_root = self.server_root[:-3].rstrip("/")
        selected_model = self._prepare_model((model or "auto").strip())
        super().__init__(
            model=selected_model,
            api_key="lm-studio",
            base_url=normalize_lm_studio_base_url(self.server_root),
            use_chat_completions=True,
        )

    def _native_request(
        self, method: str, path: str, body: dict[str, Any] | None = None, timeout: int = 120
    ) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            self.server_root + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LM Studio API returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not connect to LM Studio at {self.server_root}. "
                "Make sure the Local Server is running."
            ) from exc

    def _prepare_model(self, requested_model: str) -> str:
        try:
            payload = self._native_request("GET", "/api/v1/models", timeout=15)
            models = payload.get("models") or []
        except Exception as exc:
            temp = OpenAI(
                api_key="lm-studio",
                base_url=normalize_lm_studio_base_url(self.server_root),
            )
            response = temp.models.list()
            data = getattr(response, "data", None) or []
            ids = [str(getattr(item, "id", "")) for item in data if getattr(item, "id", None)]
            if requested_model.casefold() == "auto":
                if not ids:
                    raise RuntimeError(
                        "No LM Studio models are available. Download and load a "
                        "model in LM Studio first."
                    ) from exc
                return ids[0]
            return requested_model
        llms = [model for model in models if (model.get("type") or "").casefold() == "llm"]
        if not llms:
            raise RuntimeError(
                "LM Studio is running, but no downloaded LLMs were found. "
                "Download a chat/instruct model in LM Studio first."
            )
        selected = None
        if requested_model.casefold() == "auto":
            selected = next((model for model in llms if model.get("loaded_instances")), llms[0])
        else:
            wanted = requested_model.casefold()
            for model in llms:
                candidates = {
                    str(model.get("key") or "").casefold(),
                    str(model.get("display_name") or "").casefold(),
                    str(model.get("name") or "").casefold(),
                }
                if wanted in candidates:
                    selected = model
                    break
            if selected is None:
                return requested_model
        model_key = str(selected.get("key") or selected.get("name") or "").strip()
        if not model_key:
            raise RuntimeError("LM Studio returned a model without a usable model identifier.")
        if not (selected.get("loaded_instances") or []):
            print(f"[LM STUDIO] Loading model: {model_key} ...")
            result = self._native_request(
                "POST", "/api/v1/models/load", body={"model": model_key}, timeout=180
            )
            if (result.get("status") or "").casefold() != "loaded":
                raise RuntimeError(
                    f"LM Studio did not confirm that model '{model_key}' was loaded."
                )
            print(f"[LM STUDIO] Model loaded: {model_key}")
        else:
            print(f"[LM STUDIO] Model already loaded: {model_key}")
        return model_key

    def test(self) -> str:
        result = self.generate(
            AIRequest(
                instructions="",
                prompt="Reply with exactly: OK",
                purpose=AIRequestPurpose.CONNECTION_TEST,
            )
        )
        if not result.text:
            raise RuntimeError("LM Studio connected, but the model returned no test response.")
        return f"Connected. Model loaded and responding: {self.model}."


class GeminiProvider:
    provider_name = "Google Gemini"
    FALLBACK_MODELS = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]

    def __init__(self, model: str, api_key: str) -> None:
        if genai is None:
            raise RuntimeError(
                "Google Gemini support is not installed. "
                "Run the launcher again to install dependencies."
            )
        if not api_key:
            raise RuntimeError("A Google Gemini API key is required.")
        self.client = genai.Client(api_key=api_key)
        self.model = (model or "gemini-3.7-flash").strip()
        self.last_successful_model: str | None = None

    def _candidate_models(self) -> list[str]:
        requested = self.model.strip()
        ordered = (
            list(self.FALLBACK_MODELS)
            if requested.casefold() in ("auto", "auto-free", "free-auto")
            else [requested] + self.FALLBACK_MODELS
        )
        result = []
        seen = set()
        for name in ordered:
            key = name.casefold()
            if name and key not in seen:
                seen.add(key)
                result.append(name)
        if self.last_successful_model in result:
            result.remove(self.last_successful_model)
            result.insert(0, self.last_successful_model)
        return result

    @staticmethod
    def _error_code(exc: Exception) -> int | None:
        for attr in ("status_code", "code"):
            value = getattr(exc, attr, None)
            try:
                value = value() if callable(value) else value
            except Exception:
                value = None
            if isinstance(value, int):
                return value
            if value is not None:
                match = re.search(r"\b(400|403|404|408|409|429|500|502|503|504)\b", str(value))
                if match:
                    return int(match.group(1))
        match = re.search(r"\b(400|403|404|408|409|429|500|502|503|504)\b", str(exc))
        return int(match.group(1)) if match else None

    @classmethod
    def _should_try_another_model(cls, exc: Exception) -> bool:
        code = cls._error_code(exc)
        text = str(exc).casefold()
        if code in (408, 429, 500, 502, 503, 504):
            return True
        if any(
            term in text
            for term in (
                "resource_exhausted",
                "resource exhausted",
                "unavailable",
                "overloaded",
                "busy",
                "capacity",
                "rate limit",
                "rate_limit",
                "too many requests",
                "temporarily unavailable",
            )
        ):
            return True
        access_terms = (
            "model not found",
            "not found for api version",
            "not supported for generatecontent",
            "does not have access",
            "permission denied",
            "not available for",
        )
        return code in (400, 403, 404) and any(term in text for term in access_terms)

    def _generate_with_fallback(self, contents: str) -> tuple[Any, str]:
        candidates = self._candidate_models()
        failures = []
        for index, model_name in enumerate(candidates):
            try:
                if len(candidates) > 1:
                    print(f"[GEMINI] Trying {model_name}...")
                response = self.client.models.generate_content(model=model_name, contents=contents)
                self.last_successful_model = model_name
                self.model = model_name
                if index > 0:
                    print(f"[GEMINI] Switched to available model: {model_name}")
                return response, model_name
            except Exception as exc:
                failures.append(f"{model_name}: {exc}")
                if not self._should_try_another_model(exc):
                    raise
                if index < len(candidates) - 1:
                    print(f"[GEMINI] {model_name} unavailable/busy. Trying another Gemini model...")
        detail = "\n".join(failures[-3:])
        raise RuntimeError(
            "No Gemini fallback model was available for this request. "
            "The project may be rate-limited, all candidate models may be busy, "
            "or the free-tier quota may be exhausted.\n" + detail
        )

    def generate(
        self,
        request: AIRequest | str,
        prompt: str | None = None,
        *,
        purpose: AIRequestPurpose = AIRequestPurpose.REPLY,
    ) -> AIResult:
        normalized = AIRequest.coerce(request, prompt, purpose=purpose)
        started = time.perf_counter()
        response, model_name = self._generate_with_fallback(
            normalized.instructions + "\n\n" + normalized.prompt
        )
        return AIResult(
            text=(getattr(response, "text", "") or "").strip(),
            provider=self.provider_name,
            model=model_name,
            purpose=normalized.purpose,
            usage=_gemini_usage(response),
            duration_seconds=time.perf_counter() - started,
            provider_request_id=str(getattr(response, "response_id", "") or ""),
        )

    def test(self) -> str:
        result = self.generate(
            AIRequest(
                instructions="",
                prompt="Reply with exactly: OK",
                purpose=AIRequestPurpose.CONNECTION_TEST,
            )
        )
        if not result.text:
            raise RuntimeError("Gemini connected, but returned no text.")
        return f"Connected to Gemini. Working model: {self.model}."


def create_ai_provider(settings: dict[str, Any], api_key: str = ""):
    provider = settings.get("ai_provider", "OpenAI")
    model = str(settings.get("model", "")).strip()
    if provider == "LM Studio":
        base_url = settings.get("lm_studio_base_url", "http://127.0.0.1:1234")
        settings["lm_studio_base_url"] = normalize_lm_studio_base_url(base_url)
        return LMStudioProvider(model=model, base_url=base_url)
    if provider == "Google Gemini":
        return GeminiProvider(model=model, api_key=api_key)
    if provider == "OpenAI":
        return OpenAICompatibleProvider(model=model, api_key=api_key)
    raise RuntimeError(f"Unknown AI provider: {provider}")
