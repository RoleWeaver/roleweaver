# Game versions (v1.2.3)

Select **Game Version** above **Server / Log**, then choose your edition.
Stop the client before changing games. Each edition remembers its own selected
server, discovered servers, log paths, parser preference and window title.
Existing settings default to NWN: Enhanced Edition and retain their custom paths.
Character and campaign files remain world-scoped as before; identical world IDs
across editions refer to the same stored roleplay data.

## Windows locations

| Selection | Locations checked |
| --- | --- |
| NWN: Enhanced Edition | Your Documents/Neverwinter Nights/logs |
| NWN Original (1.69), Diamond | Program Files (x86)/Neverwinter Nights/logs; common standalone/GOG install folders |
| NWN2 / modded original | TEMP/NWN2/LOGS and AppData/Local/Temp/NWN2/LOGS; Documents/Neverwinter Nights 2/Logs |
| NWN2 Enhanced Edition | Temp/NWN2 EE (nwclientLog1.txt or nwn2client64Log1.txt), optional LOGS subfolder; original NWN2 fallbacks |
| NWN2 + Client Extender | Documents/Neverwinter Nights 2/Logs, including character/chat subfolders; NWN2 temporary logs |

The usual base filename is nwclientLog1.txt. Extender chat logs may have dated
filenames instead. Discovery excludes paths containing "combat".
These are candidate locations, not guarantees for every installer or mod.
Use **Server / Log → Browse** for relocated Documents, custom install folders,
different EE log locations, or a specific character's Extender chat file.

The Client Extension is a separate add-on to the original NWN2 client, not the
same product as NWN2 Enhanced Edition. See its
[author's project page](https://www.neverwintervault.org/project/nwn2/other/nwn2-client-extension).
Role Weaver reads logs and does not install or launch either extension.

## Linux locations

NWN:EE keeps the existing native user-data default:
~/.local/share/Neverwinter Nights/logs/nwclientLog1.txt.
NWN_USER_DIRECTORY and the Flatpak Steam user-data folder remain supported.

Classic NWN checks common home installation folders and Wine installations.
NWN2 checks Windows-style log folders inside WINEPREFIX (or ~/.wine) and
standard Steam/Flatpak Steam Proton compatdata prefixes. STEAM_COMPAT_DATA_PATH
is also supported. These prefix mappings are discovery heuristics. External
Steam libraries, Lutris/Bottles prefixes, and custom native classic installs may
require browsing to the actual log file.

Linux X11 uses the existing game-input adapter. Wayland retains manual copy/paste;
global F-keys and AFK automatic sending remain unavailable.

## NWN2 parsing and setup

The NWN2 selections accept mixed channel-first and speaker-first messages,
including Talk, Party, Whisper, Tell, Shout and DM, plus bracketed numeric
timestamps. Outgoing To messages are marked as your own and retain their recipient;
incoming From messages retain the other character's identity.
Unmarked combat, server status and script lines are ignored.
Loading Area lines update the area display. Server welcome text supplies the
world label where present.

The supplied NWN2 sample produced 11 chat events from 57 lines, including both
whisper directions and DM messages. This validates that sample, not every
localized, modded or Client Extender logging format. Unsupported layouts may need
another sample. Your supplied log is not bundled in the repository.

Enable chat logging in your game or extension first and select a log that updates
while playing. Role Weaver tails new text after Start; it does not replay the
existing file into the active conversation. Daily/character-specific Extender
files may require selecting the new file and restarting the client.

The selected game also sets the input window-title match to Neverwinter Nights
or Neverwinter Nights 2. Live keyboard delivery across these newly added editions
has not been validated here. Use the keyboard test and F9 editable draft before
enabling AFK; custom window titles and key bindings may require settings changes.

## Manual checks

1. Select each installed edition and check its suggested log location.
2. Browse to the actual log, select the world/character, then Start.
3. Speak in-game and confirm only new chat appears, with the correct speaker and
   channel. For NWN2, test Talk, Party, both private-message directions and DM.
4. Confirm combat and script messages do not appear as character dialogue.
5. Test F8, then F9 and keyboard input with an editable draft.
6. Stop, switch editions, then switch back: confirm the saved log/server returns.
7. Test AFK only after confirming draft delivery targets the correct game window.

See [v1.2.3 release notes](RELEASE_NOTES_v1.2.3.md).

For INI configuration and identifying the live file, follow [NWN2 logging](NWN2_LOGGING.md).
