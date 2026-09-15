# Contributing to Role Weaver

Thanks for helping improve Role Weaver.

## Bug reports

Before opening an issue:

1. Confirm the problem occurs with the newest release.
2. Note the Role Weaver version.
3. Note the selected NWN server profile and AI provider.
4. Include the relevant Activity-panel messages.
5. Remove API keys, private Tells, personal paths, and other sensitive information.

For NWN input/paste problems, mention whether **Keyboard Test** works and whether Neverwinter Nights is running as Administrator.

## Feature requests

Describe the roleplay problem the feature would solve. Role Weaver's design principle is:

> The human owns the character; Role Weaver helps preserve the story.

Features should preserve player/DM control rather than silently taking ownership of roleplay decisions.

## Pull requests

- Keep changes focused.
- Do not commit `settings.json`, `RoleWeaver_Data`, API keys, logs, or personal character profiles.
- Run a Python syntax check before submitting.
- If changing the GUI, verify all Tkinter button callbacks still resolve.
- If changing NWN input behavior, test manual F9 paste as well as automatic sending.

## Development setup

Install Python and dependencies using the instructions in `INSTALLATION.md`.

Windows packaging instructions are in `BUILDING_WINDOWS.md`.

## Windows and Linux development

Windows source is at the root; the self-contained Linux client is in linux/. Apply shared recovery changes to both copies of roleweaver_backup.py, roleweaver_crash.py, roleweaver_drafts.py, roleweaver_pending.py and roleweaver_storage.py. Keep platform input adapters separate. Run the root tests from the root and the Linux tests from linux/; tests use isolated temporary data.
Keep Windows and Linux shared modules synchronized. Run both platform suites before tagging a release. Never commit personal data, API keys, recovery journals or build output.
