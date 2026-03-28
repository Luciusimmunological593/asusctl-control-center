#!/usr/bin/env bash
# Launch ASUS Linux Control Center with a clean environment.
#
# Some terminals (e.g. VS Code snap) inject library paths that conflict
# with system glibc.  This wrapper passes only the variables the app
# actually needs so Qt and D-Bus work without interference.

exec env -i \
  HOME="$HOME" \
  PATH="$PATH" \
  DISPLAY="${DISPLAY:-}" \
  WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
  XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" \
  XDG_SESSION_TYPE="${XDG_SESSION_TYPE:-}" \
  DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
  asus-linux-control-center "$@"
