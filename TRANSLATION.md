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

## Desktop workflow

The Windows and Linux clients now provide a resizable Translation window beside
Activity. **Translate Last 3** translates the newest incoming game-chat lines;
**Continuous Translation** processes new incoming lines as they arrive.

The **Language Settings** page selects the user's language, game language,
incoming auto-detection, and protected terminology. F8 candidates and F9 replies
are drafted in the user's language. A second editable editor contains the game-
language translation. **Generate in My Language**, **Shorter**, and **Longer**
use the current text in the first editor as their seed; if that editor is empty,
Generate starts from the recent scene. **Translate to Game Language** sends the
chosen/edited first draft to the second editor. **Refine in Game Language** uses
the current second editor text as its seed without regenerating from scratch.
**Translate to My Language** back-translates the second editor for review while
leaving its game-language text intact. F9 still creates and translates a new
reply in one step. Before pasting, the player reviews the second editor; edits
to the first editor require translating again. Ctrl+Z in either editor restores
the previous text after a generated or translated replacement. Each editor has
its own **Clear** button, which leaves the other editor intact; **Clear Both**
empties both drafts.

For older NWN logs, the game language also selects the character encoding used
when a line is not UTF-8. Spanish, German, French, Italian, and Dutch use
Windows-1252; Polish uses Windows-1250; Russian uses Windows-1251. Changes to
the game language apply to newly received lines during a running session.
Mixed legacy encodings in one log cannot always be distinguished reliably.
