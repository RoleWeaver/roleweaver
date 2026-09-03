# Role Weaver

**AI-assisted roleplay for Neverwinter Nights: Enhanced Edition — for players and Dungeon Masters.**

Role Weaver watches the Neverwinter Nights client log, builds roleplay context, and helps generate character-consistent dialogue and emotes. It is designed around one principle:

> **The human owns the character; Role Weaver helps preserve the story.**

You decide what your character or NPC says. Role Weaver provides memory, context, lore, and editable drafts to make long-running roleplay easier to maintain.

## Download for Windows

Go to the repository's **Releases** page:

https://github.com/RoleWeaver/roleweaver/releases

For most users, download:

**`RoleWeaver-Setup-v1.0.0.exe`**

The installer contains the application and its Python dependencies. Python is **not** required on the user's computer.

A portable build is also available:

**`RoleWeaver-Portable-v1.0.0.zip`**

Extract the entire portable folder before running `RoleWeaver.exe`.

> Early unsigned Windows releases may trigger Microsoft SmartScreen. Code signing is planned as the project matures.

## What Role Weaver does

### For players
- Generates in-character dialogue and short emotes from recent NWN conversation.
- Maintains a character profile covering personality, speaking style, background, beliefs, relationships, goals, secrets, and roleplay rules.
- Provides multiple candidate replies with **F8**.
- Generates and pastes an editable, unsent reply into NWN with **F9**.
- Supports persistent Guidance so you can steer the current scene without changing the character profile.
- Tracks durable memories and relationships across sessions.

### For Dungeon Masters
- Uses the same character system for NPCs.
- Helps keep recurring NPC voices, motivations, knowledge, and relationships consistent.
- Supports server-specific lore and response rules.
- Makes it practical to maintain many conversational NPCs without surrendering DM control.

### Context and continuity
- Persistent character memory.
- Rolling session summaries.
- Relationship/attitude records.
- Separate private Tell context.
- IC/OOC filtering.
- Manual context controls.
- Conversation history.
- AI Context inspection so you can see what roleplay material was supplied for a reply.

### AI providers
Role Weaver currently supports:
- **Google Gemini**
- **OpenAI**
- **LM Studio** for local/offline-capable models

API keys are not included with Role Weaver. Hosted providers may charge for API usage according to their own pricing.

## Supported server profiles

Role Weaver includes profiles for:
- Custom / Other NWN Server
- The Dragon's Neck
- Arelith
- Ravenloft: Prisoners of the Mist
- Cormyr and the Dalelands
- Star Wars: Legends of the Old Republic
- Haze: Saltborne

The parser is built around standard NWN client-log chat, so additional servers can be added.

Server profiles scope character files, lore, and response rules independently.

## Quick start

1. Install Role Weaver.
2. Launch it.
3. Select **Google Gemini**, **OpenAI**, or **LM Studio**.
4. Enter an API key when the selected hosted provider requires one.
5. Press **Test AI Connection**.
6. Create or select a character profile.
7. Select the appropriate NWN server profile.
8. Confirm the NWN client-log path.
9. Press **Start**.
10. Enter Neverwinter Nights and roleplay.

Detailed setup: [`FIRST_RUN.md`](FIRST_RUN.md)

AI setup: [`AI_PROVIDER_SETUP.md`](AI_PROVIDER_SETUP.md)

Player guide: [`PLAYER_GUIDE.md`](PLAYER_GUIDE.md)

DM guide: [`DM_GUIDE.md`](DM_GUIDE.md)

## Main controls

| Control | Purpose |
| --- | --- |
| **F8** | Generate multiple candidate drafts in Role Weaver |
| **F9** | Generate a fresh reply and paste it into NWN without sending |
| **F10** | Toggle automatic reply/send mode |
| **F6** | Pause/resume listening |
| **F11** | Clear current conversation context |
| **F12** | Stop Role Weaver |

For F9, wait for generation to finish, then click/focus NWN during the two-second countdown. Role Weaver opens the NWN chat entry and pastes the reply, but deliberately leaves the final Enter to you.

## Character, lore, and server rules

Character profiles are stored under:

```text
Characters/<server>/
```

Server lore is stored under:

```text
Lore/<server>/
```

Response rules are stored under:

```text
RoleplayRules/<server>/roleplay_rules.txt
```

Role Weaver includes built-in editors for character profiles and lore.

Runtime memory and conversation history are kept out of source control.

## Privacy

Role Weaver reads the NWN client log you configure and can send selected roleplay context to the AI provider you choose.

If you use a hosted AI provider, relevant prompt/context data is transmitted to that provider to generate the response. Review that provider's privacy and data policies before using it with sensitive roleplay.

LM Studio can be used with locally hosted models.

Never commit or post API keys, private Tells, personal logs, or private character data.

## Building from source

See [`INSTALLATION.md`](INSTALLATION.md) for Python/source installation.

See [`BUILDING_WINDOWS.md`](BUILDING_WINDOWS.md) for the PyInstaller + Inno Setup Windows build and GitHub Actions release process.

## Contributing and support

Bug reports and feature requests are welcome:

https://github.com/RoleWeaver/roleweaver/issues

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting code and [`SECURITY.md`](SECURITY.md) before reporting sensitive problems.

## License

Role Weaver is released under the [MIT License](LICENSE).

## Disclaimer

Role Weaver is an independent community project. It is not affiliated with or endorsed by Beamdog, BioWare, Wizards of the Coast, OpenAI, Google, or the operators of any supported persistent-world server.

Neverwinter Nights and related names and trademarks belong to their respective owners.

AI-generated content can be inaccurate. Players and Dungeon Masters remain responsible for reviewing and sending roleplay generated with Role Weaver.
