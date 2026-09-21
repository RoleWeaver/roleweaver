# Role Weaver architecture

Role Weaver is being migrated from platform-specific application scripts to a
shared Python package. The migration is deliberately incremental so releases
remain usable and existing character, campaign and memory data stay compatible.

## Repository map

| Path | Responsibility |
| --- | --- |
| `src/roleweaver/` | Shared, platform-neutral application code |
| `src/roleweaver/ai/` | Provider-independent AI contracts and built-in providers |
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

## Compatibility layer

The root and Linux scripts remain runnable during migration. They re-export the
shared provider names that older code imports from `nwn_ai_bot.py`, while the
implementations live only in `roleweaver.ai`.

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
