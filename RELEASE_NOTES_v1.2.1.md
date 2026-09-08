# Role Weaver v1.2.1 — Automatic Server & Log Detection

v1.2.1 removes the bundled persistent-world server list and replaces it with local automatic world discovery and adaptive NWN log parsing.

## What changed

- Removed named persistent-world selections from the distributed application.
- Added **Auto Detect** as the normal default.
- Added **Rescan Logs** to discover worlds from local NWN client logs.
- Browsing to a log now attempts to identify the world and add it to the local list automatically.
- Detected world profiles store their own log path and parser format locally.
- Added generic world-name detection from login/welcome text with area-root fallback.
- Added adaptive chat parsing for several NWN log layouts rather than selecting parser code by server name.
- Structured NWN chat is preferred when both structured and `[CHAT WINDOW TEXT]` copies are present, preventing duplicate context.
- Area tracking is now generic and recognizes multiple common NWN area-entry formats.
- Character, lore, campaign, roleplay-rule, and memory folders now accept dynamically discovered world IDs.
- Existing users can retain the currently selected legacy world profile during upgrade without shipping a legacy server catalog to new users.
- Removed named-server example folders from the new distribution; generic Player and NPC examples are included under `AUTO` and copied into newly detected world folders.

## Stable release

v1.2.1 is the stable distribution of Automatic Server & Log Detection. Testing confirmed the following release requirements:

1. existing v1.2 installations migrate without losing the selected world's data;
2. the server/world list populates from local NWN logs;
3. changing or browsing log files selects the correct local world profile;
4. Talk, Whisper, Party, Tell, Shout, and DM chat continue to parse correctly;
5. chat is not duplicated when NWN writes both display and structured records;
6. current-area tracking works on different log styles;
7. character profiles, lore, memory, campaigns, and DM tools remain isolated by detected world;
8. F8/F9/F10 behavior is unchanged.

Role Weaver remains server-neutral and makes no public compatibility claim for any named persistent world.
