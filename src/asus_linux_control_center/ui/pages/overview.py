"""Home page — dashboard with device identity, mode bar, and telemetry panels."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...models import SystemSnapshot
from ...services import format_diagnostics_report
from ..components import (
    action_bar,
    mode_bar,
    page_header,
    panel,
    primary_button,
    secondary_button,
    stat_row,
)
from ..widgets.status_indicator import StatusIndicator


class OverviewPage(QWidget):
    """Dashboard with device identity, operating-mode bar, and telemetry panels."""

    def __init__(self, controller, settings):
        super().__init__()
        self.controller = controller
        self.settings = settings
        self._snapshot: SystemSnapshot | None = None
        self._busy = False
        self._profiles_supported = False
        self._available_profiles: list[str] = []
        self._active_profile = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header("Home", "Device identity and system status"))

        # -- Operating mode bar --
        self._mode_frame, self._mode_buttons = mode_bar(
            [
                ("Quiet", "\U0001f54a  Quiet"),
                ("Balanced", "\u2696  Balanced"),
                ("Performance", "\U0001f525  Performance"),
            ],
            callback=self._apply_profile,
        )
        layout.addWidget(self._mode_frame)

        # -- 2-column dashboard grid --
        dash = QGridLayout()
        dash.setSpacing(12)
        dash.setColumnStretch(0, 1)
        dash.setColumnStretch(1, 1)

        # -- Left column: Device panel --
        dev_panel, dev_layout = panel("SYSTEM INFO")
        self._dev_fields: dict[str, tuple[QLabel, QLabel]] = {}
        for key, label in [
            ("device", "Device"),
            ("board", "Board"),
            ("kernel", "Kernel"),
            ("distro", "Distribution"),
            ("asusctl", "asusctl"),
        ]:
            container, lbl_w, val_w = stat_row(label, "—")
            self._dev_fields[key] = (lbl_w, val_w)
            dev_layout.addWidget(container)
        dash.addWidget(dev_panel, 0, 0)

        # -- Right column: Services panel --
        svc_panel, svc_layout = panel("SERVICES")
        self._svc_fields: dict[str, tuple[QLabel, QLabel]] = {}
        for key, label in [
            ("asusd", "asusd"),
            ("supergfxd", "supergfxd"),
            ("profile", "Active profile"),
        ]:
            container, lbl_w, val_w = stat_row(label, "—")
            self._svc_fields[key] = (lbl_w, val_w)
            svc_layout.addWidget(container)
        dash.addWidget(svc_panel, 0, 1)

        # -- Capabilities panel (spans full width) --
        cap_panel, cap_layout = panel("CAPABILITIES")
        self._cap_grid = QGridLayout()
        self._cap_grid.setSpacing(6)
        self._indicators: dict[str, StatusIndicator] = {}
        capabilities = [
            ("profiles", "Performance profiles"),
            ("fan_curves", "Fan curve control"),
            ("keyboard", "Keyboard brightness"),
            ("aura", "Aura lighting"),
            ("battery", "Battery charge limit"),
            ("graphics", "Graphics switching"),
        ]
        for i, (key, label) in enumerate(capabilities):
            indicator = StatusIndicator(f"{label}: —", "unavailable")
            self._indicators[key] = indicator
            row_i, col_i = divmod(i, 3)
            self._cap_grid.addWidget(indicator, row_i, col_i)
        cap_layout.addLayout(self._cap_grid)
        dash.addWidget(cap_panel, 1, 0, 1, 2)

        layout.addLayout(dash)

        # -- Warnings banner --
        self._warning_frame = QFrame()
        self._warning_frame.setObjectName("WarningBanner")
        warn_layout = QVBoxLayout(self._warning_frame)
        warn_layout.setContentsMargins(14, 10, 14, 10)
        warn_layout.setSpacing(4)
        warn_title = QLabel("\u26a0  Warnings")
        warn_title.setObjectName("SectionTitle")
        warn_title.setStyleSheet("font-size: 13px;")
        warn_layout.addWidget(warn_title)
        self._warning_label = QLabel("")
        self._warning_label.setObjectName("BodyLabel")
        self._warning_label.setWordWrap(True)
        warn_layout.addWidget(self._warning_label)
        self._warning_frame.setVisible(False)
        layout.addWidget(self._warning_frame)

        # -- Quick actions --
        self._refresh_btn = primary_button("Refresh", self._request_refresh)
        self._copy_btn = secondary_button("Copy diagnostics", self._copy_diagnostics)
        self._copy_btn.setEnabled(False)
        layout.addLayout(action_bar(self._copy_btn, self._refresh_btn, align_left=True))

        layout.addStretch(1)

    # -- Public interface --------------------------------------------------

    def apply_snapshot(self, snapshot: SystemSnapshot) -> None:
        self._snapshot = snapshot
        active_profile = snapshot.profiles.active or "—"
        self._active_profile = snapshot.profiles.active or ""
        self._profiles_supported = snapshot.profiles.supported
        self._available_profiles = snapshot.profiles.available[:]

        # Device panel
        self._dev_fields["device"][1].setText(snapshot.device.product_family or "ASUS Device")
        self._dev_fields["board"][1].setText(snapshot.device.board_name)
        self._dev_fields["kernel"][1].setText(snapshot.device.kernel)
        self._dev_fields["distro"][1].setText(snapshot.device.distro or "Unknown")
        self._dev_fields["asusctl"][1].setText(snapshot.device.asusctl_version)

        # Services panel
        self._svc_fields["asusd"][1].setText(snapshot.integration.asusd_service)
        self._svc_fields["supergfxd"][1].setText(
            f"{snapshot.integration.supergfxd_service}"
            f" ({snapshot.integration.supergfxd_enabled})"
        )
        self._svc_fields["profile"][1].setText(active_profile)

        # Mode bar state
        self._sync_mode_buttons()

        def _cap(supported: bool) -> tuple[str, str]:
            return ("Available", "available") if supported else ("Not available", "unavailable")

        graphics_status = "unavailable"
        graphics_text = "Not available"
        if snapshot.graphics.installed:
            if (
                snapshot.integration.supergfxd_service == "active"
                and snapshot.integration.supergfxd_bus_name
            ):
                graphics_status, graphics_text = "available", "Ready"
            else:
                graphics_status, graphics_text = "warning", "Daemon unavailable"

        self._indicators["profiles"].set_status(
            f"Performance profiles: {_cap(snapshot.profiles.supported)[0]}",
            _cap(snapshot.profiles.supported)[1],
        )
        self._indicators["fan_curves"].set_status(
            f"Fan curve control: {_cap(snapshot.fan_curve.supported)[0]}",
            _cap(snapshot.fan_curve.supported)[1],
        )
        self._indicators["keyboard"].set_status(
            f"Keyboard brightness: {_cap(snapshot.keyboard.supported)[0]}",
            _cap(snapshot.keyboard.supported)[1],
        )
        self._indicators["aura"].set_status(
            f"Aura lighting: {_cap(snapshot.aura.supported)[0]}",
            _cap(snapshot.aura.supported)[1],
        )
        self._indicators["battery"].set_status(
            f"Battery charge limit: {_cap(snapshot.battery.supported)[0]}",
            _cap(snapshot.battery.supported)[1],
        )
        self._indicators["graphics"].set_status(
            f"Graphics switching: {graphics_text}",
            graphics_status,
        )

        if snapshot.warnings:
            self._warning_label.setText("\n".join(f"\u2022 {w}" for w in snapshot.warnings))
            self._warning_frame.setVisible(True)
        else:
            self._warning_frame.setVisible(False)

        self._copy_btn.setEnabled(not self._busy)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._refresh_btn.setEnabled(not busy)
        self._copy_btn.setEnabled(self._snapshot is not None and not busy)
        self._sync_mode_buttons()

    def save_state(self, settings) -> None:
        pass  # Overview has no persistent state

    # -- Slots -------------------------------------------------------------

    def _request_refresh(self) -> None:
        self.controller.refresh()

    def _copy_diagnostics(self) -> None:
        if self._snapshot:
            QApplication.clipboard().setText(format_diagnostics_report(self._snapshot))

    def _apply_profile(self, name: str) -> None:
        if self._busy or not self._profiles_supported or name == self._active_profile:
            self._sync_mode_buttons()
            return
        # Keep the mode bar truthful to the last confirmed snapshot while
        # the request is in flight. The status bar cursor change provides
        # pending feedback without claiming success before confirmation.
        self._sync_mode_buttons()
        self.controller.set_profile(name)

    def _sync_mode_buttons(self) -> None:
        for name, btn in self._mode_buttons.items():
            btn.setChecked(name == self._active_profile)
            btn.setEnabled(
                self._profiles_supported and name in self._available_profiles and not self._busy
            )
