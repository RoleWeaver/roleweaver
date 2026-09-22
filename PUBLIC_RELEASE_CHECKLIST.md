# Public release checklist

Before tagging the next Role Weaver client release:

## Source and metadata

- [ ] Choose the exact release commit (merge to `main` or tag the intended
  branch commit); do not tag an older checkout accidentally.
- [ ] Set matching versions in root `VERSION`, `linux/VERSION`, and
  `src/roleweaver/__init__.py`.
- [ ] Write new release notes and acceptance checks. Point the release workflow
  `body_path`, README, Linux guides and packaged documentation at the new files.
- [ ] Confirm the MIT license and repository links are present and current.
- [ ] Review tracked files for API keys, private logs, personal character
  profiles, conversation histories and machine-specific paths.

## Automated builds and manual acceptance

- [ ] Run the root and Linux-layout suites, Ruff, source-integrity check and
  `python -m build` in an editable development environment.
- [ ] Run Linux CI on Ubuntu, including the native GUI smoke test. Install from
  the **extracted Linux release archive**, not only the source checkout.
- [ ] Build Windows Setup, portable ZIP, developer ZIP, wheel and sdist. Run
  `scripts/check_developer_package.py` on the developer ZIP.
- [ ] Test clean Windows Setup and portable launches, plus an upgrade from the
  previous Setup release that preserves settings, character/campaign files and
  memory. Confirm splash image and taskbar icon.
- [ ] Test Ubuntu X11 and, if supported, Wayland startup and game-input limits.
  Test F8/F9/F10 and manual paste with the selected NWN or NWN2 edition.
- [ ] Exercise update download, checksum-failure rejection and fresh-folder
  data migration with a simulated newer release. The ordinary Updates tab will
  show “up to date” until a newer stable release exists.
- [ ] Test OpenAI, Gemini and LM Studio with currently supported models;
  confirm translation and guardrail/usage UI against real provider responses.
- [ ] Check that Windows and Linux checksum manifests cover their respective
  published assets; inspect the final archives before publishing.

## Publication

- [ ] Tag the checked release commit as `vX.Y.Z`; the release workflow publishes
  the downloads and notes. Verify the public asset names and checksums.
- [ ] Keep known limitations visible, especially local-only memory, Linux
  Wayland input limits and the fact that portable/Linux updates prepare a fresh
  folder rather than overwrite the old installation.
- [ ] Consider signed Windows builds and new screenshots/video as follow-up
  improvements, not substitutes for acceptance testing.

## Player + DM messaging

- [ ] GitHub description says Role Weaver is for **players and DMs**.
- [ ] Screenshots show both a player-character workflow and a DM/NPC workflow.
- [ ] Release notes link to both `PLAYER_GUIDE.md` and `DM_GUIDE.md`.
- [ ] Test both included example profiles on a clean installation.
- [ ] Avoid describing Role Weaver as an autonomous player or autonomous DM.
