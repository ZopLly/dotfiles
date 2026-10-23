#!/usr/bin/env bash
set -euo pipefail
# Official Arch packages only; no AUR helpers or downloaded build scripts.
command -v pacman >/dev/null || { echo 'Supported systems: Arch Linux, EndeavourOS and CachyOS.' >&2; exit 1; }
(( EUID != 0 )) || { echo 'Run this installer as your regular desktop user.' >&2; exit 1; }
packages=(niri quickshell gtklock swayidle awww alacritty fuzzel mako imagemagick
    playerctl wireplumber pamixer brightnessctl cava curl libnotify glib2 gtk3
    pavucontrol network-manager-applet networkmanager blueman bluez-utils libpulse
    python python-gobject python-pillow python-icalendar python-recurring-ical-events
    gcc pkgconf jq firefox ttf-jetbrains-mono-nerd xwayland-satellite
    xdg-desktop-portal xdg-desktop-portal-gnome)
sudo pacman -S --needed "${packages[@]}" </dev/tty
