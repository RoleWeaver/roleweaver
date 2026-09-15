ROLE WEAVER v1.2.3

Persistent Character and Campaign Continuity for NWN and NWN2
For players and Dungeon Masters — Windows and Linux

Role Weaver is a free, open-source companion for all editions of Neverwinter
Nights and Neverwinter Nights 2: Original NWN, Diamond, NWN:EE, NWN2, NWN2 EE
(including 64-bit client logs), and NWN2 with Client Extender.

It follows your local client chat log, maintains character/NPC memory and
relationships, and generates editable roleplay suggestions. It also provides
NPC briefings, campaign continuity, persistent guidance and conversation history.

NEW IN v1.2.3
- Game Version selector with per-edition server and log settings.
- Mixed NWN2 chat parsing, including incoming/outgoing private messages.
- NWN2 EE log discovery in Temp/NWN2 EE, including nwn2client64Log*.txt.
- F10 AFK: a short character emote on activation, attention checks every
  30 seconds, and at least three minutes between follow-up emotes.
- Manual backups, automatic crash protection and atomic saves.
- Recovery of unfinished Guidance, Character, Lore and AI Draft edits.
- Durable pending AI summaries that can resume after interruption.
- Recover Edits with Copy text, Discard and Clear all; controls remain visible
  while resizing the window.
- Quieter automatic backups, improved Auto log selection and clean Exit controls.

WINDOWS INSTALLATION (THIS ZIP)
1. Back up an existing Role Weaver installation before upgrading.
2. Extract the entire ZIP into a writable folder. Run RoleWeaver.exe.
   Python is not required for this packaged Windows build.
3. Configure Google Gemini, OpenAI, or a local model through LM Studio,
   then test the AI connection. Supply your own provider credentials if needed.
4. Choose Game Version, then Server / Log. For NWN2, follow NWN2_LOGGING.md
   to enable file logging and Browse to the client log receiving new chat.
5. Create/select the correct character profile and press Start.
6. Make a new in-game chat message and verify it appears in Role Weaver.

Do not overwrite personal profiles or data with the generic examples.
Copying Python files beside an old executable does not update that executable.

LINUX
Download RoleWeaver-v1.2.3-Linux.tar.gz from the GitHub release. Follow
INSTALL_LINUX.md in that archive, then run bash install-linux.sh and
bash start-role-weaver.sh as your normal desktop user.
Linux X11 supports automatic input and global hotkeys. Wayland uses manual
copy/paste; F10 AFK automatic sending and global hotkeys are unavailable there.

NWN2 LOGGING
Close the game before editing its active nwn2player.ini. Back up that file,
then add/update these keys in the existing section:

[Game Options]
ClientChatLogging=1
ClientEntireChatWindowLogging=1

The active INI location depends on the edition/launcher; start with
Documents/Neverwinter Nights 2. See NWN2_LOGGING.md for older installations,
EE, Client Extender and Wine/Proton details.

Common Windows client logs:
- NWN2: %LOCALAPPDATA%/Temp/NWN2/LOGS/nwclientLog1.txt
- NWN2 EE: %LOCALAPPDATA%/Temp/NWN2 EE/nwclientLog1.txt
- NWN2 EE 64-bit: %LOCALAPPDATA%/Temp/NWN2 EE/nwn2client64Log1.txt
- Client Extender: Documents/Neverwinter Nights 2/Logs, often dated and
  organized under character/chat subfolders.

Always confirm the selected file receives a new test sentence while playing.
Do not select a stale copy, server log or combat-only file. If the game switches
log files, stop Role Weaver, select the active file and Start again.

DRAFTS AND AFK
F8 generates editable suggestions. F9 places an editable draft in the game chat
on supported platforms; review it before sending.
AFK is opt-in and sends emotes automatically. It pauses normal automatic replies.
Follow-up AFK emotes require attention detected through the character's name
or an incoming Tell. Unrelated chat stays quiet. Turn AFK off to cancel pending
emotes and restore the previous response mode.
See AFK_MODE.md for the full behavior and platform limits.

SUPPORT AND COMPATIBILITY
Role Weaver reads logs your game already creates; it does not supply server
logs, install Client Extender or launch the game. Server discovery is local;
no named persistent-world catalog or official server endorsements are included.
Game patches, localization and third-party loggers may need custom paths or
additional parsing support. See GAME_VERSIONS.md and TESTING_v1.2.3.md.

Source: https://github.com/RoleWeaver/roleweaver
Release: https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.3
Feedback: roleweaverinfo@gmail.com

LICENSE
MIT License. Role Weaver is an independent community project, not affiliated
with or endorsed by the game developers, publishers or persistent-world operators.
