#!/usr/bin/env bash
set -euo pipefail
root=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && cd ../.. && pwd -P)
if [[ -f "$root/quickshell/appearance/wallpaper_start.py" ]]; then
    source=$(python3 "$root/quickshell/appearance/wallpaper_start.py")
else
    source=$(find -L "$root/assets/themes/current" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.gif' -o -name '*.webp' \) -print -quit)
fi
[[ -n "$source" ]] || { echo 'No selected wallpaper' >&2; exit 1; }
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$cache_dir"
signature=$(sha256sum "$source" | cut -d' ' -f1)
output="$cache_dir/gtklock-wallpaper-$signature.jpg"
signature="minimal-v1:$signature"
if [[ -s "$output" && -f "$output.signature" && "$(cat "$output.signature")" == "$signature" ]]; then
    printf '%s\n' "$output"; exit 0
fi
temp=$(mktemp "$cache_dir/.gtklock-minimal.XXXXXX.jpg")
trap 'rm -f "$temp"' EXIT
# Static, moderate blur; GIF's first frame avoids processing an animation.
magick "${source}[0]" -resize '2560x1440>' -blur 0x12 -brightness-contrast -5x-2 -quality 88 "$temp"
mv -- "$temp" "$output"
printf '%s\n' "$signature" > "$output.signature"
printf '%s\n' "$output"
