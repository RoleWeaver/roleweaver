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


if __name__ == "__main__":
    main()
