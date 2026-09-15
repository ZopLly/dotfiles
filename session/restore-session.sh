#!/usr/bin/env bash

set -euo pipefail

SESSION_FILE="$HOME/.local/state/niri-session/session.json"

if [[ ! -f "$SESSION_FILE" ]]; then
    exit 0
fi

if ! command -v fuzzel >/dev/null 2>&1; then
    exit 1
fi

CHOICE=$(printf 'Restore previous session\nStart fresh\n' |
    fuzzel --dmenu --prompt="Session: ")

case "$CHOICE" in
    "Restore previous session")
        ;;
    *)
        exit 0
        ;;
esac


wait_for_window() {
    local app="$1"
    local old_ids="$2"

    for _ in {1..40}; do
        while IFS=$'\t' read -r ID APP; do
            [[ -z "$ID" ]] && continue

            if [[ "$APP" == "$app" ]] &&
               ! grep -qx "$ID" <<< "$old_ids"; then
                echo "$ID"
                return 0
            fi
        done < <(
            niri msg -j windows |
                jq -r '.[] | [.id, .app_id] | @tsv'
        )

        sleep 0.25
    done

    return 1
}


spawn_app() {
    case "$1" in
        Alacritty)
            niri msg action spawn -- alacritty
            ;;

        firefox)
            niri msg action spawn -- firefox --new-window
            ;;

        Happ)
            niri msg action spawn -- happ
            ;;

        *)
            return 1
            ;;
    esac
}


mapfile -t ENTRIES < <(
    jq -r '
        .[]
        | [.app_id, .workspace, .column]
        | @tsv
    ' "$SESSION_FILE"
)


for entry in "${ENTRIES[@]}"; do
    IFS=$'\t' read -r APP WORKSPACE COLUMN <<< "$entry"

    OLD_IDS=$(
        niri msg -j windows |
            jq -r '.[].id'
    )

    if ! spawn_app "$APP"; then
        echo "Skipping unknown application: $APP"
        continue
    fi

    WINDOW_ID=$(wait_for_window "$APP" "$OLD_IDS") || {
        echo "Could not find new window: $APP"
        continue
    }

    niri msg action focus-window --id "$WINDOW_ID"

    niri msg action move-column-to-workspace \
        "$WORKSPACE"

    niri msg action move-column-to-index \
        "$COLUMN"
done
