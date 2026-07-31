#!/bin/bash

# Набор символов для верхней части (растут снизу вверх)
bar_up=(" " " " "▂" "▃" "▄" "▅" "▆" "▇" "█")

# Набор символов для нижней части (растут сверху вниз)
bar_down=(" " "▔" "🮂" "🮃" "▀" "▔" "🮀" "🮁" "█")

pipe="/tmp/cava_fifo"
[ -p $pipe ] || mkfifo $pipe

config_file="/tmp/cava_config"
cat <<EOF > $config_file
[general]
bars = 12
sleep_timer = 2

[output]
method = raw
raw_target = $pipe
data_format = ascii
ascii_max_range = 8
EOF

cava -p $config_file &

while read -r line; do
    top_line=""
    bot_line=""
    for (( i=0; i<${#line}; i++ )); do
        val="${line:$i:1}"
        if [ "$val" -ge 0 ] 2>/dev/null; then
            top_line+="${bar_up[$val]}"
            bot_line+="${bar_down[$val]}"
        fi
    done

    # Вывод с двухстрочным вертикальным выравниванием (если поддерживает шрифт)
    # или красивой зеркальной суммой:
    echo "{\"text\": \"$top_line\n$bot_line\"}"
done < $pipe
