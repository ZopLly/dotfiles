#!/usr/bin/env bash
# Optional dependencies for Google Calendar, separate from system Python.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
venv="${XDG_DATA_HOME:-$HOME/.local/share}/niri-shell/calendar-venv"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install -r "$root/quickshell/calendar-requirements.txt"
printf '%s\n' 'Calendar libraries installed. Restart Quickshell or log in again.'
