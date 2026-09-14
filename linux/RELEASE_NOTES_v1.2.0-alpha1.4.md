# Role Weaver v1.2.0-alpha1.4 — Chat Parser Hotfix

Fixes a regression introduced by the alpha1.3 identity detector. The identity detector accidentally redefined the global structured-chat regular expression with a reduced pattern that did not contain the `message` capture group. Normal chat parsing then raised `IndexError: no such group` and stopped the Activity/conversation feed.

## Fix
- Keeps the normal `STRUCTURED_CHAT_RE` exclusively for chat parsing.
- Uses a separate `IDENTITY_STRUCTURED_CHAT_RE` for active-character detection.
- Preserves the alpha1.3 character-profile mismatch detection behavior.
