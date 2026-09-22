# Contributing to Role Weaver

Thanks for helping improve Role Weaver.

## Bug reports

Before opening an issue:

1. Confirm the problem occurs with the newest release.
2. Note the Role Weaver version.
3. Note the selected NWN server profile and AI provider.
4. Include the relevant Activity-panel messages.
5. Remove API keys, private Tells, personal paths, and other sensitive information.

For NWN or NWN2 input/paste problems, mention whether **Keyboard Test** works and whether Neverwinter Nights is running as Administrator.

## Feature requests

Describe the roleplay problem the feature would solve. Role Weaver's design principle is:

> The human owns the character; Role Weaver helps preserve the story.

Features should preserve player/DM control rather than silently taking ownership of roleplay decisions.

## Pull requests

- Keep changes focused.
- Do not commit `settings.json`, `RoleWeaver_Data`, API keys, logs, or personal character profiles.
- Run the Linux tests and the root shared/update tests before submitting.
- If changing the GUI, verify all Tkinter button callbacks still resolve.
- If changing NWN input behavior, test manual F9 paste as well as automatic sending.

## Development setup

In a repository checkout, use the root `DEVELOPMENT.md` and
`DEVELOPER_PACKAGE.md` for editable setup and module ownership. From the Linux
client folder, run `../.venv/bin/python -m unittest discover -s tests -v` when
using the root development environment. Run the same tests with
`.venv/bin/python` in an extracted Linux release archive.

Shared contracts and services live under `src/roleweaver/`; Linux keyboard,
clipboard and desktop integration remain in `linux/`. Do not duplicate shared
AI, translation, guardrail, update or log-parsing logic in the Linux bot file.
Native Ubuntu desktop validation is still needed for GUI and game input work.

For Windows packaging, consult `BUILDING_WINDOWS.md` in the full repository or
developer-source ZIP.
