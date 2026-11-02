#!/usr/bin/env bash
set -euo pipefail
cache="${XDG_CACHE_HOME:-$HOME/.cache}/eww/covers"
mkdir -p "$cache"
url=$(playerctl metadata mpris:artUrl 2>/dev/null) || { echo ''; exit 0; }
case "$url" in
    file://*) printf '%s\n' "${url#file://}" ;;
    https://*|http://*)
        hash=$(printf '%s' "$url" | sha256sum | cut -d' ' -f1)
        cover="$cache/$hash"
        if [[ ! -s "$cover" ]]; then
            temp=$(mktemp "$cache/.download.XXXXXX")
            trap 'rm -f "$temp"' EXIT
            curl --fail --location --silent --show-error --max-time 10 --proto '=http,https' --proto-redir '=http,https' "$url" -o "$temp" || { echo ''; exit 0; }
            mv -- "$temp" "$cover"
        fi
        printf '%s\n' "$cover" ;;
    *) echo '' ;;
esac
