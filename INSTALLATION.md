# Role Weaver 1.2.3 — Installation

Supports Windows and Linux and all NWN/NWN2 editions: Original NWN, Diamond,
NWN:EE, NWN2, NWN2 EE and NWN2 with Client Extender.

## Download and install

Choose from the [v1.2.3 release](https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.3).

| Package | Installation |
| --- | --- |
| RoleWeaver-Setup-v1.2.3.exe | Run the Windows installer |
| RoleWeaver-Portable-v1.2.3.zip | Extract fully and run RoleWeaver.exe |
| RoleWeaver-NeverwinterVault-v1.2.3.zip | Windows portable build with Vault README |
| RoleWeaver-v1.2.3-Linux.tar.gz | Extract and follow INSTALL_LINUX.md |
| GitHub source archive | Windows at root; Linux under linux/ |

**Packaged Windows builds do not require Python.** Keep the supplied folders with
the executable. Extract archives into a writable location and back up existing
data before upgrading. Checksum files accompany the downloads.

## Windows from source

Install Python 3.10 through 3.13 with Tkinter; release builds use Python 3.12.
In Command Prompt, change to the source root and run:

    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    .venv\Scripts\python.exe nwn_ai_gui.py

Use py -3 for the first command if your installation uses the Python launcher.
After setup, RoleWeaver.bat also launches the client.
Create_RoleWeaver_Desktop_Shortcut.ps1 optionally creates a source shortcut.
Developers can build with scripts/build_windows.ps1.
For an editable development install, architecture notes and full validation
commands, see [DEVELOPMENT.md](DEVELOPMENT.md) and
[ARCHITECTURE.md](ARCHITECTURE.md).

## Linux

Follow [Linux installation](linux/INSTALL_LINUX.md). In a full checkout, change
to linux/ first. The Linux release archive already contains the client root.
Run installation and launch scripts as your normal desktop user.

X11 supports automatic input and global hotkeys. Wayland uses manual copy/paste
and on-screen controls; automatic AFK sending is unavailable.

## First-time setup

1. Enable your game's client chat logging and enter a session.
2. Choose **Game Version**, then **Server / Log**.
3. Select the file receiving new chat. Auto Detect discovers local worlds; for
   NWN2 verify the live file using [NWN2 logging](NWN2_LOGGING.md).
4. Create/select your player character or DM NPC for that world.
   See [character profiles](CHARACTER_PROFILE_GUIDE.md).
5. Configure Gemini, OpenAI or LM Studio and confirm **Test AI Connection**.
   See [AI provider setup](AI_PROVIDER_SETUP.md).
6. Press **Start**, make a new in-game message and check Activity.

Role Weaver follows new text after Start; it does not replay old contents.
NWN2 EE may write nwclientLog1.txt or nwn2client64Log1.txt directly under
%LOCALAPPDATA%/Temp/NWN2 EE. Original NWN2 commonly uses Temp/NWN2/LOGS.
INI and Wine/Proton instructions are in NWN2_LOGGING.md. Do not select a stale
copy, server log or combat-only file. If the active file changes, Stop, Browse
to it and Start again. Stop before switching game editions.

## Controls and recovery

| Control | Behavior |
| --- | --- |
| F6 | Pause/resume |
| F8 | Generate editable candidate drafts |
| F9 | Place an editable draft in game chat on supported platforms |
| F10 / AFK | Toggle Away From Keyboard |
| F11 | Clear current conversation context |
| F12 | Stop the client |

F9 does not press the final Enter. Review the draft before sending.
AFK sends an initial emote, then checks attention every 30 seconds with a
three-minute minimum interval between follow-ups. See [AFK mode](AFK_MODE.md).
Test keyboard delivery before enabling automatic sending.

**Version 1.2.3 includes** backups, crash protection, pending-summary recovery and
unfinished-edit recovery. Recover Edits has Copy text, Discard and Clear all for
Guidance, Character, Lore and AI Draft text. Read [backup/recovery](BACKUP_RECOVERY.md)
and [edit/summary recovery](EDIT_SUMMARY_RECOVERY.md).

## Saved data and upgrading

Profiles are under Characters/&lt;server&gt;/, lore under Lore/&lt;server&gt;/,
and rules under RoleplayRules/&lt;server&gt;/. RoleWeaver_Data contains memory
and history. Campaigns, settings and character preferences also contain personal data.

1. Save a backup using the existing client's Backup control.
2. Close with **Exit Program**.
3. Install/extract the new version. Preserve personal data; do not replace your
   profiles with generic examples.
4. If moving to a fresh folder, restore your backup. Source installations need
   their dependency-install step rerun.
5. Verify game, live log, character and AI connection before Start.

Copying Python files beside an old executable does not update it.

## Troubleshooting and next steps

- No chat: verify a new test sentence reaches the selected file while playing.
- No paste: use Keyboard Test and focus the correct window. On Wayland,
  use Copy Edited Draft and paste manually.
- Provider changes with character: provider/model preferences are per profile.
- Continue with [First Run](FIRST_RUN.md), [Player Guide](PLAYER_GUIDE.md),
  [DM Guide](DM_GUIDE.md) or [v1.2.3 tests](TESTING_v1.2.3.md).
