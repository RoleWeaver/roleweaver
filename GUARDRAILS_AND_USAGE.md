# Guardrails and AI usage

Role Weaver validates every generated dialogue request and result through its
client-side guardrail boundary. The default implementation uses Guardrails AI
and runs locally inside the client. It does not contact, depend on, or share
configuration or data with the separate Role Weaver server addon.

## Guardrails & Usage page

Open the **Guardrails & Usage** tab in the lower application panel to:

- confirm whether Guardrails AI is active and see its installed version;
- set maximum input and output sizes;
- review request, token and blocked-request totals for the current session,
  last 24 hours, 7 days or 30 days;
- switch the chart among Role Weaver requests, actual API calls, reported
  tokens and estimated cost; and
- enter provider pricing in USD per million input and output tokens.

The tab contains three pages:

- **Overview** shows status, request totals and request/token/cost charts.
- **Policy** controls each policy category for all requests or a specific
  purpose: replies, candidates, summaries, AFK, translations or connection
  tests.
- **Events** shows recent policy decisions without storing the text that caused
  them.

Saved guardrail limits take effect the next time **Start** is pressed. Pricing
changes affect future requests; existing usage records retain the estimate made
when each request occurred.

Cost is an estimate, not a billing statement. Role Weaver only calculates a
cost when both input and output token counts were reported by the provider and
both rates were configured by the user. Missing information is displayed as
unknown and is never silently treated as zero.

## Guardrail behavior

The client checks prompt size, invalid control characters, common attempts to
override the roleplay instructions, out-of-character model disclosures and
possible instruction or API-key leakage. It also detects common forms of
personal information, toxic language, direct harassment or threats, explicit
sexual content and graphic violence. The content detectors are deliberately
lightweight local rules rather than a remote moderation service; they avoid an
additional disclosure of RP text and can be extended with custom terms and
regular expressions. Custom policy fields accept up to 100 entries; terms are
limited to 100 characters and regular expressions to 256 characters. Unsafe
nested repetition is rejected.

Every category has one of four actions:

- **Off** ignores the category.
- **Warn** permits the text but records a policy event.
- **Block** stops the input or output.
- **Replace** redacts matching input material or substitutes the configured
  safe output reply.

Purpose-specific policies inherit the Default policy until overridden. The
shipped PG-oriented profile blocks malformed input, instruction overrides and
secret leakage. It replaces model disclosure, personal information, toxic
language, harassment, explicit sexual content, graphic violence and custom
matches. Summaries override the four mature-content categories to **Warn** so
existing RP can still be recorded accurately without changing the source text.
Policy changes apply to new requests immediately. Input and output size-limit
changes apply after the next **Start**.

**Restore Defaults** on the Policy page restores this complete shipped profile,
including character limits, the summary overrides, retry behavior and the safe
replacement. It also clears custom terms and expressions. Provider token-price
estimates and usage history are not changed.

These policies apply when Role Weaver sends input to the LLM and when it
receives generated output. They do not recheck text that the player manually
adds or edits afterward; the player retains control over what is finally posted
to the game.

When output retry is enabled, Role Weaver asks the configured provider for one
fresh response after a Block or Replace decision. The retry instruction names
only the policy category and never repeats the rejected response. If the retry
also fails, the configured Block or Replace action is applied. Both provider
calls are included in token and cost estimates.

A blocked input is not sent to the AI provider. A blocked output is not returned
for use as dialogue. Connection tests now use the same guarded execution and
usage-recording path as other AI requests.

If the Guardrails AI library cannot initialize, the page reports **DEGRADED**
and Role Weaver retains a small built-in safety fallback. Packaged releases and
supported source installations include Guardrails AI by default.

Response seeds are included in the guarded LLM input just like recent chat and
Guidance. A seed that triggers an input policy is handled before any provider
request is made.

The application depends on the `GuardrailBackend` protocol rather than directly
on Guardrails AI. Developers can replace the implementation without changing
providers, the conversation engine, usage storage or UI reporting.

## Stored usage data

Usage records are stored locally in `RoleWeaver_Data/usage.sqlite3` and retained
for 30 days. Records contain timestamps, provider and model names, request
purpose, success or failure, duration, reported token counts, guardrail action,
error type and an optional estimated cost.

Policy event rows contain only timestamp, request purpose, input/output
direction, category, action and backend. They contain no reason text or matched
content.

The usage database does **not** store prompts, response seeds, generated replies,
Tells, translations, character instructions or API keys. Deleting `usage.sqlite3`
clears the usage history; Role Weaver creates a new empty database when needed.

## Developer integration

New AI features should call `AIExecutionService.generate()` with an `AIRequest`
instead of invoking a provider directly. This preserves the common sequence:

```text
guard input -> provider request -> normalize result -> guard output -> record usage
```

Implement another backend against `roleweaver.guardrails.GuardrailBackend` and
return `GuardrailResult` values. Guardrail implementations must not persist
dialogue content in telemetry or include it in error messages.
