#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# The installer copies the complete niri tree, including conf.d and runtime.sh.
exec python3 "$root/scripts/install.py" "$@"
