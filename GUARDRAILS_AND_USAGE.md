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
- switch the chart among requests, reported tokens and estimated cost; and
- enter provider pricing in USD per million input and output tokens.

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
possible instruction or API-key leakage. A blocked input is not sent to the AI
provider. A blocked output is not returned for use as dialogue.

If the Guardrails AI library cannot initialize, the page reports **DEGRADED**
and Role Weaver retains a small built-in safety fallback. Packaged releases and
supported source installations include Guardrails AI by default.

The application depends on the `GuardrailBackend` protocol rather than directly
on Guardrails AI. Developers can replace the implementation without changing
providers, the conversation engine, usage storage or UI reporting.

## Stored usage data

Usage records are stored locally in `RoleWeaver_Data/usage.sqlite3` and retained
for 30 days. Records contain timestamps, provider and model names, request
purpose, success or failure, duration, reported token counts, guardrail action,
error type and an optional estimated cost.

The usage database does **not** store prompts, generated replies, Tells,
translations, character instructions or API keys. Deleting `usage.sqlite3`
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
