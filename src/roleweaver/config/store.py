"""Loading, merging, migration and durable persistence of client settings."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Collection, Mapping
from pathlib import Path
from typing import Any

from roleweaver.storage import atomic

from .models import RoleWeaverSettings, migrate_guardrail_policy

SettingsMapping = Mapping[str, Any]
SettingsMigrator = Callable[[dict[str, Any]], dict[str, Any] | None]
LogPathResolver = Callable[[dict[str, Any], str], str]


class SettingsStore:
    """JSON-backed settings with platform behavior supplied as callbacks."""

    def __init__(
        self,
        path: str | Path,
        defaults: SettingsMapping,
        *,
        known_profiles: Collection[str] = (),
        migrate: SettingsMigrator | None = None,
        resolve_log_path: LogPathResolver | None = None,
    ) -> None:
        self.path = Path(path)
        self.defaults = copy.deepcopy(dict(defaults))
        self.known_profiles = set(known_profiles)
        self.migrate = migrate
        self.resolve_log_path = resolve_log_path

    def load(self) -> RoleWeaverSettings:
        """Load current settings, preserve extension keys and apply defaults."""

        if not self.path.exists():
            self.save(self.defaults)
        loaded = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("settings.json must contain a JSON object")
        if self.migrate:
            loaded = self.migrate(loaded) or loaded
        loaded = migrate_guardrail_policy(loaded)

        merged = copy.deepcopy(self.defaults)
        merged.update(loaded)

        default_paths = self.defaults.get("server_log_paths", {})
        saved_paths = loaded.get("server_log_paths", {})
        paths = dict(default_paths) if isinstance(default_paths, Mapping) else {}
        if isinstance(saved_paths, Mapping):
            paths.update(saved_paths)
        if "server_log_paths" not in loaded and loaded.get("log_path"):
            paths["AUTO"] = str(loaded["log_path"])
        merged["server_log_paths"] = paths

        discovered = merged.get("discovered_servers")
        if not isinstance(discovered, dict):
            discovered = {}
            merged["discovered_servers"] = discovered

        selected = str(merged.get("server_profile") or "AUTO")
        if selected not in self.known_profiles and selected not in discovered:
            legacy_path = (
                paths.get(selected) or loaded.get("log_path") or merged.get("log_path", "")
            )
            discovered[selected] = {
                "display_name": selected,
                "log_path": str(legacy_path),
                "parser_profile": "adaptive",
                "last_seen": "",
            }

        if self.resolve_log_path:
            merged["log_path"] = self.resolve_log_path(merged, selected)
        return merged

    def save(self, settings: SettingsMapping) -> None:
        """Persist a complete settings snapshot atomically."""

        atomic.atomic_write_text(
            self.path,
            json.dumps(dict(settings), indent=2),
            encoding="utf-8",
        )
