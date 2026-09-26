"""Game selection and conservative NWN2 log normalization."""

import copy
import os
import re
import sys
from pathlib import Path

__all__ = [
    "GAME_FIELDS",
    "GAME_VERSIONS",
    "default_game_log",
    "discover_game_logs",
    "game_directories",
    "parse_nwn2",
    "switch_game",
]

GAME_VERSIONS = {
    "nwn_ee": "NWN: Enhanced Edition",
    "nwn": "NWN Original (1.69)",
    "nwn_diamond": "NWN Diamond Edition",
    "nwn2": "Neverwinter Nights 2",
    "nwn2_ee": "NWN2: Enhanced Edition / modded EE",
    "nwn2_ce": "NWN2 + Client Extender",
}
GAME_FIELDS = (
    "server_profile",
    "log_path",
    "server_log_paths",
    "discovered_servers",
    "parser_profile",
    "window_title_contains",
)


def game_directories(game, home=None, environ=None, platform=None):
    home = Path(home or Path.home())
    env = os.environ if environ is None else environ
    system = platform or sys.platform
    linux = system.startswith("linux")
    nwn2 = game.startswith("nwn2")
    if system == "darwin":
        if game == "nwn_ee":
            roots = [
                home / "Documents/Neverwinter Nights/logs",
                home / "Library/Application Support/Neverwinter Nights/logs",
            ]
            if env.get("NWN_USER_DIRECTORY"):
                roots.insert(0, Path(env["NWN_USER_DIRECTORY"]).expanduser() / "logs")
            return roots
        if not nwn2:
            return [home / "Documents/Neverwinter Nights/logs"]
        return [home / "Documents/Neverwinter Nights 2/Logs"]
    if not linux:
        if game == "nwn_ee":
            return [home / "Documents/Neverwinter Nights/logs"]
        if not nwn2:
            return [
                Path(env.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
                / "Neverwinter Nights/logs",
                Path("C:/NeverwinterNights/NWN/logs"),
                Path("C:/GOG Games/Neverwinter Nights Diamond/logs"),
            ]
        temp = Path(env.get("TEMP") or str(home / "AppData/Local/Temp")) / "NWN2/LOGS"
        ce = home / "Documents/Neverwinter Nights 2/Logs"
        paths = [temp, home / "AppData/Local/Temp/NWN2/LOGS"]
        if game == "nwn2_ee":
            ee = [
                Path(env.get("TEMP") or str(home / "AppData/Local/Temp")) / "NWN2 EE",
                home / "AppData/Local/Temp/NWN2 EE",
            ]
            return ee + [p / "LOGS" for p in ee] + paths + [ce]
        return [ce] + paths if game == "nwn2_ce" else paths + [ce]
    if game == "nwn_ee":
        roots = [
            home / ".local/share/Neverwinter Nights/logs",
            home / ".var/app/com.valvesoftware.Steam/.local/share/Neverwinter Nights/logs",
        ]
        if env.get("NWN_USER_DIRECTORY"):
            roots.insert(0, Path(env["NWN_USER_DIRECTORY"]).expanduser() / "logs")
        return roots
    roots = (
        []
        if nwn2
        else [
            home / "nwn/logs",
            home / "Neverwinter Nights/logs",
            home / "GOG Games/Neverwinter Nights Diamond/logs",
        ]
    )
    prefixes = [Path(env.get("WINEPREFIX", str(home / ".wine"))).expanduser()]
    if env.get("STEAM_COMPAT_DATA_PATH"):
        prefixes.insert(0, Path(env["STEAM_COMPAT_DATA_PATH"]) / "pfx")
    for steam in (
        home / ".steam/steam",
        home / ".local/share/Steam",
        home / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
    ):
        prefixes.extend(list((steam / "steamapps/compatdata").glob("*/pfx"))[:200])
    for prefix in dict.fromkeys(prefixes):
        if not nwn2:
            roots.extend(
                [
                    prefix / "drive_c/Program Files (x86)/Neverwinter Nights/logs",
                    prefix / "drive_c/GOG Games/Neverwinter Nights Diamond/logs",
                ]
            )
            continue
        users = prefix / "drive_c/users"
        names = (
            list(users.iterdir()) if users.is_dir() else [users / "steamuser", users / home.name]
        )
        for user in names:
            ce = user / "Documents/Neverwinter Nights 2/Logs"
            temp = user / "AppData/Local/Temp/NWN2/LOGS"
            if game == "nwn2_ee":
                ee = user / "AppData/Local/Temp/NWN2 EE"
                roots.extend([ee, ee / "LOGS"])
            roots.extend([ce, temp] if game == "nwn2_ce" else [temp, ce])
            roots.append(user / "Local Settings/Temp/NWN2/LOGS")
    return list(dict.fromkeys(roots))


def default_game_log(game, **kwargs):
    roots = game_directories(game, **kwargs)
    return str(roots[0] / "nwclientLog1.txt")


def discover_game_logs(settings, max_files=20):
    explicit = [settings.get("log_path", "")] + list(
        (settings.get("server_log_paths") or {}).values()
    )
    candidates = [Path(p).expanduser() for p in explicit if p]
    for directory in game_directories(settings.get("game_version", "nwn_ee")):
        patterns = (
            "nwn2client64Log*.txt",
            "nwn2client64log*.txt",
            "nwclientLog*.txt",
            "nwclientlog*.txt",
            "*.log",
            "*/*.txt",
            "*/*.log",
            "*/*/*.txt",
            "*/*/*.log",
        )
        if "Neverwinter Nights 2" in str(directory):
            patterns += ("*.txt",)
        for pattern in patterns:
            candidates.extend(list(directory.glob(pattern))[:500])
    found = {}
    for path in candidates:
        try:
            if path.is_file() and not any("combat" in part.casefold() for part in path.parts):
                found[str(path)] = (path.stat().st_mtime, path)
        except OSError:
            continue
    return [
        p for _, p in sorted(found.values(), key=lambda item: item[0], reverse=True)[:max_files]
    ]


def switch_game(settings, game):
    if game not in GAME_VERSIONS:
        raise ValueError("Unknown game version")
    result = copy.deepcopy(settings)
    previous = result.get("game_version", "nwn_ee")
    profiles = result.setdefault("game_profiles", {})
    profiles[previous] = {key: copy.deepcopy(result[key]) for key in GAME_FIELDS if key in result}
    path = default_game_log(game)
    fresh = dict(
        server_profile="AUTO",
        log_path=path,
        server_log_paths={"AUTO": path},
        discovered_servers={},
        parser_profile="adaptive",
        window_title_contains="Neverwinter Nights 2"
        if game.startswith("nwn2")
        else "Neverwinter Nights",
    )
    fresh.update(copy.deepcopy(profiles.get(game, {})))
    result.update(fresh)
    result["game_version"] = game
    return result


CHANNEL = r"Talk|Whisper|Party|Tell|Shout|DM"
NWN2_PATTERNS = [
    re.compile(
        r"^\[(?P<channel>" + CHANNEL + r")\]\s*(?P<speaker>[^:]{1,120}):\s*(?P<message>.+)$", re.I
    ),
    re.compile(
        r"^(?P<speaker>[^:]{1,120}):\s*\[(?P<channel>" + CHANNEL + r")\]\s*(?P<message>.+)$", re.I
    ),
    re.compile(
        r"^(?P<speaker>[^:\[]{1,120})\s*\[(?P<channel>" + CHANNEL + r")\]\s*:\s*(?P<message>.+)$",
        re.I,
    ),
]


def parse_nwn2(raw, character_name, server_profile, build_event):
    raw = re.sub(r"^\[CHAT WINDOW TEXT\]\s*", "", raw, flags=re.I)
    raw = re.sub(r"^\[(?:\d{4}[-/]\d{2}[-/]\d{2}[ T])?\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\]\s*", "", raw)
    for pattern in NWN2_PATTERNS:
        match = pattern.match(raw)
        if not match:
            continue
        speaker, message, channel = match.group("speaker", "message", "channel")
        recipient = ""
        if channel.casefold() in ("tell", "whisper"):
            direction = re.match(r"^(To|From)\s+(.+)$", speaker, re.I)
            if direction:
                if direction[1].casefold() == "to":
                    recipient, speaker = direction[2], character_name
                else:
                    speaker = direction[2]
        event = build_event(speaker, message, channel, character_name, server_profile)
        if event and recipient:
            event["recipient"] = recipient
        return event
    return None
