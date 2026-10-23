#!/usr/bin/env bash
# Credentials remain exclusively in NetworkManager's terminal prompt.
set -u
nmcli --ask device wifi connect "${1:?Missing BSSID}"
result=$?
if (( result != 0 )); then
    printf '\nПодключение не выполнено. Нажмите Enter, чтобы закрыть окно.\n'
    read -r _ || true
fi
exit "$result"
