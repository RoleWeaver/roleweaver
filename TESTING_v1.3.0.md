# v1.3.0 acceptance checks

Use synthetic or backed-up profiles for upgrade tests. Never upload logs, API
keys, private Tells or a player's saved data with a test report.

1. On Windows, install from Setup and separately extract the portable ZIP into
   clean folders. On Ubuntu, extract the Linux archive and run
   `bash install-linux.sh` followed by `bash start-role-weaver.sh`.
2. Confirm all three version values and release asset names are 1.3.0. Check
   Windows and Linux SHA-256 manifests against the downloaded files.
3. Select a live NWN/NWN2 client log. Confirm rapid messages appear once each
   with correct speaker/channel. Try accented Western European text and, if
   available, Polish or Russian legacy logs without replacement characters.
4. Set different user and game languages. Translate Last 3 and Continuous
   Translation should affect game chat only. Edit the first F8/F9 draft,
   translate again and edit the game-language draft before pasting.
5. Open Guardrails & Usage. Confirm backend status, PG defaults, Restore
   Defaults, policy events, request/token counts and cost estimates when rates
   are configured. Verify player edits remain under player control.
6. Check the Updates tab on both platforms. Until a newer stable release is
   published, it should report 1.3.0 as current. Run
   `tests/test_update_rehearsal.py` to exercise a simulated future release,
   checksum failure and safe fresh-folder migration without personal data.
7. Test a Windows Setup upgrade from v1.2.3, preserving settings, characters,
   campaign files and memory. Test F8/F9, manual paste, F10 AFK, backups and
   recovery on a selected game edition. Confirm icons and splash art.
8. On native Ubuntu, test X11 and Wayland behavior as available. Wayland must
   not claim automatic paste or global hotkeys. Close the client before
   preparing a real fresh-folder update, and rerun the Linux installer there.

Run the root and Linux-layout unit suites, Ruff, source-integrity guard and
developer-ZIP checker before tagging. CI also runs the Linux desktop smoke and
update rehearsal under Xvfb.
