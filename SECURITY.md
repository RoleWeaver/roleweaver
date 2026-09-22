# Security Policy

## Reporting a security issue

Please do not publish API keys, private logs, character secrets, or other sensitive data in a public issue.

For ordinary bugs, use the GitHub issue tracker and remove sensitive information from screenshots and logs before posting.

If you believe you found a security vulnerability, open a GitHub issue containing only enough non-sensitive information to identify it as a security report and request a private contact channel.

## API keys

Role Weaver does not require API keys to be committed to the repository. Never place an OpenAI or Gemini API key in a character profile, lore file, issue, pull request, or source commit.

## Local data

Role Weaver can store character memory, conversation history, lore, profiles, and settings locally. Users are responsible for reviewing these files before sharing a Role Weaver data directory publicly.

AI usage metadata is retained locally for 30 days in
`RoleWeaver_Data/usage.sqlite3`. It contains provider/model names, request
purpose, timing, reported token counts, guardrail outcomes, error types and
optional cost estimates. It does not contain prompt text, generated replies,
Tells, translations, character instructions or API keys.

Guardrail event history uses the same database and retention period. It stores
only time, request purpose, input/output direction, policy category, selected
action and backend. Matched text and detailed failure reasons are not stored.
