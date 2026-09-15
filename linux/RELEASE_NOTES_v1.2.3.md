# Role Weaver v1.2.3

- Backup, automatic crash recovery, atomic saves and durable pending AI summaries.
- Recover Guidance, Character, Lore and AI Draft edits with Copy, Discard and
  Clear all. Recovery controls stay visible while the text area resizes.
- F10 AFK: initial character emote, attention checks every 30 seconds, and a
  three-minute minimum interval between subsequent emotes.
- Game Version selection for NWN:EE, Original/Diamond, NWN2, NWN2 EE and Client
  Extender, with mixed NWN2 chat parsing and per-edition log/server selections.
- NWN2 EE Temp/NWN2 EE paths and nwn2client64Log*.txt discovery.
- Quieter backups, improved Auto log selection and clean Exit controls.

## Downloads and upgrading

Windows: installer, portable ZIP and Neverwinter Vault ZIP.
Linux: self-contained source archive with installation/launch scripts.
SHA256 files accompany both platforms.

Back up client data before upgrading. Follow [NWN2 logging](NWN2_LOGGING.md)
to locate the file actually receiving chat. See [game versions](GAME_VERSIONS.md)
and [AFK](AFK_MODE.md). Linux Wayland retains manual paste; automated input and
global hotkeys require X11.

The maintainer reports successful live tests of game selection and AFK.
Not every game patch, localization or third-party logger has been tested.
