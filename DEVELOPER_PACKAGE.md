# Developer source package

The GitHub release offers three kinds of download with different purposes:

| Download | Contains | Intended use |
| --- | --- | --- |
| `RoleWeaver-Developer-vX.Y.Z.zip` | Full tracked repository: Windows and Linux entry points, shared package, tests, docs and scripts | Modify or contribute to the desktop client |
| `roleweaver_client-X.Y.Z-py3-none-any.whl` / `.tar.gz` | Installable `roleweaver` library under `src/` | Reuse shared contracts and services in Python code |
| Windows or Linux application archive | Runnable desktop client and platform resources | Play, DM or test a packaged release |

The wheel is not a standalone desktop application. It intentionally excludes
`nwn_ai_gui.py`, platform launchers, assets and personal data. If you want to
change the desktop UI or game input, use a Git clone or the developer ZIP.

## Start from the developer ZIP

1. Extract the ZIP into a writable folder. Do not work in the ZIP viewer.
2. Open a terminal in the extracted `RoleWeaver-Developer-vX.Y.Z` folder.
3. Follow [DEVELOPMENT.md](DEVELOPMENT.md) for a Windows or Linux editable
   environment. The root `pyproject.toml` installs `src/roleweaver` in editable
   mode; source edits are immediately visible to both clients.
4. Run the root tests and the Linux-layout tests before making changes.
5. Read [ARCHITECTURE.md](ARCHITECTURE.md) for module ownership and the current
   compatibility layer. [CONTRIBUTING.md](CONTRIBUTING.md) covers pull requests.

The latest code is on the repository, while a developer ZIP is a snapshot of
its release tag. A Git clone is preferable if you intend to submit a pull
request because it retains history and makes rebasing straightforward.

## Where to make a change

| Change | First place to look | Contract tests |
| --- | --- | --- |
| AI provider, structured result or usage | `src/roleweaver/ai/` | `tests/test_ai_contracts.py`, `tests/test_guardrails_usage.py` |
| Guardrail policy or backend | `src/roleweaver/guardrails/` | `tests/test_guardrails_usage.py` |
| Translation or protected terminology | `src/roleweaver/translation/` | `tests/test_translation.py` |
| Bilingual draft generation, refinement or editor state | `src/roleweaver/drafting.py` | `tests/test_drafting.py`, both `test_client_fixes.py` suites |
| Chat parsing or log following | `src/roleweaver/conversation/` | `tests/test_conversation_contracts.py` |
| Settings or data location | `src/roleweaver/config/`, `src/roleweaver/paths.py` | `tests/test_config_storage_contracts.py` |
| Backup, recovery or updater | `src/roleweaver/storage/`, `src/roleweaver/update_install.py`, `src/roleweaver/updates.py` | `tests/test_backup.py`, `tests/test_update_install.py`, `tests/test_updates.py` |
| Desktop UI | `nwn_ai_gui.py`, `linux/nwn_ai_gui.py`, shared `src/roleweaver/update_ui.py` | Both test suites plus a manual desktop check |
| Game keyboard/clipboard input | `nwn_ai_bot.py`, `linux/nwn_ai_bot.py`, `linux/linux_platform.py`; outgoing text normalization in `src/roleweaver/game_text.py` | Both test suites, `tests/test_game_text.py`, and live-game checks |

Do not put new platform-neutral rules into just one bot or GUI file. Extract a
small shared service, retain compatible entry points, and add tests for both
clients. `scripts/check_source_integrity.py` catches drift in mirrored bot
functions, but it does not replace desktop or game testing.

## Privacy and release verification

Use synthetic characters and logs in tests. Never include `settings.json`,
API keys, private chat, `RoleWeaver_Data`, backups or a real player's profiles
in an issue, fixture or pull request. The release workflow builds the developer
ZIP with `git archive` (tracked files only), then runs
`scripts/check_developer_package.py` to check expected files and reject known
runtime-data paths. That check complements, rather than replaces, a human
privacy review before release.
