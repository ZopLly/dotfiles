#!/bin/bash

exec >>"$HOME/.cache/gtklock.log" 2>&1

echo "=== LOCK START $(date) ==="

"$HOME/dotfiles/gtklock/scripts/blur-background.sh"

echo "Starting gtklock..."

exec gtklock \
    --background="$HOME/.cache/gtklock-blurred.jpg"
