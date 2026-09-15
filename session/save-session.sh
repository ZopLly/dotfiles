#!/usr/bin/env bash

set -euo pipefail

SESSION_DIR="$HOME/.local/state/niri-session"
SESSION_FILE="$SESSION_DIR/session.json"

mkdir -p "$SESSION_DIR"

niri msg -j windows | jq '[
    .[] |
    {
        app_id,
        title,
        workspace: .workspace_id,
        column: .layout.pos_in_scrolling_layout[0]
    }
]' > "$SESSION_FILE"

echo "Session saved: $SESSION_FILE"
