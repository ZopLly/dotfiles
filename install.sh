#!/bin/bash

success() {
	echo -e "\033[0;32m ✓ $1\033[0m"
}
error() {
	echo -e "\033[0:31mx $1\033[0m"
}
warning() {
	echo -e "\033[0;33m!!$1\033[0m"
}



set -e



DOTFILES="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$HOME/.config"



echo "Installing dotfiles"
echo "Source: $DOTFILES"



create_link() {

    local source=$1
    local target=$2

    if [ -L "$target" ]; then

	    echo "Removing old symlink: $target"
	    rm "$target"
    
    elif [ -e "$target" ]; then

	    echo "Backing up existing file: $target"
	    mv "$target" "$target.backup"
    fi

    ln -s "$source" "$target"

    success "Linked:"
    echo "  $target -> $source"
}



echo "Creating directories..."
mkdir -p \
"$CONFIG/niri" \
"$CONFIG/kitty" \
"$CONFIG/waybar" \
"$CONFIG/fuzzel" \
"$CONFIG/mako"



echo
echo "Creating links..."

create_link \
"$DOTFILES/niri/config.kdl" \
"$CONFIG/niri/config.kdl"

create_link \
"$DOTFILES/kitty/kitty.conf" \
"$CONFIG/kitty/kitty.conf"

create_link \
"$DOTFILES/waybar/config.jsonc" \
"$CONFIG/waybar/config.jsonc"

create_link \
"$DOTFILES/waybar/style.css" \
"$CONFIG/waybar/style.css"

create_link \
"$DOTFILES/fuzzel/fuzzel.ini" \
"$CONFIG/fuzzel/fuzzel.ini"

create_link \
"$DOTFILES/mako/config" \
"$CONFIG/mako/config"

echo "linked: $DOTFILES" 
