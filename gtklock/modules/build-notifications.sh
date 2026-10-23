#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
gcc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared notifications.c -o notifications-module.so $(pkg-config --cflags --libs gtk+-3.0 gio-2.0)
