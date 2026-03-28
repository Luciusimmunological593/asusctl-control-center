"""Performance page — profile switching and fan curve editing."""

from __future__ import annotations

from copy import deepcopy

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...constants import DEFAULT_FAN_TEMPS, RECOMMENDED_CURVES
from ...models import SystemSnapshot
from ...utils import normalize_curve_values
from ..components import (
    channel_button,
    mode_bar,
    page_header,
    panel,
    primary_button,
    secondary_button,
)
from ..widgets.curve_editor import CurveEditor
from ..widgets.unavailable_notice import UnavailableNotice

# Built-in presets derived from RECOMMENDED_CURVES — always present, not deletable
_BUILTIN_PRESETS: dict[str, dict[str, list[int]]] = {
    f"\u2605 {name}": curves for name, curves in RECOMMENDED_CURVES.items()
}
_BUILTIN_PRESET_NAMES: frozenset[str] = frozenset(_BUILTIN_PRESETS.keys())


class PerformancePage(QWidget):
    """Profile tile selector and interactive fan curve editor."""

    def __init__(self, controller, settings):
        super().__init__()
        self.controller = controller
        self.settings = settings
        self.current_temps = DEFAULT_FAN_TEMPS[:]
        self.current_channel = settings.selected_fan
        self.edited_curves: dict[str, list[int]] = deepcopy(settings.custom_curves)
        self._current_curve_profile = settings.last_curve_profile
        self._selected_profile: str = settings.last_curve_profile or ""
        self._active_profile: str = ""
        self._available_profiles: list[str] = []
        self._available_curve_channels: list[str] = []
        self._profiles_supported = False
        self._fan_curves_supported = False
        self._busy = False
        self._profile_dirty = False
        self._curve_dirty = False
        self._awaiting_profile_curves: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header("Performance", "Select a profile, adjust the fan curve, and apply"))

        # ---- Profile mode bar ----
        self._mode_frame, self._mode_buttons = mode_bar(
            [
                ("Quiet", "\U0001f54a  Quiet"),
                ("Balanced", "\u2696  Balanced"),
                ("Performance", "\U0001f525  Performance"),
            ],
            callback=self._on_mode_clicked,
        )
        layout.addWidget(self._mode_frame)

        # Active profile indicator
        active_row = QHBoxLayout()
        active_row.setSpacing(8)
        active_label = QLabel("Active:")
        active_label.setObjectName("MutedLabel")
        self.active_profile_value = QLabel("—")
        self.active_profile_value.setObjectName("ValueLabel")
        active_row.addWidget(active_label)
        active_row.addWidget(self.active_profile_value)
        active_row.addStretch(1)
        layout.addLayout(active_row)

        self.selection_status = QLabel("")
        self.selection_status.setObjectName("MutedLabel")
        self.selection_status.setWordWrap(True)
        layout.addWidget(self.selection_status)

        self.profile_status = QLabel("")
        self.profile_status.setObjectName("MutedLabel")
        self.profile_status.setWordWrap(True)
        layout.addWidget(self.profile_status)

        # ---- Fan curves panel ----
        perf_panel, perf_layout = panel("FAN CURVES")

        # Unavailable notice (shown when fan curves not supported)
        self._curve_unavailable = UnavailableNotice(
            "Fan curve control not available",
            "This device does not expose fan curve editing through asusctl.",
        )
        perf_layout.addWidget(self._curve_unavailable)

        # Fan curve controls container
        self._curve_controls = QWidget()
        cc_layout = QVBoxLayout(self._curve_controls)
        cc_layout.setContentsMargins(0, 0, 0, 0)
        cc_layout.setSpacing(10)

        # Channel buttons
        channel_row = QHBoxLayout()
        channel_row.setSpacing(6)
        self.channel_buttons: dict[str, QWidget] = {}
        for channel, label in [("cpu", "CPU"), ("gpu", "GPU"), ("mid", "Mid")]:
            btn = channel_button(label, lambda checked=False, c=channel: self._set_channel(c))
            self.channel_buttons[channel] = btn
            channel_row.addWidget(btn)
        channel_row.addStretch(1)
        cc_layout.addLayout(channel_row)

        # Curve editor (the graph)
        self.curve_editor = CurveEditor()
        self.curve_editor.curveChanged.connect(self._on_curve_changed)
        cc_layout.addWidget(self.curve_editor)

        # Readback
        self.curve_readback = QLabel("")
        self.curve_readback.setObjectName("MutedLabel")
        self.curve_readback.setWordWrap(True)
        cc_layout.addWidget(self.curve_readback)

        # Saved presets row
        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        self.saved_preset_combo = QComboBox()
        self.load_preset_button = secondary_button("Load", self._load_preset_curve)
        self.save_preset_button = secondary_button("Save as...", self._save_preset)
        self.delete_preset_button = secondary_button("Delete", self._delete_preset)
        self.saved_preset_combo.currentTextChanged.connect(lambda _: self._update_delete_button_state())
        self._refresh_preset_combo()
        preset_row.addWidget(QLabel("Presets:"))
        preset_row.addWidget(self.saved_preset_combo, 1)
        preset_row.addWidget(self.load_preset_button)
        preset_row.addWidget(self.save_preset_button)
        preset_row.addWidget(self.delete_preset_button)
        cc_layout.addLayout(preset_row)

        # Action buttons row
        apply_row = QHBoxLayout()
        self.max_speed_button = primary_button("\u26a1 Max Speed", self._apply_max_speed)
        self.max_speed_button.setToolTip("Set all fans to 100% immediately")
        apply_row.addWidget(self.max_speed_button)
        apply_row.addStretch(1)
        self.apply_curve_button = primary_button("Apply Profile + Curve", self._apply_all)
        apply_row.addWidget(self.apply_curve_button)
        cc_layout.addLayout(apply_row)

        perf_layout.addWidget(self._curve_controls)

        # Profile-only apply (shown when fan curves not available)
        self._profile_only_row = QHBoxLayout()
        self._profile_only_row.addStretch(1)
        self.profile_apply_button = primary_button("Apply profile", self._apply_profile_only)
        self._profile_only_row.addWidget(self.profile_apply_button)
        self._profile_only_container = QWidget()
        self._profile_only_container.setLayout(self._profile_only_row)
        perf_layout.addWidget(self._profile_only_container)

        layout.addWidget(perf_panel)

        layout.addStretch(1)

    # -- Public interface --------------------------------------------------

    def apply_snapshot(self, snapshot: SystemSnapshot) -> None:
        active = snapshot.profiles.active or ""
        self._active_profile = active
        self._available_profiles = snapshot.profiles.available[:]
        self._profiles_supported = snapshot.profiles.supported
        self._fan_curves_supported = snapshot.fan_curve.supported

        # Mode bar
        self.active_profile_value.setText(active or "—")
        self.profile_status.setText(snapshot.profiles.message)
        if active and not self._profile_dirty:
            self._selected_profile = active

        # Fan curves
        if snapshot.fan_curve.snapshot:
            self.current_temps = snapshot.fan_curve.snapshot.temps[:]
            self._current_curve_profile = snapshot.fan_curve.probe_profile or self._current_curve_profile
            hardware_curves = {
                fan: values[:]
                for fan, values in snapshot.fan_curve.snapshot.fans.items()
            }
            self._available_curve_channels = [
                fan for fan in ["cpu", "gpu", "mid"] if fan in hardware_curves
            ]
            awaited = self._awaiting_profile_curves
            should_reload = (
                not self.edited_curves
                or (awaited is not None and active == awaited)
                or not self._curve_dirty
            )
            if should_reload:
                self.edited_curves = hardware_curves
                if awaited is not None and active == awaited:
                    self._curve_dirty = False
        else:
            self.current_temps = DEFAULT_FAN_TEMPS[:]
            self._available_curve_channels = []
            self._curve_dirty = False

        awaited = self._awaiting_profile_curves
        if awaited is not None:
            if active == awaited:
                self._profile_dirty = False
                if not self._fan_curves_supported:
                    self._curve_dirty = False
            self._awaiting_profile_curves = None

        if not self._fan_curves_supported:
            self._curve_unavailable.set_text(
                "Fan curve control not available",
                snapshot.fan_curve.message or "This device does not expose fan curve editing.",
            )

        # Fall back if current channel isn't in data
        if self.current_channel not in self._available_curve_channels and self._available_curve_channels:
            self.current_channel = self._available_curve_channels[0]

        self._sync_mode_buttons()
        self._sync_curve_controls()
        self._update_selection_status()
        self.curve_editor.set_curve(self.current_temps, self.edited_curves.get(self.current_channel, []))
        self.curve_readback.setText(self._format_curve_readback(snapshot))

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._sync_mode_buttons()
        self._sync_curve_controls()
        self._update_selection_status()

    def save_state(self, settings) -> None:
        settings.custom_curves = deepcopy(self.edited_curves)
        settings.saved_presets = deepcopy(self.settings.saved_presets)
        settings.last_curve_profile = self._selected_profile or settings.last_curve_profile
        settings.selected_fan = self.current_channel

    # -- Internal slots ----------------------------------------------------

    def _sync_mode_buttons(self) -> None:
        selected = self._selected_profile or self._active_profile
        for name, btn in self._mode_buttons.items():
            btn.setEnabled(name in self._available_profiles and not self._busy)
            btn.setChecked(name == selected)

    def _on_mode_clicked(self, name: str) -> None:
        """Select a profile locally; apply only when the user confirms."""
        if self._busy or name not in self._available_profiles:
            self._sync_mode_buttons()
            return
        self._selected_profile = name
        self._profile_dirty = name != self._active_profile
        self._sync_mode_buttons()
        self._sync_curve_controls()
        self._update_selection_status()

    def _apply_profile_only(self) -> None:
        profile = self._selected_profile
        if (
            self._busy
            or not profile
            or profile not in self._available_profiles
            or profile == self._active_profile
        ):
            return
        self._awaiting_profile_curves = profile
        self._update_selection_status()
        self.controller.set_profile(profile)

    def _apply_all(self) -> None:
        """Apply both the selected profile and the edited fan curve atomically."""
        profile = self._selected_profile
        if self._busy or not profile or profile not in self._available_profiles:
            return
        self.edited_curves[self.current_channel] = self.curve_editor.curve()
        payload = self._filtered_curve_payload()
        if not payload:
            self.curve_readback.setText("No detected fan channels are available to apply.")
            return
        self._awaiting_profile_curves = profile
        self._update_selection_status()
        self.controller.apply_profile_and_curves(
            profile, deepcopy(payload), self.current_temps[:],
        )

    def _apply_max_speed(self) -> None:
        """Set all fans to 100% immediately and update the graph."""
        profile = self._selected_profile
        if self._busy or not profile or profile not in self._available_profiles:
            return
        channels = self._available_curve_channels or list(self.edited_curves)
        if not channels:
            self.curve_readback.setText("No detected fan channels are available to apply.")
            return
        max_curves = {fan: [100] * len(self.current_temps) for fan in channels}
        for fan, values in max_curves.items():
            self.edited_curves[fan] = values[:]
        self._curve_dirty = True
        self._awaiting_profile_curves = profile
        self._update_selection_status()
        self.controller.apply_profile_and_curves(profile, deepcopy(max_curves), self.current_temps[:])
        self.curve_editor.set_curve(self.current_temps, self.edited_curves.get(self.current_channel, []))
        self.curve_readback.setText("\u26a1 Max speed applied to all fans.")

    def _set_channel(self, channel: str) -> None:
        if channel not in self._available_curve_channels:
            return
        self.current_channel = channel
        self.settings.selected_fan = channel
        for name, button in self.channel_buttons.items():
            button.setChecked(name == channel)
        self.curve_editor.set_curve(self.current_temps, self.edited_curves.get(channel, []))

    def _load_preset_curve(self) -> None:
        name = self.saved_preset_combo.currentText()
        if not name:
            return
        # Check built-in presets first, then user presets
        preset = _BUILTIN_PRESETS.get(name) or self.settings.saved_presets.get(name)
        if not preset:
            return
        channels = self._available_curve_channels or [fan for fan in preset if fan in self.channel_buttons]
        for fan in channels:
            values = preset.get(fan, [])
            self.edited_curves[fan] = normalize_curve_values(values, len(self.current_temps))
        self._curve_dirty = True
        self.curve_editor.set_curve(
            self.current_temps, self.edited_curves.get(self.current_channel, [])
        )
        self.curve_readback.setText(f"Loaded \"{name}\" preset into the editor.")
        self._update_selection_status()

    def _save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Save preset", "Preset name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        # Prevent overwriting built-in presets
        if name in _BUILTIN_PRESET_NAMES:
            self.curve_readback.setText(f"Cannot overwrite built-in preset \"{name}\".")
            return
        # Save current edited curves (all channels)
        self.edited_curves[self.current_channel] = self.curve_editor.curve()
        self.settings.saved_presets[name] = deepcopy(self.edited_curves)
        self._refresh_preset_combo()
        self.saved_preset_combo.setCurrentText(name)
        self.curve_readback.setText(f"Saved preset \"{name}\".")

    def _delete_preset(self) -> None:
        name = self.saved_preset_combo.currentText()
        if not name or name in _BUILTIN_PRESET_NAMES:
            return
        if name in self.settings.saved_presets:
            del self.settings.saved_presets[name]
            self._refresh_preset_combo()
            self.curve_readback.setText(f"Deleted preset \"{name}\".")

    def _update_delete_button_state(self) -> None:
        """Disable delete button for built-in presets."""
        name = self.saved_preset_combo.currentText()
        is_builtin = name in _BUILTIN_PRESET_NAMES
        self.delete_preset_button.setEnabled(
            self._fan_curves_supported and not self._busy and bool(name) and not is_builtin
        )

    def _refresh_preset_combo(self) -> None:
        self.saved_preset_combo.blockSignals(True)
        current = self.saved_preset_combo.currentText()
        self.saved_preset_combo.clear()
        # Built-in presets first (always present)
        builtin_names = sorted(_BUILTIN_PRESET_NAMES)
        user_names = sorted(self.settings.saved_presets.keys())
        self.saved_preset_combo.addItems(builtin_names + user_names)
        all_names = set(builtin_names) | set(user_names)
        if current and current in all_names:
            self.saved_preset_combo.setCurrentText(current)
        self.saved_preset_combo.blockSignals(False)
        self._update_delete_button_state()

    def _on_curve_changed(self, values: list[int]) -> None:
        self.edited_curves[self.current_channel] = list(values)
        self._curve_dirty = True
        self.curve_readback.setText("Draft curve updated. Click Apply Profile + Curve to write it.")
        self._update_selection_status()

    # -- Helpers -----------------------------------------------------------

    def _filtered_curve_payload(self) -> dict[str, list[int]]:
        channels = self._available_curve_channels or [fan for fan in self.edited_curves if fan in self.channel_buttons]
        return {
            fan: normalize_curve_values(self.edited_curves.get(fan, []), len(self.current_temps))
            for fan in channels
            if fan in self.edited_curves
        }

    def _sync_curve_controls(self) -> None:
        has_channels = bool(self._available_curve_channels)
        self._curve_unavailable.setVisible(not self._fan_curves_supported)
        self._curve_controls.setVisible(self._fan_curves_supported)
        self._profile_only_container.setVisible(not self._fan_curves_supported and self._profiles_supported)

        for channel, button in self.channel_buttons.items():
            available = channel in self._available_curve_channels
            button.setVisible(available)
            button.setEnabled(self._fan_curves_supported and available and not self._busy)
            button.setChecked(channel == self.current_channel and available)

        self.profile_apply_button.setEnabled(
            self._profiles_supported
            and not self._fan_curves_supported
            and not self._busy
            and bool(self._selected_profile)
            and self._selected_profile in self._available_profiles
            and self._selected_profile != self._active_profile
        )
        self.apply_curve_button.setEnabled(
            self._fan_curves_supported
            and has_channels
            and not self._busy
            and bool(self._selected_profile)
            and self._selected_profile in self._available_profiles
        )
        self.max_speed_button.setEnabled(
            self._fan_curves_supported
            and has_channels
            and not self._busy
            and bool(self._selected_profile)
            and self._selected_profile in self._available_profiles
        )
        self.saved_preset_combo.setEnabled(self._fan_curves_supported and not self._busy)
        self.load_preset_button.setEnabled(self._fan_curves_supported and not self._busy)
        self.save_preset_button.setEnabled(self._fan_curves_supported and has_channels and not self._busy)
        self._update_delete_button_state()
        self.curve_editor.set_read_only(not self._fan_curves_supported or not has_channels or self._busy)

    def _update_selection_status(self) -> None:
        if self._awaiting_profile_curves:
            if self._fan_curves_supported:
                self.selection_status.setText(
                    f"Applying {self._awaiting_profile_curves} and syncing the current fan-curve draft."
                )
            else:
                self.selection_status.setText(f"Applying profile {self._awaiting_profile_curves}.")
            return

        if self._profile_dirty and self._curve_dirty:
            self.selection_status.setText(
                f"Selected profile: {self._selected_profile}. The curve editor contains unapplied changes."
            )
            return

        if self._profile_dirty:
            if self._fan_curves_supported:
                self.selection_status.setText(
                    f"Selected profile: {self._selected_profile}. Click Apply Profile + Curve to send it."
                )
            else:
                self.selection_status.setText(
                    f"Selected profile: {self._selected_profile}. Click Apply profile to switch modes."
                )
            return

        if self._curve_dirty and self._fan_curves_supported:
            target = self._selected_profile or self._active_profile or "the selected profile"
            self.selection_status.setText(
                f"Fan curve draft changed for {target}. Click Apply Profile + Curve to write it."
            )
            return

        if self._active_profile:
            self.selection_status.setText(
                f"Selected profile matches the active hardware profile: {self._active_profile}."
            )
        else:
            self.selection_status.setText("")

    @staticmethod
    def _format_curve_readback(snapshot: SystemSnapshot) -> str:
        if not snapshot.fan_curve.snapshot:
            return snapshot.fan_curve.message
        temps = snapshot.fan_curve.snapshot.temps
        lines: list[str] = []
        for fan in ["cpu", "gpu", "mid"]:
            values = snapshot.fan_curve.snapshot.fans.get(fan, [])
            enabled = snapshot.fan_curve.snapshot.enabled.get(fan, False)
            tag = "\u2713" if enabled else "\u2717"
            pairs = "  \u2502  ".join(
                f"{temp}\u00b0C \u2192 {value}%"
                for temp, value in zip(temps, values, strict=False)
            )
            lines.append(f"{tag} {fan.upper()}:  {pairs}")
        return "\n".join(lines)
