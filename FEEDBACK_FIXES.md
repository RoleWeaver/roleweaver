# Client feedback fixes and acceptance checks

## Both clients

- Draft capture only observes Guidance, character-editor text, Lore and AI Draft. It ignores Tk internal string widget paths and unrelated fields.
- Removed the recovered-edits popup at startup. Open Recover Edits when needed.
- Recovery includes Copy text, Ctrl+C for selected text, Discard selected edit and Clear all. Selecting text no longer loses the edit selection. Copy never copies the list-row label.
- Automatic backup successes are silent. Errors remain visible in Activity.
- Server / Log appears before Character and is the initial settings panel.
- Exit Program uses the normal close handler, including draft flushing and the final automatic backup.
- Auto resolves the live log before loading the detected world's character. A cached default cannot suppress discovery. Scanning multiple logs for the same world retains its newest log. Each log reader stays bound to its own bot/session; a stopped old reader cannot stop a new session.

## Linux

The default is the current user's `~/.local/share/Neverwinter Nights/logs/nwclientLog1.txt`. NWN_USER_DIRECTORY remains an explicit override. Nonexistent defaults copied from another home directory or Windows are migrated; existing files and custom paths are retained.

## Update and retest

These changes are maintained in GitHub as unreleased development source. Use the source package for your platform, preserving personal data. Replace the seven Python files listed in EDIT_SUMMARY_RECOVERY.md together. On Linux, also replace linux_platform.py. Windows executable installations require a rebuild; copying Python files alongside an old executable does not update it.

The maintainer confirmed these fixes work on both platforms. Repeat these checks after further changes:

1. Open Guidance, a character editor, Lore and AI Draft; type, open dropdowns and switch windows. Confirm there are no draft-recovery widget errors and no recovery popup on the next launch.
2. In Recover Edits, highlight part of a saved edit and use Copy text or Ctrl+C. Paste into Guidance. Clear all, close/reopen recovery and confirm it stays empty until you make a new edit.
3. Select Auto and press Start once while NWN is logging. Confirm the displayed Watching path is the live client log and new chat immediately arrives. Stop and restart once to check session isolation.
4. Leave the client open for six minutes. Confirm the Automatic backup directory gains a backup without a success line in Activity. Close with Exit Program and reopen normally.
5. On Linux, check the initial log path uses your own home directory. Your Browse-selected custom paths should remain usable.

Automated checks: Windows 51 passed, one Linux-only test skipped; Linux source 79 passed, all run on the Windows host. The log-start regression test tails a real temporary file and receives appended chat. Clipboard and editor tests use mocked Tk widgets. The maintainer has confirmed the reported issues are resolved on Windows and Linux; broader gameplay/platform coverage should continue before the next release.

## Development status

The maintainer confirmed the recovery and feedback-fix tests work on Windows and Linux. Further features will be added before creating the next distribution. Automated tests ran on the Windows host; that does not establish exhaustive native Linux desktop or gameplay coverage.
