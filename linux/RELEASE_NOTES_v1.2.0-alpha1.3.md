# Role Weaver v1.2.0-alpha1.3 — Identity Detector Hotfix

This hotfix corrects active-character detection introduced in alpha1.2.

## Fixed

- `Messages for:` is now correctly treated as an NWN log timestamp/session header, not a character name.
- Date/time strings are explicitly rejected as character identities.
- On servers that expose the local player/account join, Role Weaver maps that account to the character name through structured chat lines.
- On servers without a usable join line, Role Weaver uses a conservative speaker-dominance fallback and returns `unknown` instead of guessing when evidence is ambiguous.
- Player-profile mismatch warnings therefore appear only when Role Weaver has credible evidence of the active character.

NPC profiles remain exempt from Player-profile mismatch warnings.
