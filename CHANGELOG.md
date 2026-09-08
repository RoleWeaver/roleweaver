## v1.2.1 — Automatic Server & Log Detection

- Removed the bundled named persistent-world server list from new distributions.
- Added local automatic world discovery from NWN client logs and a **Rescan Logs** control.
- Added adaptive chat-log format detection with structured-record preference to avoid duplicate context.
- Added generic area-entry recognition and dynamic world-scoped Characters, Lore, Campaigns, RoleplayRules, and memory folders.
- Preserved the currently selected legacy world profile during upgrade without shipping a legacy server catalog.
- Replaced named-server example folders with generic `AUTO` examples.

## v1.2.0-alpha6.1 — Campaign Manager
- Added campaign description and Current Situation fields.
- Added ordered Story Beats with status and completion tracking.
- Added Objectives, Locations, Player/Party DM Notes, and Session Log.
- Added direct NPC Briefing access from the campaign roster.
- Expanded Campaign Briefing to summarize campaign-management data.
- Expanded the synthetic DM Continuity Demo campaign for testing.

## v1.2.0-alpha6 — DM Continuity

- Added NPC Briefing and Campaign Briefing.
- Added character-owned shared-with-player disclosure memory.
- Added a synthetic DM Continuity Demo campaign and NPC memories for testing.
- No DM writes to Player Knowledge and no NPC-to-NPC knowledge transfer.

# Changelog

## v1.2.0-alpha5.1 — Relationship Entity Validation
- Prevented descriptive knowledge/continuity phrases from becoming relationship characters.
- Added post-LLM relationship entity validation.
- Added manual Delete Character control to Relationships.

## v1.2.0-alpha5 — Adaptive Characters
- Added correction learning from edited-and-sent AI drafts.
- Added player-reviewed Character Development proposals and approval/rejection workflow.
- Added Adaptive tab and persistent approved development.


- Added continuity events, story-thread management, promises/commitments, manual CRUD, and relevance-ranked continuity retrieval.

## v1.2.0-alpha3.1 — Resizable Character Memory

- Character Memory now uses a draggable vertical divider between the Character Intelligence overview and Manual Character Knowledge Management.
- Resize the divider to give either section more screen space.
- Both panes resize proportionally when the main Role Weaver window changes size.
- Preserves alpha3 manual knowledge management and the tested identity/chat-parser fixes.

# Changelog

## v1.2.0-alpha3 — Manual Character Intelligence Management

- Added a manual Character Knowledge Manager to the Character Memory tab.
- Added Add, Edit, and Delete controls for persistent IC knowledge.
- Knowledge entries can be manually classified as PUBLIC, SHARED, CHARACTER, PRIVATE, or DM_ONLY.
- Knowledge confidence can be set to Known, Believed, Uncertain, or Rumor.
- Added an editable source field for manually maintained facts.
- Added stable knowledge IDs so existing facts can be safely edited without relying on list position.
- Legacy string knowledge entries are migrated into structured records automatically.
- Manual entries are authoritative and are protected from being silently overwritten by automatic summarization.
- DM_ONLY entries remain excluded from character AI context.
- Included a supplied Player profile example using the provided character description and RP rules.
- Preserved the tested alpha1.4 identity/chat fixes and alpha2 Character Intelligence behavior.

## v1.2.0-alpha2 — Character Intelligence

- Added persistent emotional-state continuity for the active character.
- Added structured character knowledge learned from IC context.
- Added privacy labels and hard exclusion of DM-only knowledge from character AI context.
- Added Character Memory display for emotional state and knowledge.
- Added generic Player and NPC examples to server profile folders.
- Added a supplied Player profile example based on the provided character profile.
- Preserved the alpha1.4 identity and chat-parser hotfixes.

## 1.2.0-alpha1.3

- Fixed active NWN character detection: `Messages for:` is a timestamp/session header, not a character name.
- Added date/time rejection, account-to-character resolution, and a conservative fallback for servers without local join information.

## 1.2.0-alpha1.2

- Added Player-profile mismatch detection against current NWN logs.
- Added immediate identity checks when selecting a Player profile and when starting Role Weaver.
- Added explicit logging when active-character detection is unavailable.

All notable public changes to Role Weaver are documented here.

## 1.2.0-alpha1.1

- Added multi-campaign create/load/rename/delete management.
- Added campaign-specific NPC membership without duplicating NPC profiles.
- Added character canonical identity/alias handling and conservative title resolution.
- Added manual alias and character-memory merge controls.
- Routed memory summarizer output through identity resolution to prevent titled duplicate records.
- Added Player-profile versus NWN-session mismatch detection with Switch / Keep / Cancel behavior.
- NPC profiles intentionally bypass Player mismatch warnings for DM portrayal workflows.

## v1.2.0-alpha1 — DM Foundation

- Added explicit **Player / NPC** profile type selection in the Character Editor.
- Added the first **NPC Cast Manager** for DMs.
- Added shared Campaign Memory and separate DM-only campaign notes.
- Added Campaign Pack export/import for sharing NPC profiles and continuity between DMs.
- Shared Campaign Memory is included in character context; DM-only notes are never sent to the character AI.
- Preserves the v1.1 learned-voice, interaction-history, relationship, and story-thread systems.

## 1.1.0 — Adaptive character memory

### Guidance
- Fixed F8 candidate generation clearing Guidance after the first use.
- Guidance now remains active across F8, F9, and draft revisions until the player explicitly clears or replaces it.
- Updated the GUI and console wording to match persistent Guidance behavior.

### Character voice learning
- Role Weaver now learns speaking style only from IC lines that the player character actually sends into the NWN log.
- Manually written dialogue and player-edited AI drafts therefore teach the same learned voice system.
- Learned voice tracks recurring vocabulary, sentence patterns, emote style, emotional expression, and patterns the character usually avoids.
- The explicit character profile remains authoritative and always takes precedence over learned observations.
- Added a Character Memory tab to inspect or reset the learned voice.
- Added **Summarize Now** to force a memory update before the normal message interval.

### Continuity and interaction memory
- Added structured per-character interaction histories with timestamps, importance, topics, unresolved details, and private-Tell flags.
- Role Weaver keeps a mix of recent and high-importance interactions available when a character returns.
- Added ongoing story-thread tracking for promises, investigations, debts, conflicts, goals, and unresolved matters.
- Relationship records preserve their structured history even if editable notes are blank.
- The Relationships tab now displays recent automatic interaction history.
- Raw conversation history continues to be retained separately on disk.
- OOC lines remain in History but no longer teach IC character memory or speaking style.
- Private Tell material is excluded from the public rolling summary and can be marked private in structured memory.

### Packaging
- Updated package version to 1.1.0.
- Windows release workflow now reads the version from `VERSION` so future release filenames do not need to be hard-coded.

## 1.0.0 — Initial public release

### Roleplay
- AI-assisted Neverwinter Nights: Enhanced Edition roleplay for players and Dungeon Masters.
- Character profiles with personality, speaking style, background, beliefs, relationships, goals, secrets, and roleplay rules.
- Persistent player Guidance for steering replies without exposing that guidance in-character.
- Multiple AI draft candidates and editable drafts.
- F9 workflow that generates and pastes an unsent reply into NWN for review.
- Automatic reply mode for users who explicitly enable it.

### Memory and context
- Persistent character memory and rolling session summaries.
- Relationship and attitude records for characters encountered during play.
- Separate private Tell conversation context.
- IC/OOC filtering.
- Manual context controls for ignoring, remembering, and forgetting conversation material.
- Conversation history viewer.
- AI Context view showing the roleplay material used for generation.

### World support
- World-specific character profiles.
- World-specific lore folders and lore editor.
- World-specific response rules.
- Earlier development builds included several named persistent-world profiles. v1.2.1 removes all named world profiles in favor of local automatic detection.

### AI providers
- Google Gemini.
- OpenAI.
- LM Studio for local models.
- Provider-aware default model switching.
- Gemini fallback behavior when an eligible model is unavailable.

### Windows distribution
- Self-contained Windows executable built with PyInstaller.
- Standard Windows installer built with Inno Setup.
- Portable Windows ZIP.
- Automated GitHub Actions build and release workflow.

### Recent reliability fixes
- Improved NWN foreground/focus handling for F9/manual draft paste.
- Scan-code keyboard injection is the default for NWN.
- Manual drafts remain on the clipboard as a fallback.
- Relationship tab populates encountered characters immediately.
- Fixed relationship-memory saving.
- Fixed first provider-switch model synchronization.
