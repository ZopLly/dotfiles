#!/usr/bin/env bash
set -euo pipefail
state="${XDG_STATE_HOME:-$HOME/.local/state}/niri-session"
mkdir -p "$state"
temp=$(mktemp "$state/.session.XXXXXX")
trap 'rm -f "$temp"' EXIT
workspaces=$(niri msg -j workspaces)
niri msg -j windows | jq --argjson workspaces "$workspaces" '{version: 2, windows: [
    .[] | . as $window |
    ($workspaces[] | select(.id == $window.workspace_id)) as $workspace |
    {app_id, workspace: ($workspace.name // ($workspace.idx | tostring)),
     output: $workspace.output,
     column: (.layout.pos_in_scrolling_layout[0] // null)}
]}' > "$temp"
mv -- "$temp" "$state/session.json"
echo "Session saved: $state/session.json"
