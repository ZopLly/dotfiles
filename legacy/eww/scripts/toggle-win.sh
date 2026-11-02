#!/usr/bin/env bash
set -euo pipefail
config_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
case "${1:-}" in control_center|media_popup) target=$1 ;; *) exit 2 ;; esac
if eww --config "$config_dir" active-windows | grep -q "^$target:"; then
    eww --config "$config_dir" update open_cc=false media_open=false
    sleep 0.35
    eww --config "$config_dir" close "$target" closer
else
    eww --config "$config_dir" close control_center media_popup closer 2>/dev/null || true
    eww --config "$config_dir" update open_cc=false media_open=false
    eww --config "$config_dir" open closer
    eww --config "$config_dir" open "$target"
    eww --config "$config_dir" update "$([ "$target" = control_center ] && echo open_cc || echo media_open)=true"
fi
