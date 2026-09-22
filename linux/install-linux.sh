#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
umask 077
if [[ "$(uname -s)" != Linux ]]; then
    echo 'This installer requires Linux.' >&2
    exit 1
fi
if [[ "$(id -u)" == 0 ]]; then
    echo 'Run this installer as your normal desktop user, without sudo.' >&2
    exit 1
fi
command -v python3 >/dev/null || { echo 'Install Python 3.10-3.13; see INSTALL_LINUX.md.' >&2; exit 1; }
python3 -c 'import sys; assert (3, 10) <= sys.version_info < (3, 14), "Python 3.10-3.13 is required"; import tkinter'
tools=(xdotool xclip)
if [[ -n "${WAYLAND_DISPLAY:-}" || "${XDG_SESSION_TYPE:-}" == wayland ]]; then
    tools=(wl-copy)
fi
for tool in "${tools[@]}"; do
    command -v "$tool" >/dev/null || { echo "Install $tool; see INSTALL_LINUX.md." >&2; exit 1; }
done
python3 -m venv .venv
package_root='.'
if [[ ! -f pyproject.toml && -f ../pyproject.toml ]]; then
    package_root='..'
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e "$package_root"
echo 'Installation complete. Start with: bash start-role-weaver.sh'
