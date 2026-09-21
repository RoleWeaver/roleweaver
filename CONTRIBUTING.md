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
- Run a Python syntax check before submitting.
- If changing the GUI, verify all Tkinter button callbacks still resolve.
- If changing NWN input behavior, test manual F9 paste as well as automatic sending.

## Development setup

Use an editable package installation so changes under `src/roleweaver` are
available to both platform clients immediately:

    py -3 -m venv .venv
    .venv\Scripts\python.exe -m pip install -e ".[dev]"

See `DEVELOPMENT.md` for Linux commands, validation, package builds and provider
development. `ARCHITECTURE.md` describes module boundaries and migration state.

Windows packaging instructions are in `BUILDING_WINDOWS.md`.

## Windows and Linux development

Windows entry points are at the root and Linux entry points are in `linux/`.
New platform-neutral logic belongs in `src/roleweaver/`; keep operating-system
input and desktop integration behind platform-specific adapters. Some recovery
modules still have mirrored platform copies during the staged migration, so
changes to those files must remain synchronized for now.

Run the root tests from the root and the Linux tests from `linux/`; tests use
isolated temporary data. Run both platform suites before tagging a release.
Never commit personal data, API keys, recovery journals or build output.
