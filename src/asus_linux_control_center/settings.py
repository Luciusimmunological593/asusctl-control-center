from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .constants import DEFAULT_FAN_TEMPS, RECOMMENDED_CURVES
from .models import SettingsData
from .paths import settings_file


def _default_custom_curves() -> dict[str, list[int]]:
    return {
        fan: values[:]
        for fan, values in RECOMMENDED_CURVES["Balanced"].items()
        if len(values) == len(DEFAULT_FAN_TEMPS)
    }


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or settings_file()

    def load(self) -> SettingsData:
        defaults = SettingsData(custom_curves=_default_custom_curves())
        if not self.path.exists():
            return defaults

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return defaults

        custom_curves = data.get("custom_curves") or defaults.custom_curves

        def _safe_int(value: object, fallback: int) -> int:
            try:
                return int(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return fallback

        theme = data.get("theme", defaults.theme)
        if theme not in ("light", "dark"):
            theme = defaults.theme

        return SettingsData(
            last_page=data.get("last_page", defaults.last_page),
            last_curve_profile=data.get("last_curve_profile", defaults.last_curve_profile),
            selected_fan=data.get("selected_fan", defaults.selected_fan),
            custom_curves={fan: list(values) for fan, values in custom_curves.items()},
            saved_presets={
                name: {fan: list(vals) for fan, vals in curves.items()}
                for name, curves in (data.get("saved_presets") or {}).items()
                if isinstance(curves, dict)
            },
            aura_effect=data.get("aura_effect", defaults.aura_effect),
            aura_zone=data.get("aura_zone", defaults.aura_zone),
            aura_color_1=data.get("aura_color_1", defaults.aura_color_1),
            aura_color_2=data.get("aura_color_2", defaults.aura_color_2),
            window_width=_safe_int(data.get("window_width", defaults.window_width), defaults.window_width),
            window_height=_safe_int(data.get("window_height", defaults.window_height), defaults.window_height),
            theme=theme,
        )

    def save(self, settings: SettingsData) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
