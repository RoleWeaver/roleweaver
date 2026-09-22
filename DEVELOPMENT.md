# Role Weaver development guide

## Prerequisites

- Git
- Python 3.10 through 3.13; release builds currently use Python 3.12
- Tkinter for the desktop client
- Linux desktop tools described in `linux/INSTALL_LINUX.md` when developing on Linux

## Editable development environment

Clone the repository and work from its root.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe nwn_ai_gui.py
```

### Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
cd linux
../.venv/bin/python linux_start.py
```

An editable install exposes `src/roleweaver` immediately, so package edits do
not require reinstalling. Do not use a real character profile, private game log,
or production API key in automated tests.

## Validation

Run all checks before opening a pull request:

```powershell
py -3 -m compileall -q src
py -3 -m unittest discover -s tests -v
Push-Location linux
py -3 -m unittest discover -s tests -v
Pop-Location
py -3 -m ruff check
```

On Linux, use `.venv/bin/python` in place of `py -3`.

GUI, input, packaging and release changes also require the manual checks in the
current `TESTING_*.md` and `PUBLIC_RELEASE_CHECKLIST.md` documents.

## Build the development package

```powershell
py -3 -m build
```

This creates a wheel and Python source distribution under `dist/`. They contain
the reusable `roleweaver` package, not private runtime data. The complete
developer-source ZIP produced by the release workflow contains the application
entry points, tests, documentation and build scripts as well.

## Adding a provider

1. Implement the provider in `src/roleweaver/ai/providers.py` or a focused module
   under that package.
2. Accept `AIRequest` and return `AIResult`.
3. Report provider token usage only when the SDK actually supplies it.
4. Add the provider to `AI_PROVIDERS` and `create_ai_provider`.
5. Add contract tests without making network calls.
6. Update `AI_PROVIDER_SETUP.md` and privacy documentation.

Provider exceptions should remain actionable and must never include API keys,
complete prompts, private Tells or personal filesystem paths.

## Adding a guardrail backend

1. Implement `roleweaver.guardrails.GuardrailBackend` and return
   `GuardrailResult` from input and output validation.
2. Keep the backend independent of Tkinter and provider SDKs.
3. Do not persist prompts, replies, Tells, translations or API keys as
   telemetry.
4. Route provider calls through `AIExecutionService`; direct provider calls
   bypass both guardrails and usage reporting.
5. Add focused tests for pass, block and degraded behavior without network
   access.

Guardrails AI is the installed default implementation. The protocol is the
replacement boundary; it is not a switch for silently disabling validation.
See `GUARDRAILS_AND_USAGE.md` for data retention and UI behavior.

## Adding a game-log format

1. Add platform-neutral directory discovery or normalization to
   `src/roleweaver/games.py`.
2. Add parsing behavior under `src/roleweaver/conversation/` and return a
   `ChatEvent`; do not pass raw platform log lines into AI providers.
3. Keep system/combat lines conservative so they cannot become false speakers.
4. Add fixtures to `tests/test_games.py` or a focused contract test without
   including a real player's log.
5. Run both Windows/shared and Linux suites because both clients consume the
   same parser and follower.

## Adding configuration

1. Add built-in fields to `RoleWeaverSettings` and `default_settings()` under
   `src/roleweaver/config/`.
2. Preserve unknown JSON fields so extensions can maintain their own settings.
3. Use an explicit migration callback for renamed or transformed values; never
   silently discard an older value.
4. Resolve saved-data locations through `RuntimePaths` instead of constructing
   new paths throughout GUI or provider code.
5. Use `roleweaver.storage.atomic` for persistent writes. Direct writes can
   bypass shutdown protection, crash recovery and backup serialization.

## Pull-request scope

Keep refactors separable from behavior changes. A package extraction should
first preserve behavior; feature work can then depend on the new interface in a
later commit or pull request. This makes regressions and platform drift easier
to identify.
