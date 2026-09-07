# Role Weaver v1.2.0-alpha2 — Character Intelligence

This test build begins the Character Intelligence stage while retaining the identity and chat-parser fixes from alpha1.4.

## New Character Intelligence

- **Emotional continuity**: persistent character emotional state can be inferred from supported IC words/actions and carried into later replies.
- **Character knowledge**: Role Weaver now maintains a structured list of facts the active character has actually learned in character.
- **Knowledge privacy labels**: `public`, `shared`, `character`, `private`, and reserved `dm_only` are supported by the memory schema. The automatic summarizer never creates `dm_only` knowledge.
- **DM-only exclusion**: `dm_only` knowledge is never included in character AI context.
- **Cumulative knowledge**: older knowledge is preserved when a later summarization does not repeat it, allowing memory to grow over time.
- **Character Memory UI** now shows observed voice, current emotional state, structured character knowledge, and story threads.
- Existing v1.0/v1.1/v1.2 memory files migrate additively; old relationships, interaction history, voice, aliases, and story threads are preserved.

## Additional Example Profiles

Each server profile now includes additional generic examples:
- Mira Vale — Player
- Brother Aldren — NPC
- Nessa Quickstep — NPC

The Dragon's Neck also includes:
- Lora Thendry — Player, based on the supplied Lora profile.

## Important alpha limitations

- Emotional state and knowledge are LLM-maintained and should be treated as editable/test-stage continuity, not infallible truth.
- Knowledge deduplication is currently exact-text based; semantic consolidation can be improved later.
- `private` knowledge is supplied to the character with an explicit instruction not to reveal it casually. `dm_only` is excluded entirely.
- Full manual knowledge/privacy editing and campaign-level knowledge transfer are planned for a later stage.
