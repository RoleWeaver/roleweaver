# Role Weaver architecture

Role Weaver is being migrated from platform-specific application scripts to a
shared Python package. The migration is deliberately incremental so releases
remain usable and existing character, campaign and memory data stay compatible.

## Repository map

| Path | Responsibility |
| --- | --- |
| `src/roleweaver/` | Shared, platform-neutral application code |
| `src/roleweaver/ai/` | Provider-independent AI contracts and built-in providers |
| `src/roleweaver/guardrails/` | Replaceable dialogue-safety boundary and Guardrails AI adapter |
| `src/roleweaver/config/` | Typed defaults, migration-aware settings loading and persistence |
| `src/roleweaver/conversation/` | Chat event contract, NWN log parsing and resilient log following |
| `src/roleweaver/games.py` | Game editions, log discovery and NWN2 normalization |
| `src/roleweaver/paths.py` | Explicit runtime locations for source and packaged applications |
| `src/roleweaver/storage/` | Atomic writes, validated backups and crash recovery |
| `nwn_ai_gui.py` | Windows Tkinter entry point and compatibility application shell |
| `nwn_ai_bot.py` | Windows conversation engine and compatibility exports |
| `linux/` | Linux entry points and platform input adapter |
| `tests/` | Windows/shared regression tests |
| `linux/tests/` | Linux and platform-adapter regression tests |
| `scripts/` | Build and release tooling |
| `installer/` | Inno Setup definition for the Windows installer |

New platform-neutral behavior belongs under `src/roleweaver/`. Platform files
should translate operating-system events into shared types rather than duplicate
business logic.

## AI request boundary

All built-in providers implement the same request/result contract from
`roleweaver.ai`:

```python
from roleweaver.ai import AIRequest, AIRequestPurpose

result = provider.generate(
    AIRequest(
        instructions="Return one in-character response.",
        prompt="Conversation context...",
        purpose=AIRequestPurpose.REPLY,
    )
)

print(result.text)
print(result.provider, result.model)
print(result.usage.input_tokens, result.usage.output_tokens)
```

`AIResult` records text, provider, model, purpose, duration, provider request ID,
and token counts when the provider reports them. A count with
`usage.source == "provider"` came from the provider response. Unavailable values
remain `None`; callers must not present them as zero.

The supported purposes are reply, candidate generation, memory summary, AFK,
translation and connection test. Translation is included in the contract now so
it can use the same monitoring and guardrail path later.

`AIExecutionService` is the common runtime boundary around providers. It checks
input through a `GuardrailBackend`, invokes the provider, normalizes the result,
checks output and writes content-free usage metadata. The shipped backend is
Guardrails AI, but the protocol keeps that implementation replaceable. The
client has no runtime, configuration, database or service dependency on the
separate Role Weaver server addon.

Usage telemetry is stored locally in `RoleWeaver_Data/usage.sqlite3` with a
30-day retention period. It records request metadata, reported token counts,
guardrail actions and optional cost estimates. It never stores prompt or reply
text. See `GUARDRAILS_AND_USAGE.md` for the user and extension contract.

## Conversation boundary

Game logs are normalized through `roleweaver.conversation` before they reach
memory, prompting or the UI. `parse_chat_line()` returns a `ChatEvent` mapping
with stable speaker, channel, message, self-message and server-profile fields.
NWN2 Tells may also contain a `recipient`. This dictionary-shaped contract
preserves compatibility while giving extensions a documented type to target.

`LogFollower` owns rotation and truncation handling. It is platform-neutral;
operating-system adapters are responsible only for locating logs and delivering
keyboard/clipboard input.

## Compatibility layer

The root and Linux scripts remain runnable during migration. They re-export the
shared provider and conversation names that older code imports from
`nwn_ai_bot.py`. The root and Linux `roleweaver_games.py` files redirect legacy
imports to `roleweaver.games`, so monkey-patching and existing extensions still
operate on the authoritative module.

The legacy `roleweaver_storage`, `roleweaver_backup`, and `roleweaver_crash`
module names similarly redirect to `roleweaver.storage`. This is a module alias,
not a copied facade, so locks, shutdown state and monkey-patches remain shared.

## Configuration and storage boundary

Both desktop clients construct their defaults through `roleweaver.config` and
inject only platform-specific values such as the default log path, keyboard
method and Linux path migration. `SettingsStore` preserves unknown extension
keys, merges nested server-log paths, registers legacy selected profiles and
writes complete settings snapshots atomically.

`RuntimePaths` is the authoritative description of persistent locations. The
launchers determine the installation root; shared code derives settings,
characters, campaigns, lore, rules, backups and application-data paths from it.
User data remains beside the current installation for compatibility.

The storage package owns the process-wide write lock, atomic replacement,
validated backup archives and crash recovery. Higher-level character and
campaign repositories can now be added without duplicating these guarantees.

Future extractions should be small and behavior-preserving. Move shared logic,
keep a compatibility import where necessary, add focused tests, then remove the
obsolete copy after both platform paths use the package directly.

## Data and privacy boundaries

Runtime data is intentionally outside the installable package. Settings,
characters, lore, campaigns, histories, API keys and recovery data must never be
included in a wheel, source distribution, test fixture derived from a user, or
commit. See `SECURITY.md` and `.gitignore`.

## Dependency direction

The intended dependency direction is:

```text
platform launchers / GUI
          |
          v
conversation orchestration
          |
          v
shared package contracts and services
          |
          v
provider SDKs / platform adapters / filesystem
```

Shared modules must not import either GUI. Provider modules must not know about
Tkinter, NWN input injection, character storage or campaign storage.
