#!/bin/bash

TARGET_WIN=$1

# Проверяем, открыто ли запрашиваемое окно
if eww active-windows | grep -q "^$TARGET_WIN:"; then
    # Если открыто — закрываем всё
    eww close $TARGET_WIN closer
else
    # Если закрыто — сначала закрываем другие открытые окна,
    # затем открываем подложку и нужное окно
    eww close control_center media_popup closer 2>/dev/null
    eww open closer
    eww open $TARGET_WIN
fi
