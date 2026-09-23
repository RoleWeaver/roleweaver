# Role Weaver v1.3.1

This maintenance release improves editable bilingual drafts, game-chat
punctuation, and the shared developer package on Windows and Linux. The Role
Weaver server addon remains independent of this client.

## Changes since v1.3.0

- Generate, shorten or lengthen text from the edited draft in either the user's
  language or the game language. Translate back for review without losing the
  choice of editor. Each draft has its own Clear control.
- Move the Activity display's Clear control next to its heading.
- Convert typographic apostrophes, quotation marks and dashes to game-safe
  punctuation only when copying or pasting into NWN. The editable draft keeps
  the original text.
- Share bilingual draft transitions between the Windows and Linux clients and
  document their integration boundary for contributors.

## Updating from v1.3.0

Open **Updates** and press **Check for Updates**. Once this stable release and
its assets are published, **Download Update** verifies the relevant download
against its SHA-256 manifest. Installed Windows copies can close and launch
Setup. Windows portable and Linux copies use **Prepare New Folder**, which
copies supported saved data while keeping the old installation available for
rollback. On Linux, run `bash install-linux.sh` in the new folder before
starting the client. Back up your data and stop an active game session first.
See [Updates](UPDATES.md) and [installation](INSTALLATION.md).

Guardrail checks still apply to generated content, not player edits made after
generation. Linux Wayland still requires on-screen controls and manual paste.
See [acceptance checks](TESTING_v1.3.1.md).
