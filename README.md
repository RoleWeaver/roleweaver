# Role Weaver

**Role Weaver is an AI-assisted roleplay client for Neverwinter Nights: Enhanced Edition, built for both players and Dungeon Masters.**

It watches the NWN client chat log, follows the conversation around your selected character, remembers useful continuity, retrieves relevant lore, and helps generate in-character dialogue that you can review and edit before it is sent.

**Players** can use Role Weaver to deepen the portrayal of their own characters: maintain a consistent voice, remember relationships and promises, keep track of long-running stories, and get several possible replies when inspiration runs dry.

**Dungeon Masters** can use the same tools to portray recurring NPCs, preserve characterization across sessions, maintain campaign lore, and give multiple DMs a common foundation for shared NPCs and storylines.

> **Role Weaver assists the person roleplaying the character; it does not replace them.** You remain responsible for what your character or NPC actually says and what becomes canon.

## Two ways to use Role Weaver

### For players

Role Weaver can act as a continuity and writing companion for your own NWN character.

It can help you:

- keep your character's personality and speaking style consistent;
- remember friendships, rivalries, suspicions, promises, and unresolved threads;
- retrieve relevant lore while you are in a scene;
- separate private Tell conversations from public RP context;
- filter explicit OOC chatter from AI generation context;
- generate several candidate replies and choose or edit the one that feels right;
- use persistent Guidance for temporary moods or scene direction;
- review old conversations when returning to a storyline after days or weeks.

A player might keep a profile such as:

```text
Characters\CUSTOM\character_Kaelen_Marr_Player_Character.txt
```

The profile describes who the character is. Role Weaver then combines that foundation with recent conversation, relationships, memory, and lore.

### For Dungeon Masters

For DMs, Role Weaver becomes a character-continuity tool for recurring NPCs and collaborative worlds.

It can help a DM team:

- keep an NPC recognizable across many sessions;
- let different DMs portray the same NPC from the same character profile;
- preserve relationships between an NPC and individual player characters;
- maintain focused campaign lore files;
- remember prior promises, conflicts, discoveries, and goals;
- inspect exactly what context the AI used;
- correct memory manually when campaign canon requires it;
- create richer ongoing characters without every DM memorizing every prior scene.

A DM might keep a shared profile such as:

```text
Characters\CUSTOM\character_Captain_Veyra_DM_NPC.txt
```

Shared character profiles and Lore files work well in a private campaign Git repository.

**Current limitation:** Role Weaver does not automatically synchronize live memory between several DMs. Profiles and lore are easy to share; runtime memory/history remains local unless the group deliberately shares and curates it.

## Core idea

Role Weaver is not simply a dialogue generator. Its purpose is **roleplay continuity**.

A good response should reflect:

1. who the character is;
2. what the character knows;
3. how the character feels about the people present;
4. what has happened before;
5. what is happening now;
6. any scene direction supplied by the human player or DM.

The human then chooses what to use.

## Quick start

1. Read [INSTALLATION.md](INSTALLATION.md).
2. Run `Install_RoleWeaver.bat` once, or install the Python requirements manually.
3. Launch Role Weaver with `RoleWeaver.bat`.
4. Select the server and the character you are currently portraying.
5. Configure OpenAI, Google Gemini, or LM Studio.
6. Confirm the NWN client log path.
7. Click **Start**.
8. Use **F8** for multiple candidate replies or **F9** for an editable draft placed directly into NWN.

## Included examples

The public package includes two deliberately generic examples in each server profile folder:

- **Captain Veyra — DM NPC Example:** demonstrates a recurring NPC that several DMs could portray consistently.
- **Kaelen Marr — Player Character Example:** demonstrates a personal player-character profile focused on voice, relationships, and long-term RP continuity.

Copy whichever example is closest to your use case and edit the copy.

## Documentation

- [INSTALLATION.md](INSTALLATION.md) — Windows/source installation and first-run setup.
- [PLAYER_GUIDE.md](PLAYER_GUIDE.md) — using Role Weaver with your own player character.
- [DM_GUIDE.md](DM_GUIDE.md) — recurring NPCs, lore, canon, and multi-DM workflows.
- [FEATURES.md](FEATURES.md) — complete feature overview.
- [PUBLIC_RELEASE_CHECKLIST.md](PUBLIC_RELEASE_CHECKLIST.md) — checklist for maintainers preparing a GitHub release.

## Privacy and control

Role Weaver stores conversation continuity, summaries, history, and character memory locally. API keys are not intentionally written to normal Role Weaver settings files.

Generated replies are suggestions. Review them before sending, particularly when another player's character, campaign canon, secrets, or sensitive story material is involved.

## Project status

This package is a **release candidate** intended for testing by both NWN players and DMs before broader distribution.

**Your character. Your world. Your story — remembered.**
