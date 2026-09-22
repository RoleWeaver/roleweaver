"""Runtime data paths without platform UI or storage dependencies."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    """All persistent locations belonging to one Role Weaver installation."""

    root: Path

    @classmethod
    def from_entrypoint(
        cls,
        entrypoint: str | Path,
        *,
        frozen: bool | None = None,
        executable: str | Path | None = None,
    ) -> RuntimePaths:
        """Resolve the data root for source and frozen application launches."""

        is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
        location = Path(executable or sys.executable) if is_frozen else Path(entrypoint)
        return cls(location.resolve().parent)

    @property
    def settings(self) -> Path:
        return self.root / "settings.json"

    @property
    def character_prompt(self) -> Path:
        return self.root / "character_prompt.txt"

    @property
    def characters(self) -> Path:
        return self.root / "Characters"

    @property
    def campaigns(self) -> Path:
        return self.root / "Campaigns"

    @property
    def lore(self) -> Path:
        return self.root / "Lore"

    @property
    def roleplay_rules(self) -> Path:
        return self.root / "RoleplayRules"

    @property
    def application_data(self) -> Path:
        return self.root / "RoleWeaver_Data"

    @property
    def backups(self) -> Path:
        return self.root / "Backups"
