"""Start the macOS client and seed user-writable application data."""

import shutil
import sys
from pathlib import Path


def seed_user_data():
    from roleweaver.paths import RuntimePaths

    root = RuntimePaths.from_entrypoint(__file__).root
    root.mkdir(parents=True, exist_ok=True)
    resources = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for folder in ("Characters", "Campaigns", "Lore", "RoleplayRules"):
        source = resources / folder
        if source.is_dir():
            for file in source.rglob("*"):
                if file.is_file():
                    target = root / folder / file.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        shutil.copy2(file, target)


def main():
    from mac_platform import require_desktop

    require_desktop()
    seed_user_data()
    import nwn_ai_gui

    nwn_ai_gui.main()


def guardrails_smoke(result_path):
    """Exercise Guardrails from the packaged app without opening the GUI."""
    from roleweaver.storage import atomic_write_text

    try:
        from roleweaver.guardrails import GuardrailsAIBackend

        backend = GuardrailsAIBackend()
        if backend.error:
            raise RuntimeError(backend.error)
        backend.validate_output("A safe reply.", {"purpose": "reply"})
        result = "active"
    except Exception as exc:
        result = f"{type(exc).__name__}: {exc}"
    atomic_write_text(Path(result_path), result)
    return result == "active"


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--guardrails-smoke":
        raise SystemExit(0 if guardrails_smoke(sys.argv[2]) else 1)
    main()
