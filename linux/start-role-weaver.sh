#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
umask 077
if [[ ! -x .venv/bin/python ]]; then
    echo 'Run bash install-linux.sh first. See INSTALL_LINUX.md.' >&2
    exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
exec .venv/bin/python linux_start.py "$@"
