# Translation service

Role Weaver's shared translation foundation lives in
`src/roleweaver/translation/`. It has no Tkinter, operating-system input or game
log dependencies, so the Windows and Linux clients use the same contracts.

`TranslationService` accepts batches of `TranslationMessage` values with stable
IDs, source and target languages, an incoming/outgoing direction and optional
protected terminology. It sends one `AIRequestPurpose.TRANSLATION` request
through `AIExecutionService`. Translation therefore uses the configured
guardrail backend and appears under Translation in the existing request, token
and estimated-cost reports.

```python
from roleweaver.translation import (
    TranslationDirection,
    TranslationMessage,
    TranslationRequest,
    TranslationService,
)

service = TranslationService(ai_execution)
result = service.translate(
    TranslationRequest(
        source_language="English",
        target_language="German",
        direction=TranslationDirection.INCOMING,
        messages=(
            TranslationMessage(
                id="chat-42",
                speaker="Elara",
                channel="Talk",
                text="Welcome to Waterdeep.",
            ),
        ),
        protected_terms=("Waterdeep",),
    )
)

print(result.message("chat-42").translated_text)
print(result.provider, result.model, result.usage.total_tokens)
```

## Contract guarantees

- Up to 50 messages may be translated in one provider call.
- Result IDs must exactly match the request IDs. Missing, duplicate and unknown
  IDs reject the whole result rather than associating text with the wrong
  speaker.
- Speaker and channel metadata never need to be reconstructed by the model.
- Auto-detection is reported per message, so one batch can safely contain more
  than one source language. The batch-level detected language is set only when
  every message agrees.
- Protected terms are replaced with opaque tokens before the provider call.
  The response is accepted only when every token returns in the correct message
  the correct number of times, after which the original term is restored.
- Same-language requests are returned unchanged without a provider call or
  usage charge.
- Provider responses must contain strict structured JSON. Markdown fences are
  tolerated, but incomplete or explanatory output is rejected.
- Prompts and translations are not written to usage telemetry.

## Privacy and provider boundary

The original message text is sent to the AI provider selected by the user so it
can be translated. OpenAI and Google Gemini are hosted services; LM Studio can
keep provider processing on the user's own machine. The service itself does not
persist source text or translations. Its exceptions omit provider output and
source text, and the existing usage database records only content-free request
metadata.

The current layer provides service contracts only. The incoming Translation
window, continuous/manual batching, Language Settings page and dual outgoing
draft editors will be connected in subsequent stages.
