# Validation

Validation was performed on an Ubuntu 25.10 machine with an actual `ROG Strix G614JV`, kernel `6.17.0-19-generic`, `asusctl 6.3.5`, and `asusd.service` active.
This identifies the validation host only; it is not the project's supported-device list.

## Test matrix

| # | Feature | Scenario | Input/Value | Expected | Validated | Notes |
|---|---------|----------|-------------|----------|-----------|-------|
| 1 | Profile switch | Happy path | "Performance" | Profile changes, read-back matches | Unit + HW | asusctl required |
| 2 | Profile switch | Unknown profile | "Turbo" | Error returned | Unit | |
| 3 | Profile switch | During busy | Any | Button disabled | Code | Phase 2 fix |
| 4 | Fan curve apply | Happy path | 2-fan dict, 8 temps | All fans written + enable-all | Unit | |
| 5 | Fan curve apply | Partial failure | 1st fan write fails | Enable-all skipped, error shown | Unit | Phase 1 fix |
| 6 | Fan curve apply | Empty curves dict | {} | Error returned, no commands run | Unit | Phase 5 fix |
| 7 | Fan curve apply | Single fan only | {"cpu": [...]} | Only CPU written, enable-all runs | Unit | Phase 5 fix |
| 8 | Fan curve apply | All zeros | [0]*8 | Non-decreasing enforced (all 0) | Unit | |
| 9 | Fan curve apply | All 100s | [100]*8 | Accepted | Unit | |
| 10 | Fan curve apply | Values >100 | [200]*8 | Clamped to 100 | Unit | |
| 11 | Fan curve apply | Negative values | [-10]*8 | Clamped to 0 | Unit | |
| 12 | Battery limit | Happy path (80%) | 80 | Accepted | Unit + HW | |
| 13 | Battery limit | Minimum (20) | 20 | Accepted | Unit | |
| 14 | Battery limit | Maximum (100) | 100 | Accepted | Unit | |
| 15 | Battery limit | Below minimum (5) | 5 | Rejected, no command sent | Unit | Phase 1 fix |
| 16 | Battery limit | Above maximum (150) | 150 | Rejected, no command sent | Unit | Phase 1 fix |
| 17 | Battery limit | Zero | 0 | Rejected | Unit | Phase 1 fix |
| 18 | Oneshot charge | Happy path (100%) | 100 | Accepted | Unit | |
| 19 | Oneshot charge | Below minimum (10) | 10 | Rejected | Unit | Phase 1 fix |
| 20 | Keyboard brightness | Happy path | "high" | Level changes | Unit + HW | |
| 21 | Keyboard brightness | Failure | Permission denied | Error returned | Unit | |
| 22 | Aura effect | Static + color | "#ff0000" | Command correct, no zone | Unit | |
| 23 | Aura effect | Breathe + zone | "keyboard" | colour2 + speed + zone flags | Unit | |
| 24 | Aura effect | Rainbow wave | direction "right" | direction flag present | Unit | |
| 25 | Aura effect | Unsupported | "sparkle" | Error, no command | Unit | |
| 26 | Aura color | Picked but not applied | Color dialog | Color NOT persisted in settings | Code | Phase 2 fix |
| 27 | Aura power | Enable all | "keyboard", True | --boot/--awake/--sleep/--shutdown | Unit | |
| 28 | Aura power | Disable all | "keyboard", False | No state flags (bare command) | Unit | Documented behaviour |
| 29 | Graphics mode | Happy path | "Hybrid" | Mode requested | Unit | Needs HW |
| 30 | Graphics mode | Confirmation dialog | Any mode | Warning shown first | Code | Phase 5 fix |
| 31 | Graphics mode | Timeout | 75s expires | Specific timeout message | Unit | Phase 3 fix |
| 32 | Graphics mode | Daemon unavailable | supergfxd down | Explains daemon requirement | Unit | |
| 33 | Settings | Round-trip | Save + load | All fields match | Unit | |
| 34 | Settings | Missing file | Nonexistent path | Defaults returned | Unit | |
| 35 | Settings | Corrupted JSON | Invalid content | Defaults returned | Unit | Phase 3 fix |
| 36 | Settings | Non-int dimensions | "not_a_number" | Defaults used, no crash | Unit | Phase 3 fix |
| 37 | Settings | Empty custom_curves | {} | Defaults used | Unit | |
| 38 | Settings | Nested parent dirs | deep/nested/path | Dirs created | Unit | |
| 39 | bus_name_exists | Present | Known name | True | Unit | |
| 40 | bus_name_exists | Missing | Unknown name | False | Unit | |
| 41 | bus_name_exists | Blank lines | Whitespace in output | No crash | Unit | Phase 1 fix |
| 42 | bus_name_exists | Empty output | "" | False | Unit | |
| 43 | bus_name_exists | busctl missing | which() returns None | False | Unit | |
| 44 | Parser: info | Empty output | "" | "Unknown" defaults | Unit | |
| 45 | Parser: info | Partial output | Family only | Family parsed, rest Unknown | Unit | |
| 46 | Parser: profile list | Empty | "" | [] | Unit | |
| 47 | Parser: profile get | Empty | "" | (None, None, None) | Unit | |
| 48 | Parser: fan curve | No curves | "No fan curves" | None | Unit | |
| 49 | Parser: fan curve | Single fan | CPU only | snapshot with 1 fan | Unit | |
| 50 | Busy state | Multiple rapid clicks | Fast clicks | All action buttons disabled | Code | Phase 2 fix |
| 51 | Battery UI | Limit is 0 | snapshot.battery.limit=0 | Slider shows 0, not 100 | Code | Phase 2 fix |
| 52 | Channel fallback | Missing fan | "mid" not in snapshot | Falls back to first fan | Code | Phase 3 fix |
| 53 | Preset gating | Fan curves unsupported | not supported | Preset combo+button disabled | Code | Phase 2 fix |
| 54 | Curve utils | Normalize empty→8 | [], 8 | [0]*8 | Unit | |
| 55 | Curve utils | Normalize oob values | [-10, 200] | Clamped to [0, 100] | Unit | |
| 56 | Curve utils | Non-decreasing dips | [50, 30, 40] | [50, 50, 50] | Unit | |
| 57 | Curve utils | Unique lines dedup | Duplicates | Ordered set | Unit | |
| 58 | supergfxctl modes | Empty | "" | [] | Unit | |
| 59 | supergfxctl failure | Empty | "" | "unavailable" message | Unit | |
| 60 | Pending transition | All None | None, None, None | False | Unit | |

Legend:
- **Unit** = verified by automated test in `tests/`
- **Code** = verified by code inspection (UI change, no automated test)
- **HW** = verified on real ASUS hardware (ROG Strix G614JV)
- **Needs HW** = requires real hardware for full validation

Real hardware validation performed:

- `asusctl info`
- `asusctl profile list`
- `asusctl profile get`
- `asusctl fan-curve --mod-profile Performance`
- `asusctl battery info`
- `asusctl leds get`
- `asusctl aura effect --help`
- `asusctl aura power --help`
- application diagnostics mode
- offscreen GUI startup and refresh

Environment-specific limitation:

- `supergfxctl` was built from upstream source and the binaries were installed into `~/.local/bin` for validation, but a full system installation was not possible in this session because it requires privileged installation of the systemd unit and D-Bus policy.
- Launching `supergfxd` manually with `IS_SERVICE=1` failed with `org.freedesktop.DBus.Error.AccessDenied`, which is expected without the root-installed system bus policy.
- Graphics mode switching was therefore validated through real installed-binary detection, parser coverage, and daemon-unavailable UI flow, not through a successful live mode switch.
- No write operations were forced during validation because this rebuild is meant to remain safe and truthful about what was and was not changed on the host.

Automated checks:

```bash
python3 -m compileall src
PYTHONPATH=src python3 -m asus_linux_control_center --diagnostics
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 - <<'PY'
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from asus_linux_control_center.logging_utils import configure_logging
from asus_linux_control_center.services import ControlCenterController, ControlService
from asus_linux_control_center.settings import SettingsStore
from asus_linux_control_center.ui import MainWindow

logger = configure_logging()
service = ControlService(logger)
app = QApplication([])
controller = ControlCenterController(service)
window = MainWindow(controller, SettingsStore())
window.show()
controller.refresh()
QTimer.singleShot(2500, app.quit)
raise SystemExit(app.exec())
PY
```

Package-level tests:

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python .venv/get-pip.py
.venv/bin/python -m pip install -e .[dev]
PYTHONPATH=src .venv/bin/python -m pytest
PYTHONPATH=src .venv/bin/python -m ruff check src tests
PYTHONPATH=src .venv/bin/python -m build
```

Additional graphics validation:

```bash
git clone https://gitlab.com/asus-linux/supergfxctl.git
cd supergfxctl
cargo build --release
install -Dm755 ./target/release/supergfxctl ~/.local/bin/supergfxctl
install -Dm755 ./target/release/supergfxd ~/.local/bin/supergfxd
~/.local/bin/supergfxctl --help
IS_SERVICE=1 ~/.local/bin/supergfxd
PYTHONPATH=src .venv/bin/python -m asus_linux_control_center --diagnostics-json
```

What failed initially:

- `python3 -m venv --system-site-packages .venv` created the venv shell structure but could not install `pip` because `ensurepip` is unavailable in the current Ubuntu environment.

Workaround used:

```bash
curl -L https://bootstrap.pypa.io/get-pip.py -o .venv/get-pip.py
.venv/bin/python .venv/get-pip.py
```
