#!/usr/bin/env bash
set -euo pipefail
root=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && cd ../.. && pwd -P)
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$cache_dir"
exec >>"$cache_dir/gtklock.log" 2>&1
# Serialize manual, idle and before-sleep requests until gtklock is ready.
# Do not pass this descriptor to gtklock: its daemon must not retain the mutex.
exec 9>"${XDG_RUNTIME_DIR:?Missing session runtime directory}/niri-gtklock.lock"
flock 9
if pgrep -u "$UID" -x gtklock >/dev/null; then
    exit 0
fi
# Never delay the sleep inhibitor for expensive image processing.
background=""
# Independent wallpaper choice; only read a prepared cache or the original image.
# Failure is cosmetic: it must never prevent acquiring the session lock.
if [[ -f "$root/quickshell/appearance/wallpaper_start.py" ]]; then
    background=$(python3 "$root/quickshell/appearance/wallpaper_start.py" --lock-background) || background=""
fi
if [[ -z "$background" ]]; then
    background=$(find -L "$root/assets/themes/current" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.gif' -o -name '*.webp' \) -print -quit) || background=""
fi
style="$root/gtklock/style.css"
[[ ! -f "$root/assets/themes/current/gtklock.css" ]] || style="$root/assets/themes/current/gtklock.css"
# --daemonize returns after acquiring the session lock, rather than after unlock.
# Accept the former caller flag for compatibility, but supply it only once.
args=()
for arg in "$@"; do
    [[ "$arg" == '--daemonize' || "$arg" == '-d' ]] || args+=("$arg")
done
# The optional display-only module has an explicit gtklock 4 ABI guard.
module="$root/gtklock/modules/minimal-module.so"
if [[ -s "$module" && "$(gtklock --version)" == 'gtklock v4.0.'* ]]; then
    args+=(--modules "$module")
fi
module="$root/gtklock/modules/notifications-module.so"
if [[ -s "$module" && "$(gtklock --version)" == 'gtklock v4.0.'* ]]; then
    args+=(--modules "$module")
fi
module="$root/gtklock/modules/layout-module.so"
if [[ -s "$module" && "$(gtklock --version)" == 'gtklock v4.0.'* ]]; then
    args+=(--modules "$module")
fi
args+=(--layout "$root/gtklock/layout.xml")
# Missing artwork must never prevent a real session lock.
[[ -r "$background" && -s "$background" ]] && args+=(--background "$background")
gtklock --daemonize --config "$root/gtklock/config.ini" --style "$style" "${args[@]}" 9>&-
