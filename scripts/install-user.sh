#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m pip install --user "$ROOT_DIR"
install -Dm644 "$ROOT_DIR/packaging/asus-linux-control-center.desktop" \
  "$HOME/.local/share/applications/asus-linux-control-center.desktop"
install -Dm644 "$ROOT_DIR/assets/icon.svg" \
  "$HOME/.local/share/icons/hicolor/scalable/apps/asus-linux-control-center.svg"

update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

echo "Installed ASUS Linux Control Center for the current user."
