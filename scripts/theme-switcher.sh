#!/bin/bash

# 1. Пути к папкам
THEMES_DIR="$HOME/dotfiles/assets/themes"
CURRENT_LINK="$THEMES_DIR/current"

# 2. Если аргумент не передан, запрашиваем тему через Fuzzel
SELECTED_THEME="$1"

if [ -z "$SELECTED_THEME" ]; then
    # Находим все папки в THEMES_DIR, убираем путь и папку 'current', передаем в fuzzel
    SELECTED_THEME=$(ls -d $THEMES_DIR/*/ | xargs -n 1 basename | grep -v "^current$" | fuzzel --dmenu -p "Выберите тему: ")
fi

# Если пользователь закрыл Fuzzel (нажал Esc), ничего не делаем
if [ -z "$SELECTED_THEME" ]; then
    echo "Отмена выбора темы."
    exit 0
fi

NEW_THEME="$THEMES_DIR/$SELECTED_THEME"

# 3. Проверяем, существует ли выбранная тема
if [ ! -d "$NEW_THEME" ]; then
    echo "Ошибка: Тема '$SELECTED_THEME' не найдена в $THEMES_DIR"
    exit 1
fi

# 4. Переключаем симлинк на новую тему
rm -f "$CURRENT_LINK"
ln -s "$NEW_THEME" "$CURRENT_LINK"

echo "Тема переключена на: $SELECTED_THEME"

# 5. Ищем и устанавливаем обои через awww
if [ -f "$CURRENT_LINK/wallpaper.gif" ]; then
    awww img "$CURRENT_LINK/wallpaper.gif" --transition-type outer
elif [ -f "$CURRENT_LINK/wallpaper.png" ]; then
    awww img "$CURRENT_LINK/wallpaper.png" --transition-type outer
elif [ -f "$CURRENT_LINK/wallpaper.jpg" ]; then
    awww img "$CURRENT_LINK/wallpaper.jpg" --transition-type outer
elif [ -f "$CURRENT_LINK/wallpaper.jpeg" ]; then
    awww img "$CURRENT_LINK/wallpaper.jpeg" --transition-type outer
else
    echo "Предупреждение: Файл обоев не найден в папке темы!"
fi

# 6. Обновляем конфиги приложений
touch "$HOME/.config/alacritty/alacritty.toml" 2>/dev/null
touch "$HOME/.config/waybar/style.css" 2>/dev/null
pkill -SIGUSR2 waybar
niri msg action reload-config 2>/dev/null
