#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
themes="$root/assets/themes"
# The checkout is editable staging, not a deployed desktop.
if [[ -d "$root/.git" ]]; then
    echo 'Theme switching is available only in an installed snapshot.' >&2
    exit 1
fi
selected=${1:-}
if [[ -z "$selected" ]]; then
    selected=$(find "$themes" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort | fuzzel --dmenu -p '🎨 Выберите тему: ') || exit 0
fi
[[ -n "$selected" ]] || exit 0
case "$selected" in catppuccin-mocha|gruvbox-dark|tokyo-night|ancient-odyssey) ;; *) echo 'Unknown theme' >&2; exit 2 ;; esac
old=$(readlink "$themes/current")
# Validate a candidate include without changing the active theme first.
candidate=$(mktemp "$root/niri/.theme-check.XXXXXX.kdl")
link="$themes/.current-$$"
trap 'rm -f "$candidate" "$link"' EXIT
python3 "$root/scripts/niri_config.py" --theme "$selected" "$root/niri/config.kdl" > "$candidate"
niri validate -c "$candidate"
ln -s "$selected" "$link"
mv -Tf "$link" "$themes/current"
if ! niri validate -c "$root/niri/config.kdl"; then
    ln -s "$old" "$link"
    mv -Tf "$link" "$themes/current"
    exit 1
fi
failed=0
refresh() { "$@" || { printf 'Failed: %s\n' "$*" >&2; failed=1; }; }
refresh "$root/scripts/wallpaper.sh"
if [[ -f "$themes/$selected/gtk-theme.txt" ]]; then
    gtk_theme=$(<"$themes/$selected/gtk-theme.txt")
    refresh gsettings set org.gnome.desktop.interface gtk-theme "$gtk_theme"
fi
refresh gsettings set org.gnome.desktop.interface color-scheme prefer-dark
if pgrep -x waybar >/dev/null; then refresh pkill -SIGUSR2 -x waybar; fi
if pgrep -x eww >/dev/null; then
    eww_config="$root/eww"
    [[ -d "$eww_config" ]] || eww_config="$root/legacy/eww"
    refresh eww --config "$eww_config" reload
fi
if pgrep -x mako >/dev/null; then refresh makoctl reload; fi
refresh "$root/gtklock/scripts/blur-background.sh"
# Fuzzel reads the selected theme on its next launch.
# Niri watches includes. Alacritty is explicitly nudged after changing the symlink.
touch "$root/alacritty/alacritty.toml"
if (( failed )); then
    notify-send 'Тема изменена частично' 'См. ошибки переключателя в журнале.' || true
    exit 1
fi
notify-send 'Тема изменена' "$selected" || true
