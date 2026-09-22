# Role Weaver 1.3.0 — First Run

1. Install using [INSTALLATION.md](INSTALLATION.md).
2. Enable game chat logging. For NWN2, follow [NWN2_LOGGING.md](NWN2_LOGGING.md)
   to locate the active INI and file receiving new chat.
3. Choose **Game Version**, then **Server / Log**. Auto Detect discovers local
   worlds; Browse to the actual live file when the suggested path is wrong.
4. Create/select the correct player character or DM NPC for that world.
   See [CHARACTER_PROFILE_GUIDE.md](CHARACTER_PROFILE_GUIDE.md).
5. Configure your AI provider and confirm **Test AI Connection** succeeds.
   See [AI_PROVIDER_SETUP.md](AI_PROVIDER_SETUP.md).
6. Press **Start**, make a new in-game chat message and check Activity.
   Old log contents are not replayed at Start.
7. F8 generates editable candidate drafts. F9 generates one reply. If user and
   game languages differ, review the user-language draft and its editable
   game-language translation, then paste the approved text into NWN yourself.
8. F10 / AFK sends an initial character emote, checks attention every 30 seconds,
   and allows follow-ups no more often than every three minutes.
   Test keyboard delivery first and read [AFK_MODE.md](AFK_MODE.md).
9. Use Backup to save data and Recover Edits to copy, discard or clear saved
   Guidance, Character, Lore and AI Draft text. Close with **Exit Program**.

F6 pauses/resumes, F11 clears current context and F12 stops the client.
On Linux Wayland, use on-screen controls and manual copy/paste; automatic AFK
sending and global hotkeys are unavailable.
See [TESTING_v1.3.0.md](TESTING_v1.3.0.md) for acceptance checks.
