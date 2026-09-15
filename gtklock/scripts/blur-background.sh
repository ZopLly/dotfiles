#!/bin/bash

set -e

SOURCE="$HOME/dotfiles/assets/wallpapers/wallpaper.jpg"
OUTPUT="$HOME/.cache/gtklock-blurred.jpg"

mkdir -p "$HOME/.cache"

magick "$SOURCE" \
	-resize '100%x100%' \
	-blur 0x25 \
	-brightness-contrast -8x-5 \
	-quality 90 \
	"$OUTPUT"
printf '%s\n' "$OUTPUT"
	
