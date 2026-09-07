# Role Weaver v1.2.0-alpha1 — DM Foundation

This is the first staged test build toward Role Weaver v1.2. It is intended for testing before the v1.2 feature set is merged into the stable release.

## Stage 1 additions

- **Profile Type is now explicitly selectable** as `Player` or `NPC` in the Character Editor.
- **DM Cast Manager** tab lists NPC profiles for the current server.
- NPCs can be selected, inspected, loaded, and opened in the Character Editor from the Cast Manager.
- The Cast Manager shows basic continuity information including remembered relationships, open story threads, and recent summary data when available.
- **Shared Campaign Memory** provides campaign-level continuity that may be included in character AI context.
- **DM-only Campaign Notes** are stored alongside campaign data but are deliberately excluded from character AI prompts.
- **Campaign Pack export/import** allows DMs to exchange campaign memory, NPC profiles, character-specific AI settings, and NPC continuity data without requiring a Role Weaver cloud service.

## Data model

Campaign data is stored under:

`Campaigns/<server>/<campaign>/campaign_memory.json`

NPC character memory remains under the normal Role Weaver character-memory structure so the existing v1.1 memory system stays compatible.

## Important alpha notes

- Campaign Pack import replaces files with matching names. This alpha build does not automatically create backups before import.
- Review imported DM/campaign data before using it during live play.
- Shared Campaign Memory is considered character-readable context. Do not place DM-only secrets there. Put secrets that characters must not know in **DM-only Notes**.
- More granular per-character/shared/private knowledge permissions are planned for the Character Knowledge stage.

## Testing priorities

Please especially test:

1. Creating both Player and NPC profiles.
2. Whether only NPC profiles appear in the DM Cast Manager.
3. Switching among several NPCs from the Cast Manager.
4. Whether each NPC retains its own memory/relationships/learned voice.
5. Whether Shared Campaign Memory appears appropriately in generated AI context.
6. Confirming DM-only Notes never appear in AI Context.
7. Exporting a Campaign Pack and importing it into another test copy of Role Weaver.

The stable v1.1 memory system remains the baseline for comparison.
