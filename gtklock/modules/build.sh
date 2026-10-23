#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
for module in minimal notifications layout; do
    gcc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared "$module.c" -o "$module-module.so" $(pkg-config --cflags --libs gtk+-3.0 gio-2.0)
done
