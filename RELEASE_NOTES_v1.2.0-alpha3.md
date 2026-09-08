# Role Weaver v1.2.0-alpha3 — Manual Character Intelligence Management

This test build moves Character Intelligence from view-only continuity into direct player/DM management.

## Manual Character Knowledge Manager

The Character Memory tab now includes a dedicated knowledge table with **Add Knowledge**, **Edit Selected**, and **Delete Selected** controls. Double-clicking an entry also opens the editor.

Each knowledge record can contain:

- **Fact / knowledge** — the information the character knows or believes.
- **Privacy** — `PUBLIC`, `SHARED`, `CHARACTER`, `PRIVATE`, or `DM_ONLY`.
- **Confidence** — `Known`, `Believed`, `Uncertain`, or `Rumor`.
- **Source** — a short provenance note such as `conversation`, `manual`, `letter`, or `DM note`.

`DM_ONLY` remains a hard privacy boundary: those entries are visible to the DM/player in the manager but are never included in the character AI context.

## Manual edits take precedence

Knowledge entered or edited manually is marked authoritative. Automatic conversation summarization may continue adding IC facts, but it will not silently replace a manually maintained entry with an LLM-generated version of the same fact.

Older knowledge records without stable IDs are migrated automatically when the manager is opened. Existing memory files remain compatible.

## Supplied Player profile used during development

Development examples included a supplied Player profile demonstrating character-specific roleplay rules.

## Recommended testing

1. Let Role Weaver learn several facts automatically through IC conversation.
2. Open Character Memory and edit one fact's wording, privacy, and confidence.
3. Add a PRIVATE fact and a DM_ONLY fact manually.
4. Generate a reply and inspect AI Context: PRIVATE should be available to the character with secrecy guidance; DM_ONLY must not appear.
5. Run Summarize Now after more conversation and verify your manually edited entries remain intact.
6. Delete a fact and confirm it disappears from memory and subsequent AI context.

## Still planned

- Manual emotional-state editing and reset controls.
- More advanced semantic duplicate detection and contradiction handling.
- Campaign/DM knowledge transfer rules for multi-DM continuity.
- More granular privacy behavior beyond the current hard DM_ONLY exclusion.
