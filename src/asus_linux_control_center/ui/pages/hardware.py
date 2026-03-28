"""Hardware page — keyboard, aura, battery, and graphics sections."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...constants import (
    AURA_DIRECTIONS,
    AURA_EFFECTS,
    AURA_SPEEDS,
)
from ...models import SystemSnapshot
from ..components import (
    experimental_notice,
    page_header,
    panel,
    primary_button,
    secondary_button,
    separator,
)
from ..widgets.unavailable_notice import UnavailableNotice


class HardwarePage(QWidget):
    """Scrollable page combining keyboard, aura, battery, and graphics controls."""

    def __init__(self, controller, settings):
        super().__init__()
        self.controller = controller
        self.settings = settings

        self._effect_labels = {display: command for display, command in AURA_EFFECTS}
        self._effect_commands = {command: display for display, command in AURA_EFFECTS}
        self._pending_aura_color_1 = settings.aura_color_1
        self._pending_aura_color_2 = settings.aura_color_2
        self._busy = False
        self._keyboard_supported = False
        self._aura_supported = False
        self._battery_supported = False
        self._graphics_installed = False
        self._graphics_can_switch = False
        self._graphics_pending = False
        self._aura_power_buttons: list[QPushButton] = []

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header("Hardware", "Keyboard, lighting, battery and graphics controls"))

        self._build_keyboard_section(layout)
        self._build_aura_section(layout)
        self._build_battery_section(layout)
        self._build_graphics_section(layout)

        layout.addStretch(1)

    # =====================================================================
    # KEYBOARD BRIGHTNESS
    # =====================================================================

    def _build_keyboard_section(self, parent_layout: QVBoxLayout) -> None:
        kb_card, kb_layout = panel("KEYBOARD")

        self._kb_unavailable = UnavailableNotice(
            "Keyboard brightness not available",
            "asusctl does not report keyboard brightness control on this device.",
        )
        kb_layout.addWidget(self._kb_unavailable)

        self._kb_controls = QWidget()
        kc = QVBoxLayout(self._kb_controls)
        kc.setContentsMargins(0, 0, 0, 0)
        kc.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)
        lbl = QLabel("Brightness level")
        lbl.setObjectName("MutedLabel")
        lbl.setFixedWidth(120)
        self.keyboard_brightness_combo = QComboBox()
        self.keyboard_brightness_combo.addItems(["off", "low", "med", "high"])
        self.keyboard_apply_button = primary_button("Apply", self._apply_keyboard_brightness)
        row.addWidget(lbl)
        row.addWidget(self.keyboard_brightness_combo, 1)
        row.addWidget(self.keyboard_apply_button)
        kc.addLayout(row)

        self.keyboard_status = QLabel("")
        self.keyboard_status.setObjectName("MutedLabel")
        self.keyboard_status.setWordWrap(True)
        kc.addWidget(self.keyboard_status)

        kb_layout.addWidget(self._kb_controls)
        parent_layout.addWidget(kb_card)

    # =====================================================================
    # AURA LIGHTING
    # =====================================================================

    def _build_aura_section(self, parent_layout: QVBoxLayout) -> None:
        aura_card, aura_layout = panel("AURA LIGHTING")

        self._aura_unavailable = UnavailableNotice(
            "Aura lighting not available",
            "asusctl does not report aura control on this device.",
        )
        aura_layout.addWidget(self._aura_unavailable)
        self._aura_controls = QWidget()
        ac = QVBoxLayout(self._aura_controls)
        ac.setContentsMargins(0, 0, 0, 0)
        ac.setSpacing(10)

        # Effect + zone row
        effect_row = QHBoxLayout()
        effect_row.setSpacing(10)
        e_lbl = QLabel("Effect")
        e_lbl.setObjectName("MutedLabel")
        e_lbl.setFixedWidth(60)
        self.aura_effect_combo = QComboBox()
        self.aura_effect_combo.currentTextChanged.connect(lambda _: self._update_aura_visibility())
        z_lbl = QLabel("Zone")
        z_lbl.setObjectName("MutedLabel")
        z_lbl.setFixedWidth(40)
        self.aura_zone_combo = QComboBox()
        effect_row.addWidget(e_lbl)
        effect_row.addWidget(self.aura_effect_combo, 1)
        effect_row.addWidget(z_lbl)
        effect_row.addWidget(self.aura_zone_combo, 1)
        ac.addLayout(effect_row)

        # Speed + direction row
        self._speed_direction_row = QWidget()
        sd = QHBoxLayout(self._speed_direction_row)
        sd.setContentsMargins(0, 0, 0, 0)
        sd.setSpacing(10)
        s_lbl = QLabel("Speed")
        s_lbl.setObjectName("MutedLabel")
        s_lbl.setFixedWidth(60)
        self._speed_label = s_lbl
        self.aura_speed_combo = QComboBox()
        self.aura_speed_combo.addItems(AURA_SPEEDS)
        d_lbl = QLabel("Direction")
        d_lbl.setObjectName("MutedLabel")
        d_lbl.setFixedWidth(60)
        self.aura_direction_combo = QComboBox()
        self.aura_direction_combo.addItems(AURA_DIRECTIONS)
        sd.addWidget(s_lbl)
        sd.addWidget(self.aura_speed_combo, 1)
        self._direction_label = d_lbl
        sd.addWidget(d_lbl)
        sd.addWidget(self.aura_direction_combo, 1)
        ac.addWidget(self._speed_direction_row)

        # Color buttons
        color_row = QHBoxLayout()
        color_row.setSpacing(10)
        self.aura_color_1_button = secondary_button("Primary color", self._pick_aura_color_1)
        self.aura_color_2_button = secondary_button("Secondary color", self._pick_aura_color_2)
        color_row.addWidget(self.aura_color_1_button)
        color_row.addWidget(self.aura_color_2_button)
        color_row.addStretch(1)
        ac.addLayout(color_row)
        self._update_color_button(self.aura_color_1_button, self.settings.aura_color_1)
        self._update_color_button(self.aura_color_2_button, self.settings.aura_color_2)

        # Apply
        apply_row = QHBoxLayout()
        apply_row.addStretch(1)
        self.aura_apply_button = primary_button("Apply effect", self._apply_aura_effect)
        apply_row.addWidget(self.aura_apply_button)
        ac.addLayout(apply_row)

        self.aura_status = QLabel("")
        self.aura_status.setObjectName("MutedLabel")
        self.aura_status.setWordWrap(True)
        ac.addWidget(self.aura_status)

        aura_layout.addWidget(self._aura_controls)

        # Aura power zones sub-section
        aura_layout.addWidget(separator())
        power_header = QLabel("Power zones")
        power_header.setObjectName("SectionTitle")
        power_header.setStyleSheet("font-size: 13px;")
        aura_layout.addWidget(power_header)
        power_hint = QLabel(
            "Zone state is not queryable through asusctl. "
            "These actions write explicit enable-all or disable-all states."
        )
        power_hint.setObjectName("MutedLabel")
        power_hint.setWordWrap(True)
        aura_layout.addWidget(power_hint)
        self.aura_power_grid = QGridLayout()
        aura_layout.addLayout(self.aura_power_grid)

        parent_layout.addWidget(aura_card)

    # =====================================================================
    # BATTERY
    # =====================================================================

    def _build_battery_section(self, parent_layout: QVBoxLayout) -> None:
        bat_card, bat_layout = panel("BATTERY")

        self._bat_unavailable = UnavailableNotice(
            "Battery charge limit not available",
            "asusctl does not report battery charge control on this device.",
        )
        bat_layout.addWidget(self._bat_unavailable)

        self._bat_controls = QWidget()
        bc = QVBoxLayout(self._bat_controls)
        bc.setContentsMargins(0, 0, 0, 0)
        bc.setSpacing(10)

        # Current limit
        limit_row = QHBoxLayout()
        limit_row.setSpacing(10)
        ll = QLabel("Current charge limit")
        ll.setObjectName("MutedLabel")
        ll.setFixedWidth(140)
        self.battery_limit_value = QLabel("—")
        self.battery_limit_value.setObjectName("ValueLabel")
        limit_row.addWidget(ll)
        limit_row.addWidget(self.battery_limit_value, 1)
        bc.addLayout(limit_row)

        # Slider + spin + apply
        control_row = QHBoxLayout()
        control_row.setSpacing(10)
        self.battery_slider = QSlider(Qt.Orientation.Horizontal)
        self.battery_slider.setRange(20, 100)
        self.battery_spin = QSpinBox()
        self.battery_spin.setRange(20, 100)
        self.battery_apply_button = primary_button("Apply limit", self._apply_battery_limit)
        control_row.addWidget(self.battery_slider, 1)
        control_row.addWidget(self.battery_spin)
        control_row.addWidget(self.battery_apply_button)
        bc.addLayout(control_row)

        self.battery_slider.valueChanged.connect(self.battery_spin.setValue)
        self.battery_spin.valueChanged.connect(self.battery_slider.setValue)

        self.battery_status = QLabel("")
        self.battery_status.setObjectName("MutedLabel")
        self.battery_status.setWordWrap(True)
        bc.addWidget(self.battery_status)

        bc.addWidget(separator())

        # One-shot charge
        os_header = QLabel("One-shot full charge")
        os_header.setObjectName("SectionTitle")
        os_header.setStyleSheet("font-size: 13px;")
        bc.addWidget(os_header)
        bc.addWidget(
            experimental_notice(
                "Experimental: one-shot charging behavior depends on firmware support and "
                "has limited runtime validation."
            )
        )

        oneshot_row = QHBoxLayout()
        oneshot_row.setSpacing(10)
        os_label = QLabel("Target percent")
        os_label.setObjectName("MutedLabel")
        os_label.setFixedWidth(120)
        self.oneshot_spin = QSpinBox()
        self.oneshot_spin.setRange(20, 100)
        self.oneshot_spin.setValue(100)
        self.oneshot_button = primary_button("Run one-shot", self._apply_oneshot_charge)
        oneshot_row.addWidget(os_label)
        oneshot_row.addWidget(self.oneshot_spin)
        oneshot_row.addWidget(self.oneshot_button)
        oneshot_row.addStretch(1)
        bc.addLayout(oneshot_row)

        bat_layout.addWidget(self._bat_controls)
        parent_layout.addWidget(bat_card)

    # =====================================================================
    # GRAPHICS
    # =====================================================================

    def _build_graphics_section(self, parent_layout: QVBoxLayout) -> None:
        gfx_card, gfx_layout = panel("GRAPHICS")

        self._gfx_unavailable = UnavailableNotice(
            "Graphics switching not available",
            "supergfxctl is not installed or the daemon is not running.",
        )
        gfx_layout.addWidget(self._gfx_unavailable)
        gfx_layout.addWidget(
            experimental_notice(
                "Experimental: graphics mode changes depend on supergfxd, may require logout "
                "or reboot, and still have limited session-safe validation."
            )
        )

        self._gfx_controls = QWidget()
        gc = QVBoxLayout(self._gfx_controls)
        gc.setContentsMargins(0, 0, 0, 0)
        gc.setSpacing(10)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(10)
        ml = QLabel("Graphics mode")
        ml.setObjectName("MutedLabel")
        ml.setFixedWidth(120)
        self.graphics_mode_combo = QComboBox()
        self.graphics_apply_button = primary_button("Request change", self._apply_graphics_mode)
        mode_row.addWidget(ml)
        mode_row.addWidget(self.graphics_mode_combo, 1)
        mode_row.addWidget(self.graphics_apply_button)
        gc.addLayout(mode_row)

        self.graphics_status = QLabel("")
        self.graphics_status.setObjectName("MutedLabel")
        self.graphics_status.setWordWrap(True)
        gc.addWidget(self.graphics_status)

        gfx_layout.addWidget(self._gfx_controls)

        # Firmware attributes sub-section
        gfx_layout.addWidget(separator())
        fw_header = QLabel("Firmware attributes")
        fw_header.setObjectName("SectionTitle")
        fw_header.setStyleSheet("font-size: 13px;")
        gfx_layout.addWidget(fw_header)
        fw_hint = QLabel("Read-only kernel view for troubleshooting.")
        fw_hint.setObjectName("MutedLabel")
        gfx_layout.addWidget(fw_hint)

        self.firmware_table = QTableWidget(0, 4)
        self.firmware_table.setHorizontalHeaderLabels(["Attribute", "Value", "Writable", "Notes"])
        self.firmware_table.verticalHeader().setVisible(False)
        self.firmware_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.firmware_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.firmware_table.horizontalHeader().setStretchLastSection(True)
        self.firmware_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        gfx_layout.addWidget(self.firmware_table)

        parent_layout.addWidget(gfx_card)

    # =====================================================================
    # PUBLIC INTERFACE
    # =====================================================================

    def apply_snapshot(self, snapshot: SystemSnapshot) -> None:
        self._apply_keyboard(snapshot)
        self._apply_aura(snapshot)
        self._apply_battery(snapshot)
        self._apply_graphics(snapshot)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.keyboard_brightness_combo.setEnabled(self._keyboard_supported and not busy)
        self.keyboard_apply_button.setEnabled(self._keyboard_supported and not busy)

        for widget in [
            self.aura_effect_combo,
            self.aura_zone_combo,
            self.aura_speed_combo,
            self.aura_direction_combo,
            self.aura_color_1_button,
            self.aura_color_2_button,
            self.aura_apply_button,
        ]:
            widget.setEnabled(self._aura_supported and not busy)
        for button in self._aura_power_buttons:
            button.setEnabled(self._aura_supported and not busy)

        for widget in [
            self.battery_slider,
            self.battery_spin,
            self.battery_apply_button,
            self.oneshot_spin,
            self.oneshot_button,
        ]:
            widget.setEnabled(self._battery_supported and not busy)

        can_change_graphics = self._graphics_can_switch and not self._graphics_pending and not busy
        self.graphics_mode_combo.setEnabled(can_change_graphics)
        self.graphics_apply_button.setEnabled(can_change_graphics)

    def save_state(self, settings) -> None:
        # Aura settings are persisted on apply, nothing extra needed
        pass

    # =====================================================================
    # SNAPSHOT APPLICATION
    # =====================================================================

    def _apply_keyboard(self, snapshot: SystemSnapshot) -> None:
        supported = snapshot.keyboard.supported
        self._keyboard_supported = supported
        self._kb_unavailable.setVisible(not supported)
        self._kb_controls.setVisible(supported)
        if not supported:
            self._kb_unavailable.set_text(
                "Keyboard brightness not available",
                snapshot.keyboard.message or "Not supported on this device.",
            )
        if snapshot.keyboard.brightness:
            self.keyboard_brightness_combo.setCurrentText(snapshot.keyboard.brightness)
        self.keyboard_status.setText(
            snapshot.keyboard.message
            or f"Current brightness: {snapshot.keyboard.brightness or 'unknown'}"
        )
        self.keyboard_brightness_combo.setEnabled(supported and not self._busy)
        self.keyboard_apply_button.setEnabled(supported and not self._busy)

    def _apply_aura(self, snapshot: SystemSnapshot) -> None:
        supported = snapshot.aura.supported
        self._aura_supported = supported
        self._aura_unavailable.setVisible(not supported)
        self._aura_controls.setVisible(supported)
        if not supported:
            self._aura_unavailable.set_text(
                "Aura lighting not available",
                snapshot.aura.message or "Not supported on this device.",
            )

        available_effects = [
            self._effect_commands[cmd]
            for cmd in snapshot.aura.effects
            if cmd in self._effect_commands
        ]
        if not available_effects:
            available_effects = [display for display, _ in AURA_EFFECTS]
        self._set_combo_items(self.aura_effect_combo, available_effects, self.settings.aura_effect)

        zone_items = ["Default device zone"] + list(snapshot.aura.zones)
        selected_zone = self.settings.aura_zone if self.settings.aura_zone else "Default device zone"
        self._set_combo_items(self.aura_zone_combo, zone_items, selected_zone)

        self.aura_status.setText(
            snapshot.aura.message or "Aura writes go through the installed asusctl CLI."
        )

        for w in [
            self.aura_effect_combo, self.aura_zone_combo,
            self.aura_speed_combo, self.aura_direction_combo,
            self.aura_color_1_button, self.aura_color_2_button,
            self.aura_apply_button,
        ]:
            w.setEnabled(supported and not self._busy)

        self._populate_aura_power_grid(snapshot)
        self._update_aura_visibility()

    def _apply_battery(self, snapshot: SystemSnapshot) -> None:
        supported = snapshot.battery.supported
        self._battery_supported = supported
        self._bat_unavailable.setVisible(not supported)
        self._bat_controls.setVisible(supported)
        if not supported:
            self._bat_unavailable.set_text(
                "Battery charge limit not available",
                snapshot.battery.message or "Not supported on this device.",
            )

        value = snapshot.battery.limit if snapshot.battery.limit is not None else 100
        battery_text = (
            str(snapshot.battery.limit) if snapshot.battery.limit is not None else "—"
        )
        self.battery_limit_value.setText(battery_text)
        self.battery_slider.setValue(value)
        self.battery_status.setText(snapshot.battery.message or "Battery limit control detected.")

        for w in [self.battery_slider, self.battery_spin, self.battery_apply_button,
                   self.oneshot_spin, self.oneshot_button]:
            w.setEnabled(supported and not self._busy)

    def _apply_graphics(self, snapshot: SystemSnapshot) -> None:
        self._graphics_installed = snapshot.graphics.installed
        self._graphics_can_switch = bool(snapshot.graphics.supported_modes)
        self._graphics_pending = bool(snapshot.graphics.pending_action)
        has_gfx = snapshot.graphics.installed

        self._gfx_unavailable.setVisible(not has_gfx)
        self._gfx_controls.setVisible(has_gfx)

        if not has_gfx:
            self._gfx_unavailable.set_text(
                "Graphics switching not available",
                snapshot.graphics.message or "supergfxctl is not installed or the daemon is not running.",
            )

        mode_items = snapshot.graphics.supported_modes[:]
        if snapshot.graphics.current_mode and snapshot.graphics.current_mode not in mode_items:
            mode_items.append(snapshot.graphics.current_mode)
        if snapshot.graphics.pending_mode and snapshot.graphics.pending_mode not in mode_items:
            mode_items.append(snapshot.graphics.pending_mode)

        selection = (
            snapshot.graphics.pending_mode
            if snapshot.graphics.pending_mode and snapshot.graphics.pending_mode in mode_items
            else snapshot.graphics.current_mode
            or (mode_items[0] if mode_items else "")
        )
        self._set_combo_items(self.graphics_mode_combo, mode_items, selection)

        status_parts = []
        if snapshot.graphics.current_mode:
            status_parts.append(f"Current mode: {snapshot.graphics.current_mode}")
        if snapshot.graphics.vendor:
            status_parts.append(f"Vendor: {snapshot.graphics.vendor}")
        if snapshot.graphics.power_status:
            status_parts.append(f"Power: {snapshot.graphics.power_status}")
        if snapshot.graphics.pending_action:
            pending = snapshot.graphics.pending_mode or "?"
            status_parts.append(f"Pending: {snapshot.graphics.pending_action} → {pending}")
            status_parts.append("Mode changes are locked until the pending transition completes.")
        if snapshot.graphics.message:
            status_parts.append(snapshot.graphics.message)
        self.graphics_status.setText("  |  ".join(status_parts) if status_parts else "")

        can_change_graphics = self._graphics_can_switch and not self._graphics_pending and not self._busy
        self.graphics_mode_combo.setEnabled(can_change_graphics)
        self.graphics_apply_button.setEnabled(can_change_graphics)

        # Firmware table
        self.firmware_table.setRowCount(len(snapshot.firmware_attributes))
        for row, attr in enumerate(snapshot.firmware_attributes):
            self.firmware_table.setItem(row, 0, QTableWidgetItem(attr.label))
            self.firmware_table.setItem(row, 1, QTableWidgetItem(attr.value))
            self.firmware_table.setItem(row, 2, QTableWidgetItem("Yes" if attr.writable else "No"))
            self.firmware_table.setItem(row, 3, QTableWidgetItem(attr.note))

    # =====================================================================
    # AURA HELPERS
    # =====================================================================

    def _update_aura_visibility(self) -> None:
        label = self.aura_effect_combo.currentText()
        effect = self._effect_labels.get(label, label.lower())
        needs_secondary = effect == "breathe"
        needs_speed = effect in {"breathe", "rainbow-cycle", "rainbow-wave"}
        needs_direction = effect == "rainbow-wave"
        self.aura_color_2_button.setVisible(needs_secondary)
        self._speed_direction_row.setVisible(needs_speed or needs_direction)
        self._speed_label.setVisible(needs_speed)
        self.aura_speed_combo.setVisible(needs_speed)
        self._direction_label.setVisible(needs_direction)
        self.aura_direction_combo.setVisible(needs_direction)

    def _pick_aura_color_1(self) -> None:
        color = QColorDialog.getColor(QColor(self._pending_aura_color_1), self, "Primary aura color")
        if color.isValid():
            self._pending_aura_color_1 = color.name()
            self._update_color_button(self.aura_color_1_button, color.name())

    def _pick_aura_color_2(self) -> None:
        color = QColorDialog.getColor(QColor(self._pending_aura_color_2), self, "Secondary aura color")
        if color.isValid():
            self._pending_aura_color_2 = color.name()
            self._update_color_button(self.aura_color_2_button, color.name())

    @staticmethod
    def _update_color_button(button: QPushButton, color: str) -> None:
        text_color = "#ffffff" if QColor(color).lightness() < 140 else "#1a1a1a"
        button.setStyleSheet(
            f"background: {color}; color: {text_color}; "
            "border: 1px solid #e0e0e0; border-radius: 6px; padding: 7px 16px; font-weight: 600;"
        )

    def _populate_aura_power_grid(self, snapshot: SystemSnapshot) -> None:
        while self.aura_power_grid.count():
            item = self.aura_power_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._aura_power_buttons = []
        zones = snapshot.aura.zones or []
        if not zones:
            lbl = QLabel("No aura power zones reported on this machine.")
            lbl.setObjectName("MutedLabel")
            self.aura_power_grid.addWidget(lbl, 0, 0)
            return
        for row, zone in enumerate(zones):
            label = QLabel(zone.replace("-", " ").title())
            label.setObjectName("BodyLabel")
            enable_btn = secondary_button(
                "Enable all",
                lambda checked=False, name=zone: self.controller.set_aura_power(name, True),
            )
            disable_btn = secondary_button(
                "Disable all",
                lambda checked=False, name=zone: self.controller.set_aura_power(name, False),
            )
            enabled = snapshot.aura.supported and not self._busy
            enable_btn.setEnabled(enabled)
            disable_btn.setEnabled(enabled)
            self._aura_power_buttons.extend([enable_btn, disable_btn])
            self.aura_power_grid.addWidget(label, row, 0)
            self.aura_power_grid.addWidget(enable_btn, row, 1)
            self.aura_power_grid.addWidget(disable_btn, row, 2)

    # =====================================================================
    # ACTION SLOTS
    # =====================================================================

    def _apply_keyboard_brightness(self) -> None:
        if self._busy or not self._keyboard_supported:
            return
        self.controller.set_keyboard_brightness(self.keyboard_brightness_combo.currentText())

    def _apply_aura_effect(self) -> None:
        if self._busy or not self._aura_supported:
            return
        effect_label = self.aura_effect_combo.currentText()
        effect = self._effect_labels.get(effect_label, effect_label.lower())
        zone_text = self.aura_zone_combo.currentText()
        zone = "" if zone_text == "Default device zone" else zone_text
        # Persist on apply only
        self.settings.aura_effect = effect_label
        self.settings.aura_zone = zone
        self.settings.aura_color_1 = self._pending_aura_color_1
        self.settings.aura_color_2 = self._pending_aura_color_2
        self.controller.apply_aura_effect(
            effect,
            self._pending_aura_color_1,
            self._pending_aura_color_2,
            self.aura_speed_combo.currentText(),
            self.aura_direction_combo.currentText(),
            zone,
        )

    def _apply_battery_limit(self) -> None:
        if self._busy or not self._battery_supported:
            return
        self.controller.set_battery_limit(self.battery_spin.value())

    def _apply_oneshot_charge(self) -> None:
        if self._busy or not self._battery_supported:
            return
        self.controller.oneshot_charge(self.oneshot_spin.value())

    def _apply_graphics_mode(self) -> None:
        if self._busy or not self._graphics_can_switch or self._graphics_pending:
            return
        mode = self.graphics_mode_combo.currentText().strip()
        if not mode:
            return
        reply = QMessageBox.question(
            self,
            "Confirm graphics mode change",
            f"Switch graphics mode to {mode}?\n\n"
            "Some mode transitions require a full logout or reboot to complete. "
            "Unsaved work in other applications may be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.set_graphics_mode(mode)

    # =====================================================================
    # HELPERS
    # =====================================================================

    @staticmethod
    def _set_combo_items(combo: QComboBox, values: list[str], selected: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        if selected and selected in values:
            combo.setCurrentText(selected)
        combo.blockSignals(False)
