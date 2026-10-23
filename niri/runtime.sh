#!/usr/bin/env bash
set -euo pipefail
script=$(readlink -f -- "${BASH_SOURCE[0]}")
root=$(cd -- "$(dirname -- "$script")/.." && pwd -P)
action=${1:?Missing runtime action}
shift
case "$action" in
    terminal) exec alacritty --config-file "$root/alacritty/niri.toml" ;;
    launcher) exec qs ipc -p "$root/quickshell" call -- applications menu ;;
    settings) exec qs ipc -p "$root/quickshell" call -- applications act settings - ;;
    chatgpt) exec qs ipc -p "$root/quickshell" call -- applications act launch chatgpt.desktop ;;
    vpn) exec qs ipc -p "$root/quickshell" call -- applications act launch Happ.desktop ;;
    shell-start) exec qs -n -p "$root/quickshell" ;;
    panel|edit) exec qs ipc -p "$root/quickshell" call shell "$action" "$@" ;;
    theme) exec "$root/scripts/theme-switcher.sh" "$@" ;;
    wallpaper) exec "$root/scripts/wallpaper.sh" ;;
    blur) exec "$root/gtklock/scripts/blur-background.sh" ;;
    lock) exec "$root/gtklock/scripts/lock.sh" "$@" ;;
    session) exec python3 "$root/session/session-manager.py" ;;
    *) printf 'Unknown runtime action: %s\n' "$action" >&2; exit 2 ;;
esac
