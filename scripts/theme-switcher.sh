#!/usr/bin/env bash

# ==============================================================================
# Monolithic Theme Switcher for Niri, Waybar, Eww, Alacritty, Mako, Cava, GTK & Awww
# ==============================================================================

DOTFILES="$HOME/dotfiles"
THEMES_DIR="$DOTFILES/assets/themes"
CURRENT_LINK="$THEMES_DIR/current"

# ------------------------------------------------------------------------------
# 1. Меню выбора темы (Fuzzel)
# ------------------------------------------------------------------------------
SELECTED_THEME=$(find "$THEMES_DIR" -maxdepth 1 -mindepth 1 -type d ! -name "current" -exec basename {} \; | sort | fuzzel --dmenu -p "🎨 Выберите тему: ")

# Выход, если пользователь закрыл меню
if [ -z "$SELECTED_THEME" ]; then
    exit 0
fi

TARGET_DIR="$THEMES_DIR/$SELECTED_THEME"

if [ ! -d "$TARGET_DIR" ]; then
    notify-send "Theme Switcher" "Ошибка: папка $SELECTED_THEME не найдена"
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Мгновенное переключение единого симлинка 'current'
# ------------------------------------------------------------------------------
ln -sfn "$TARGET_DIR" "$CURRENT_LINK"

# ------------------------------------------------------------------------------
# 3. Обои (Awww)
# ------------------------------------------------------------------------------
WALLPAPER=$(find "$TARGET_DIR" -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.webp" \) | head -n 1)

if [ -n "$WALLPAPER" ]; then
    if command -v awww &>/dev/null; then
        awww img "$WALLPAPER" 2>/dev/null
    fi
fi

# ------------------------------------------------------------------------------
# 4. GTK & Libadwaita (Цветовая схема и темы)
# ------------------------------------------------------------------------------
# Проверяем, есть ли кастомное название GTK темы в папке с темой
if [ -f "$TARGET_DIR/gtk-theme.txt" ]; then
    GTK_THEME=$(cat "$TARGET_DIR/gtk-theme.txt" | xargs)
    gsettings set org.gnome.desktop.interface gtk-theme "$GTK_THEME" 2>/dev/null || true
fi

# Устанавливаем светлый/темный режим для GTK/Qt/VSCode/Браузеров
if [[ "$SELECTED_THEME" == *"light"* ]]; then
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-light' 2>/dev/null || true
else
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 5. Перезагрузка и горячее обновление демонов
# ------------------------------------------------------------------------------

# Mako (Уведомления)
if pgrep -x "mako" > /dev/null; then
    makoctl reload 2>/dev/null || true
fi

# Cava (Аудио визуализатор)
if pgrep -x "cava" > /dev/null; then
    pkill -USR1 cava 2>/dev/null || true
fi

# Waybar (Статус-бар)
if pgrep -x "waybar" > /dev/null; then
    pkill -SIGUSR2 waybar 2>/dev/null || true
fi

# Eww (Виджеты)
if command -v eww &>/dev/null; then
    eww reload 2>/dev/null || true
fi

# Niri (Оконный менеджер)
if command -v niri &>/dev/null && pgrep -x "niri" > /dev/null; then
    niri msg action reload-config 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 6. Системное уведомление
# ------------------------------------------------------------------------------
if command -v notify-send &>/dev/null; then
    notify-send -u low -i preferences-desktop-theme "Theme Switcher" "Тема успешно изменена на <b>$SELECTED_THEME</b>"
fi
# ------------------------------------------------------------------------------
# 7. Niri (Автоматическая замена цвета рамки фокуса в config.kdl)
# ------------------------------------------------------------------------------
NIRI_CONF="$HOME/.config/niri/config.kdl"

if [ -f "$NIRI_CONF" ]; then
    case "$SELECTED_THEME" in
        "gruvbox-dark")      ACCENT="#fe8019" ;;
        "catppuccin-mocha")  ACCENT="#89b4fa" ;;
        "tokyo-night")       ACCENT="#7aa2f7" ;;
        *)                   ACCENT="#89b4fa" ;;
    esac

    # Меняем значение active-color в файле config.kdl
    sed -i -E "s/(active-color|active-gradient)[[:space:]]+\"[^\"]+\"/\1 \"$ACCENT\"/g" "$NIRI_CONF"
fi
# ------------------------------------------------------------------------------
# 8. Alacritty Theme Switch
# ------------------------------------------------------------------------------
# Привязываем theme.toml к теме
ln -sfn "$HOME/dotfiles/assets/themes/$SELECTED_THEME/alacritty.toml" "$HOME/.config/alacritty/theme.toml"

# Принудительно обновляем дату файла, чтобы inotify разбудил открытые терминалы
touch "$HOME/.config/alacritty/alacritty.toml"
