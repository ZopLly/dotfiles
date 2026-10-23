#!/usr/bin/env bash
# Private repository bootstrap. Run after `gh auth login` on the target machine.
set -euo pipefail
(( EUID != 0 )) || { echo 'Run as your regular desktop user, not root.' >&2; exit 1; }
command -v gh >/dev/null || { echo 'Install GitHub CLI: sudo pacman -S github-cli; then gh auth login.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Sign in first: gh auth login' >&2; exit 1; }
ref=${DOTFILES_REF:-main}
[[ "$ref" =~ ^[a-zA-Z0-9._/-]+$ ]] || { echo 'Invalid DOTFILES_REF' >&2; exit 1; }
work=$(mktemp -d -t niri-shell-install.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
# HTTPS GitHub API: uses gh authentication, never reads SSH keys.
gh api "repos/ZopLly/dotfiles/tarball/$ref" > "$work/source.tar.gz"
mkdir "$work/source"
tar --extract --gzip --file "$work/source.tar.gz" --directory "$work/source" --strip-components=1 --no-same-owner --no-same-permissions
[[ -f "$work/source/scripts/install.py" && -f "$work/source/quickshell/Dashboard.qml" ]] || { echo 'Incomplete source archive' >&2; exit 1; }
if [[ "${1:-}" == '--check' ]]; then
    bash "$work/source/install.sh"
    exit
fi
bash "$work/source/scripts/install-deps.sh"
bash "$work/source/install.sh" --portable --apply "$@"
echo 'Installation complete. Log out and select the Niri session in your login screen.'
