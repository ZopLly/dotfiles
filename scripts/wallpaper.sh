#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
wallpaper=$(python3 "$root/quickshell/appearance/wallpaper_start.py")
[[ -n "$wallpaper" ]] || { echo "No wallpaper in the selected desktop theme" >&2; exit 1; }
command -v awww >/dev/null
if ! awww query >/dev/null 2>&1; then
    awww-daemon &
    for _ in {1..40}; do
        if awww query >/dev/null 2>&1; then break; fi
        sleep 0.1
    done
fi
# A listening socket can precede output registration. Wait for an actual screen.
ready=false
for _ in {1..50}; do
    status=$(awww query 2>/dev/null) || status=''
    if [[ "$status" == *"currently displaying:"* ]]; then ready=true; break; fi
    sleep 0.1
done
[[ "$ready" == true ]] || { echo "awww: no configured output" >&2; exit 1; }
awww img --transition-type none "$wallpaper"
