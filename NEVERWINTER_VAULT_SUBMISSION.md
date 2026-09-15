# Neverwinter Vault Submission — Role Weaver v1.2.3

## Suggested title

**Role Weaver — Character and Campaign Continuity for NWN & NWN2**

## Short description

Free, open-source roleplay companion for all NWN and NWN2 editions, for players
and Dungeon Masters on Windows and Linux. Persistent character/NPC memory,
relationships, campaign continuity, editable AI drafts, AFK emotes and recovery
protection.

## Full description

**Role Weaver supports all editions of Neverwinter Nights and Neverwinter Nights 2:**
Original NWN, Diamond, NWN:EE, NWN2, NWN2 EE (including 64-bit client logs), and
NWN2 with Client Extender.

It follows the player's local client chat log to maintain character knowledge,
memories, relationships, conversation history, story threads, commitments,
speaking style and approved character development. Players can generate multiple
context-aware dialogue suggestions, review or edit them, and decide what to send.

Dungeon Masters can maintain persistent NPCs, prepare NPC briefings, and manage
campaign story beats, objectives, locations, session logs and shared continuity.

### New in version 1.2.3

- **Game Version selection** with remembered server/log settings for each edition.
- **NWN2 chat parsing**, including mixed layouts and private-message direction.
- **NWN2 EE log discovery**, including Temp/NWN2 EE and nwn2client64Log*.txt.
- **F10 AFK mode:** an initial character emote, then attention checks every
  30 seconds with a three-minute minimum interval between follow-up emotes.
- **Backup and crash protection:** rotating backups, atomic saves and recovery.
- **Unfinished-edit recovery** for Guidance, Character, Lore and AI Draft text,
  with Copy text, Discard and Clear all controls that remain visible when resizing.
- **Pending AI summary recovery** after an interruption.
- Quieter routine backups, improved Auto log selection and clean Exit controls.

### Other features

- Character/NPC memory and relationship tracking.
- Character Knowledge with privacy/confidence controls.
- Story threads, commitments and player-approved development.
- Learned speaking style and correction learning.
- Multiple editable AI candidates, persistent guidance and AI Context inspection.
- OOC filtering, NPC Briefings and Campaign Manager.
- Generic Player/NPC examples and local world discovery.
- Google Gemini, OpenAI, and local models through LM Studio.

### Installation and downloads

**Windows:** download **RoleWeaver-NeverwinterVault-v1.2.3.zip**, extract the
entire archive into a writable folder, and run **RoleWeaver.exe**. Python is
not required. Configure your AI provider, choose Game Version and Server / Log,
then create/select a character. Back up existing data before upgrading.

**Linux:** download **RoleWeaver-v1.2.3-Linux.tar.gz** from the GitHub release.
Follow INSTALL_LINUX.md, then run bash install-linux.sh and
bash start-role-weaver.sh. X11 supports automatic input and global hotkeys.
Wayland retains manual copy/paste; automatic AFK sending is unavailable.

### Important: select the live NWN2 client log

Follow **NWN2_LOGGING.md** in the package to identify the active nwn2player.ini
and enable ClientChatLogging and ClientEntireChatWindowLogging under
[Game Options]. INI locations and extension logging vary by launcher/build.

Original NWN2 commonly writes to **%LOCALAPPDATA%/Temp/NWN2/LOGS**.
NWN2 EE can write directly to **%LOCALAPPDATA%/Temp/NWN2 EE**, using
**nwclientLog1.txt** or **nwn2client64Log1.txt**. Client Extender may instead
write dated character/chat logs under Documents/Neverwinter Nights 2/Logs.
Linux Wine/Proton paths are inside the game's prefix.

Type a new test sentence in-game and confirm it reaches the selected file
while playing. Browse to that exact file in Role Weaver. Do not select a stale
copy, combat-only log or server log. Role Weaver reads new lines after Start;
select the new active file if the game rotates to another log.

### Control and compatibility

Normal AI suggestions are editable. AFK is an explicit opt-in to automatic
emotes: it pauses normal automatic replies and stays quiet unless someone
addresses the character by name or sends a Tell. Turn AFK off to cancel pending
emotes and restore the previous response mode.

Role Weaver does not install the game or Client Extender. It discovers worlds
from local logs, without a bundled list of named servers or official server
endorsements. Specific game patches, localized logs and third-party loggers may
require custom paths or additional parser support. See GAME_VERSIONS.md for
details and TESTING_v1.2.3.md for checks.

## Links and license

- [Source code](https://github.com/RoleWeaver/roleweaver)
- [Version 1.2.3 downloads and checksums](https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.3)
- Feedback: roleweaverinfo@gmail.com
- MIT License.

Role Weaver is an independent community project and is not affiliated with or
endorsed by the game developers, publishers or persistent-world operators.
