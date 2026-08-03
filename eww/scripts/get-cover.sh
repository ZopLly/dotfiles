#!/bin/bash

TMP_DIR="/tmp/eww_covers"
mkdir -p "$TMP_DIR"

# Получаем ссылку на обложку от Spotify / плеера
URL=$(playerctl metadata mpris:artUrl 2>/dev/null)

if [ -z "$URL" ]; then
    echo ""
    exit 0
fi

# Если это локальный файл (например, из локального плеера)
if [[ "$URL" == file://* ]]; then
    echo "${URL#file://}"
    exit 0
fi

# Если это ссылка Spotify (http/https)
if [[ "$URL" == http://* || "$URL" == https://* ]]; then
    # Создаем уникальное имя файла на основе ссылки
    HASH=$(echo -n "$URL" | md5sum | cut -d' ' -f1)
    COVER_PATH="$TMP_DIR/$HASH.jpg"

    # Если такой обложки ещё нет — скачиваем ее и чистим старые
    if [ ! -f "$COVER_PATH" ]; then
        rm -f "$TMP_DIR"/* 2>/dev/null
        curl -s "$URL" --output "$COVER_PATH"
    fi

    # Выдаем новый путь — Eww сразу поймет, что строка изменилась
    echo "$COVER_PATH"
    exit 0
fi

echo "$URL"
