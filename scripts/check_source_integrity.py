"""Catch damaged source text and drift in mirrored desktop-client logic."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These functions depend on the operating system or its input tools.
PLATFORM_DIFFERENCES = frozenset(
    {
        "NWNAIBot.__init__",
        "NWNAIBot.action_worker",
        "NWNAIBot.afk_available",
        "NWNAIBot.console_listener",
        "NWNAIBot.generate_and_send",
        "NWNAIBot.hotkey_listener",
        "NWNAIBot.keyboard_test",
        "NWNAIBot.paste_existing_draft",
        "NWNAIBot.run_all_keyboard_tests",
        "_settings_store",
        "discover_nwn_log_files",
        "main",
    }
)

WINDOWS_ONLY_FUNCTIONS = frozenset(
    {
        "_send_key_event",
        "_send_scancode",
        "find_window_handle",
        "focus_nwn_window",
        "get_foreground_window_title",
        "manual_focus_countdown",
        "paste_with_hotkeys",
        "press_ctrl_v_keybd_event",
        "press_ctrl_v_scancode",
        "press_ctrl_v_sendinput",
        "press_enter_keybd_event",
        "press_enter_postmessage",
        "press_scancode",
        "press_windows_key",
        "send_chat_to_nwn",
        "type_unicode_sendinput",
    }
)

SUSPICIOUS_TEXT = re.compile(r"\u00c3\S|\u00c2\S|\u00e2\u20ac|\ufffd")


def _source_paths(root: Path) -> list[Path]:
    return sorted(
        [
            *root.glob("*.py"),
            *(root / "linux").glob("*.py"),
            *(root / "src").rglob("*.py"),
            *(root / "scripts").glob("*.py"),
        ]
    )


def _functions(source: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef):
            functions.update(
                {
                    f"{cls.name}.{node.name}": node
                    for node in cls.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
            )
    return functions


def check_source_integrity(root: Path = ROOT) -> list[str]:
    """Return actionable errors; an empty list means source files agree."""

    errors = []
    sources = {}
    for path in _source_paths(root):
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            errors.append(f"{path.relative_to(root)}: invalid UTF-8: {exc}")
            continue
        sources[path.relative_to(root).as_posix()] = source
        for number, line in enumerate(source.splitlines(), 1):
            if SUSPICIOUS_TEXT.search(line):
                errors.append(f"{path.relative_to(root)}:{number}: possible mojibake")

    windows = sources.get("nwn_ai_bot.py")
    linux = sources.get("linux/nwn_ai_bot.py")
    if windows is None or linux is None:
        errors.append("Both nwn_ai_bot.py entry points are required for parity checking.")
        return errors
    try:
        windows_functions = _functions(windows)
        linux_functions = _functions(linux)
    except SyntaxError as exc:
        errors.append(f"Could not compare bot entry points: {exc}")
        return errors

    for name in sorted(windows_functions.keys() & linux_functions.keys()):
        if name not in PLATFORM_DIFFERENCES and ast.dump(
            windows_functions[name]
        ) != ast.dump(linux_functions[name]):
            errors.append(f"Mirrored function differs: {name}")
    unexpected_windows = windows_functions.keys() - linux_functions.keys() - WINDOWS_ONLY_FUNCTIONS
    for name in sorted(unexpected_windows):
        errors.append(f"Function exists only in Windows bot: {name}")
    for name in sorted(linux_functions.keys() - windows_functions.keys()):
        errors.append(f"Function exists only in Linux bot: {name}")
    return errors


if __name__ == "__main__":
    findings = check_source_integrity()
    for finding in findings:
        print(finding)
    if findings:
        raise SystemExit(1)
    print("Source encoding and platform parity checks passed.")
