# Role Weaver v1.3.0

This release adds editable language translation, client-side guardrail policy
controls, AI usage reporting, and in-app update checks to the NWN/NWN2 desktop
client. The Role Weaver server addon remains a separate product; the two do not
communicate or share runtime state.

## Highlights

- Translate recent game chat on demand or continuously. The Activity and
  Translation windows have a draggable divider. Language Settings select the
  user's language, game language and protected setting terms.
- F8/F9 generate editable drafts in the user's language. A second editable
  draft holds the game-language translation. The player reviews and explicitly
  pastes the result into NWN; manually edited text is not rechecked at posting.
- Guardrails & Usage provides PG-oriented defaults, per-purpose policy actions,
  Restore Defaults, policy events, request/token charts and optional estimated
  costs. Estimates depend on provider-reported token counts and user-entered
  rates; they are not billing statements.
- The Updates tab checks the latest stable GitHub release. Downloads are
  verified with the published SHA-256 manifest. Installed Windows builds can
  launch Setup; portable Windows and Linux builds prepare a fresh folder with
  copied saved data, preserving the old installation for rollback.
- Legacy NWN chat decoding now handles common Western European, Polish and
  Russian encodings. The conversation follower is more resilient when chat
  arrives in bursts.
- A shared Python package, developer-source ZIP, contributor guides and
  source-integrity checks make the client easier to extend on both platforms.

## Upgrading

Back up your saved data before upgrading. Version 1.2.3 does not have the
Updates tab, so download v1.3.0 manually for this upgrade. On Windows, use the
Setup executable for an installed copy or extract the portable ZIP into a new
folder. On Ubuntu, extract the Linux archive into a new folder and run
`bash install-linux.sh` there. Do not overwrite your current folder with an
archive. See [installation](INSTALLATION.md) and [updates](UPDATES.md).

## Limits and privacy

Translation sends selected game chat to the configured AI provider. The usage
database stores request metadata, not prompt or reply text. Guardrail rules
apply to AI input and generated output, not to text a player edits afterward.
Linux Wayland still uses on-screen controls and manual paste; automatic game
input and global hotkeys require X11. Portable/Linux update preparation copies
saved data but does not install Linux dependencies or remove the old version.
See [translation](TRANSLATION.md), [guardrails and usage](GUARDRAILS_AND_USAGE.md),
and [acceptance checks](TESTING_v1.3.0.md).
