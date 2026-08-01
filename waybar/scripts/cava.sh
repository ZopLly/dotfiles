#!/usr/bin/env bash

config_file="/tmp/waybar_cava_config"
cat <<EOF > "$config_file"
[general]
bars = 10
sleep_timer = 1

[input]
method = pulse

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7
EOF

# Символы колонок (от меньшего к большему)
dict=(" " " " "▂" "▃" "▄" "▅" "▆" "▇" "█")

# Убиваем застрявшие фоновые процессы cava
pkill -f "cava -p $config_file" 2>/dev/null

cava -p "$config_file" | while read -r line; do
    IFS=';' read -ra BARS <<< "$line"
    res=""
    for val in "${BARS[@]}"; do
        if [[ "$val" =~ ^[0-9]+$ ]] && [ "$val" -lt 8 ]; then
            res+="${dict[$val]}"
        fi
    done
    
    # Показываем эквалайзер при звуке, либо нотку в тишине
    if [[ -n "$res" && "$res" != "          " ]]; then
        echo "$res"
    else
        echo "󰎈"
    fi
done
