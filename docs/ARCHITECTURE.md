# Architecture

## Stack

- Python 3
- PyQt6 widgets UI
- `asusctl` CLI as the primary backend
- optional `supergfxctl` CLI backend
- read-only sysfs inspection for low-level ASUS firmware attributes

## Module layout

- `src/asus_linux_control_center/__init__.py`
  Package version and public API exports.
- `src/asus_linux_control_center/__main__.py`
  Console entry point.
- `src/asus_linux_control_center/app.py`
  Application entrypoint and CLI/GUI mode selection.
- `src/asus_linux_control_center/cli.py`
  Argument parsing and CLI-only diagnostics mode.
- `src/asus_linux_control_center/constants.py`
  App-wide constants: default fan temps, recommended curves, aura effects,
  firmware attribute labels.
- `src/asus_linux_control_center/logging_utils.py`
  Log configuration helpers (file and console handlers).
- `src/asus_linux_control_center/models.py`
  All data models (`SystemSnapshot`, `ActionOutcome`, `SettingsData`, etc.).
- `src/asus_linux_control_center/paths.py`
  XDG-aware config, state, and log path resolution.
- `src/asus_linux_control_center/settings.py`
  JSON-backed settings persistence with safe fallback on corruption.
- `src/asus_linux_control_center/utils.py`
  Pure helper functions: curve normalization, monotonic enforcement, OS release
  parsing.
- `src/asus_linux_control_center/services/detection.py`
  High-level hardware snapshot orchestration and action facade.
- `src/asus_linux_control_center/services/controller.py`
  UI-facing async task controller built on `QThreadPool`.
- `src/asus_linux_control_center/services/diagnostics.py`
  Snapshot-to-text formatting for diagnostics reports.
- `src/asus_linux_control_center/backends/commands.py`
  Subprocess wrapper with timeout and error capture (`CommandRunner`).
- `src/asus_linux_control_center/backends/asusctl.py`
  `asusctl` parsing and write operations.
- `src/asus_linux_control_center/backends/supergfxctl.py`
  Optional graphics mode parsing and switching.
- `src/asus_linux_control_center/backends/sysfs.py`
  Read-only ASUS kernel attribute inspection.
- `src/asus_linux_control_center/ui/main_window.py`
  Multi-page desktop UI and view-state coordination.
- `src/asus_linux_control_center/ui/widgets/curve_editor.py`
  Custom fan curve editor widget.
- `src/asus_linux_control_center/ui/styles.py`
  Application stylesheet (dark sidebar, light cards, blue accents).

## State flow

1. UI requests a refresh.
2. `ControlCenterController` runs snapshot gathering in a worker thread.
3. `ControlService` queries backends and builds a `SystemSnapshot`.
4. The UI updates all pages from that snapshot.
5. Write actions return `ActionOutcome`, then trigger a fresh snapshot.

## Design choices

- CLI-first integration keeps the app easy to package independently from upstream daemon internals.
- `supergfxctl` is optional by design because upstream guidance now discourages blanket installation.
- Low-level ASUS firmware attributes are surfaced read-only because write semantics differ by kernel and machine, and the goal is to remain truthful.
