# Role Weaver

**AI-assisted persistent character and campaign continuity for Neverwinter Nights: Enhanced Edition — for players and Dungeon Masters.**

Role Weaver watches the NWN client log, builds roleplay context, and helps generate character-consistent dialogue and emotes. It combines editable AI-assisted replies with persistent character memory, continuity, relationships, character development, NPC briefings, and DM campaign-management tools.

> **The human owns the character; Role Weaver helps preserve the story.**

## Download for Windows

Use the latest release on the Role Weaver GitHub Releases page. For most users, download **`RoleWeaver-Setup-v1.2.1.exe`**. A portable build, **`RoleWeaver-Portable-v1.2.1.zip`**, is also provided.

Python is not required for either packaged Windows build. Early unsigned releases may trigger Microsoft SmartScreen.

## First-time setup

1. Install Role Weaver or extract the entire portable ZIP.
2. Launch Role Weaver.
3. Choose **Google Gemini**, **OpenAI**, or **LM Studio**.
4. For Gemini or OpenAI, create your own API key using the instructions below and paste it into Role Weaver.
5. Press **Test AI Connection**.
6. Create or select a character profile.
7. Leave **World / Server** on **Auto Detect**. Role Weaver follows the normal NWN client log automatically; use **Browse...** only when you intentionally want to choose a different log file.
8. Role Weaver discovers a local world profile and log format when possible.
9. Press **Start**, enter NWN, and roleplay.

### Google Gemini API key

1. Open **Google AI Studio** and sign in.
2. Open the **API Keys** page.
3. Choose **Create API key** if you do not already have one.
4. Copy the newly created key.
5. In Role Weaver, select **Google Gemini** as the provider.
6. Paste the key into the API Key field.
7. Press **Test AI Connection**.

New Gemini keys created in AI Studio use Google's current authorization-key system. Never post or share the key.

Official Gemini setup: https://ai.google.dev/gemini-api/docs/get-started

### OpenAI API key

1. Sign in to the **OpenAI API Platform**.
2. Open the API-key area and create a new secret API key.
3. Copy the key when it is shown and store it securely.
4. Make sure your API account has billing/credits configured if required for the model you choose. ChatGPT subscriptions and API billing are separate.
5. In Role Weaver, select **OpenAI** as the provider.
6. Paste the key into the API Key field.
7. Select an available model and press **Test AI Connection**.

Official OpenAI quickstart: https://platform.openai.com/docs/quickstart

For more detail, including LM Studio, see **AI_PROVIDER_SETUP.md**.

## Highlights

### Players
- Character-consistent dialogue and emotes from recent NWN conversation.
- F8 multiple candidate replies and F9 editable, unsent paste into NWN.
- Persistent character memory, relationships, emotional continuity, knowledge and story threads.
- Learned voice based on IC dialogue actually sent through NWN.
- Correction learning and player-approved Character Development.
- Guidance for steering a scene without rewriting the character profile.
- Visible AI Context so you can inspect what roleplay material was supplied.

### Dungeon Masters
- Persistent NPC profiles and memories that can survive handoff between DMs.
- NPC Briefings covering current state, relationships, knowledge, commitments and recent continuity.
- Campaign Briefings for quickly returning to an ongoing campaign.
- Campaign Manager with description, current situation, storyline/story beats, objectives, important locations, player/party DM notes and session log.
- DM-only campaign notes kept out of character-generation context.
- Tracking of important information an NPC has previously shared with particular players.

## Main controls

| Control | Purpose |
| --- | --- |
| **F8** | Generate multiple candidate drafts in Role Weaver |
| **F9** | Generate a fresh reply and paste it into NWN without sending |
| **F10** | Toggle automatic reply/send mode |
| **F6** | Pause/resume listening |
| **F11** | Clear current conversation context |
| **F12** | Stop Role Weaver |

F9 deliberately leaves the final Enter to the player/DM so the reply can be reviewed and edited in NWN.

## Automatic world and log detection

Role Weaver v1.2.1 does not ship with a named persistent-world compatibility list. It discovers worlds from the NWN client logs already present on the user's computer and stores those profiles locally.

The parser also adapts to several NWN chat-log layouts. When both `[CHAT WINDOW TEXT]` and a structured copy of the same message are present, Role Weaver prefers the structured record to avoid duplicate conversation context. Use **Rescan Logs** to refresh locally discovered worlds. **Browse...** can point Role Weaver at a different NWN client log; if the log identifies a world, that world is then added to the list.

See **AUTOMATIC_LOG_DETECTION.md** for the automatic detection and adaptive-parser details.

## Documentation

- **FIRST_RUN.md** — first-run setup
- **AI_PROVIDER_SETUP.md** — Gemini, OpenAI and LM Studio setup
- **PLAYER_GUIDE.md** — player workflow
- **DM_GUIDE.md** — NPC continuity and campaign tools
- **CHARACTER_PROFILE_GUIDE.md** — character profiles
- **INSTALLATION.md** — source installation
- **BUILDING_WINDOWS.md** — Windows builds and releases

## Privacy and API keys

Role Weaver reads the NWN client log you configure. When using a hosted provider, relevant roleplay context is sent to that provider to generate a response. LM Studio can instead use a locally hosted model.

**Never commit, upload, screenshot, or send your Gemini/OpenAI API key to anyone.** Role Weaver does not ship with API keys. If a key is exposed, revoke it with the provider and create a new one.

## Feedback and support

Contact **roleweaverinfo@gmail.com** with questions, bug reports, testing results, or suggestions. GitHub Issues are also welcome.

## License and disclaimer

Role Weaver is released under the MIT License. It is an independent community project and is not affiliated with or endorsed by Beamdog, BioWare, Wizards of the Coast, OpenAI, Google, Nexus Mods, or the operators of persistent-world servers. Neverwinter Nights and related names and trademarks belong to their respective owners.
