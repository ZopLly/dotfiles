#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
interpreter="${XDG_DATA_HOME:-$HOME/.local/share}/niri-shell/calendar-venv/bin/python"
[[ -x "$interpreter" ]] || interpreter=python3
exec "$interpreter" "$root/calendar_service.py"
