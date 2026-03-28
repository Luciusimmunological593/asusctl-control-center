from __future__ import annotations

import os
from pathlib import Path

from .constants import APP_ID


def config_dir() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = root / APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    path = root / APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_file() -> Path:
    return state_dir() / "app.log"


def settings_file() -> Path:
    return config_dir() / "settings.json"
