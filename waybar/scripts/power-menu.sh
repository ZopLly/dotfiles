#!/bin/bash

# Формируем список опций для fuzzel
SELECTION=$(echo -e "󰐥 Power Off\n󰜉 Reboot\n󰤄 Sleep" | fuzzel --dmenu --prompt "Power Menu ❯ " --width 20 --lines 3)

# Обрабатываем выбор
case "$SELECTION" in
    *"Power Off")
        systemctl poweroff
        ;;
    *"Reboot")
        systemctl reboot
        ;;
    *"Sleep")
        systemctl suspend
        ;;
esac

