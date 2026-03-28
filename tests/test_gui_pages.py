from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6")
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication, QMessageBox

from asus_linux_control_center.constants import DEFAULT_FAN_TEMPS
from asus_linux_control_center.models import (
    AuraState,
    BatteryState,
    DeviceInfo,
    FanCurveSnapshot,
    FanCurveState,
    GraphicsState,
    IntegrationState,
    KeyboardState,
    ProfileState,
    SettingsData,
    SystemSnapshot,
)
from asus_linux_control_center.ui.pages.diagnostics import DiagnosticsPage
from asus_linux_control_center.ui.pages.hardware import HardwarePage
from asus_linux_control_center.ui.pages.overview import OverviewPage
from asus_linux_control_center.ui.pages.performance import PerformancePage
from asus_linux_control_center.ui.pages.settings import SettingsPage


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def _make_snapshot(
    *,
    profiles: ProfileState | None = None,
    fan_curve: FanCurveState | None = None,
    battery: BatteryState | None = None,
    keyboard: KeyboardState | None = None,
    aura: AuraState | None = None,
    graphics: GraphicsState | None = None,
) -> SystemSnapshot:
    default_fans = {
        "cpu": [24, 36, 46, 58, 68, 78, 90, 100],
        "gpu": [24, 36, 46, 58, 68, 78, 90, 100],
        "mid": [20, 32, 42, 52, 62, 72, 84, 94],
    }
    return SystemSnapshot(
        device=DeviceInfo(
            product_family="ROG Strix",
            board_name="G614JV",
            asusctl_version="6.3.5",
            kernel="6.17.0-19-generic",
            distro="Ubuntu 25.10",
            hostname="osa",
        ),
        integration=IntegrationState(
            asusd_service="active",
            asusd_bus_name=True,
            supergfxd_service="active",
            supergfxd_enabled="enabled",
            supergfxd_bus_name=True,
        ),
        profiles=profiles
        or ProfileState(
            supported=True,
            available=["Quiet", "Balanced", "Performance"],
            active="Performance",
        ),
        fan_curve=fan_curve
        or FanCurveState(
            supported=True,
            probe_profile="Performance",
            snapshot=FanCurveSnapshot(
                temps=DEFAULT_FAN_TEMPS[:],
                fans={fan: values[:] for fan, values in default_fans.items()},
                enabled={fan: True for fan in default_fans},
            ),
        ),
        battery=battery or BatteryState(supported=True, limit=80),
        keyboard=keyboard or KeyboardState(supported=True, brightness="low"),
        aura=aura
        or AuraState(
            supported=True,
            effects=["static", "breathe", "rainbow-wave"],
            zones=["keyboard", "logo"],
        ),
        graphics=graphics
        or GraphicsState(
            installed=True,
            current_mode="Integrated",
            supported_modes=["Hybrid", "Integrated"],
            vendor="Nvidia",
            power_status="off",
        ),
        firmware_attributes=[],
        warnings=[],
        timestamp="2026-03-28T04:20:00",
    )


def test_overview_profile_click_sets_profile_only(qapp) -> None:
    controller = MagicMock()
    page = OverviewPage(controller, SettingsData())
    page.apply_snapshot(_make_snapshot())

    page._mode_buttons["Balanced"].click()

    controller.set_profile.assert_called_once_with("Balanced")
    controller.apply_profile_and_curves.assert_not_called()


def test_overview_busy_roundtrip_preserves_available_modes(qapp) -> None:
    controller = MagicMock()
    page = OverviewPage(controller, SettingsData())
    snapshot = _make_snapshot(
        profiles=ProfileState(
            supported=True,
            available=["Balanced"],
            active="Balanced",
        ),
    )
    page.apply_snapshot(snapshot)

    assert page._mode_buttons["Balanced"].isEnabled()
    assert not page._mode_buttons["Quiet"].isEnabled()

    page.set_busy(True)
    page.set_busy(False)

    assert page._mode_buttons["Balanced"].isEnabled()
    assert not page._mode_buttons["Quiet"].isEnabled()


def test_performance_profile_selection_is_local_until_apply(qapp) -> None:
    controller = MagicMock()
    page = PerformancePage(controller, SettingsData())
    page.apply_snapshot(_make_snapshot())

    page._mode_buttons["Balanced"].click()

    controller.set_profile.assert_not_called()
    controller.apply_profile_and_curves.assert_not_called()
    assert page.active_profile_value.text() == "Performance"
    assert page._selected_profile == "Balanced"
    assert "Selected profile: Balanced" in page.selection_status.text()


def test_performance_busy_roundtrip_preserves_available_modes(qapp) -> None:
    controller = MagicMock()
    page = PerformancePage(controller, SettingsData())
    snapshot = _make_snapshot(
        profiles=ProfileState(
            supported=True,
            available=["Performance"],
            active="Performance",
        ),
    )
    page.apply_snapshot(snapshot)

    assert page._mode_buttons["Performance"].isEnabled()
    assert not page._mode_buttons["Quiet"].isEnabled()

    page.set_busy(True)
    assert page.curve_editor._readonly is True
    page.set_busy(False)

    assert page._mode_buttons["Performance"].isEnabled()
    assert not page._mode_buttons["Quiet"].isEnabled()


def test_performance_apply_filters_missing_fans(qapp) -> None:
    controller = MagicMock()
    page = PerformancePage(controller, SettingsData())
    snapshot = _make_snapshot(
        fan_curve=FanCurveState(
            supported=True,
            probe_profile="Performance",
            snapshot=FanCurveSnapshot(
                temps=DEFAULT_FAN_TEMPS[:],
                fans={
                    "cpu": [24, 36, 46, 58, 68, 78, 90, 100],
                    "gpu": [24, 36, 46, 58, 68, 78, 90, 100],
                },
                enabled={"cpu": True, "gpu": True},
            ),
        ),
    )
    page.apply_snapshot(snapshot)
    page.edited_curves["mid"] = [100] * len(DEFAULT_FAN_TEMPS)

    page._apply_all()

    payload = controller.apply_profile_and_curves.call_args.args[1]
    assert set(payload) == {"cpu", "gpu"}
    assert page.channel_buttons["mid"].isHidden()


def test_performance_profile_only_refresh_clears_waiting_state(qapp) -> None:
    controller = MagicMock()
    page = PerformancePage(controller, SettingsData())
    page._selected_profile = "Balanced"
    page._profile_dirty = True
    page._awaiting_profile_curves = "Balanced"

    page.apply_snapshot(
        _make_snapshot(
            profiles=ProfileState(
                supported=True,
                available=["Quiet", "Balanced", "Performance"],
                active="Balanced",
            ),
            fan_curve=FanCurveState(
                supported=False,
                message="Fan curve editing is not available on this device.",
            ),
        )
    )

    assert page._awaiting_profile_curves is None
    assert page._profile_dirty is False
    assert page.profile_apply_button.isEnabled() is False


def test_hardware_aura_direction_controls_restore_when_needed(qapp) -> None:
    controller = MagicMock()
    page = HardwarePage(controller, SettingsData())
    page.apply_snapshot(_make_snapshot())

    page.aura_effect_combo.setCurrentText("Breathe")
    page._update_aura_visibility()
    assert page.aura_direction_combo.isHidden()

    page.aura_effect_combo.setCurrentText("Rainbow Wave")
    page._update_aura_visibility()
    assert not page.aura_direction_combo.isHidden()


def test_hardware_pending_graphics_stays_visible_but_locked(qapp) -> None:
    controller = MagicMock()
    page = HardwarePage(controller, SettingsData())
    snapshot = _make_snapshot(
        graphics=GraphicsState(
            installed=True,
            current_mode="Hybrid",
            supported_modes=[],
            pending_action="Logout required",
            pending_mode="Integrated",
            message="Graphics mode change is pending.",
        ),
    )

    page.apply_snapshot(snapshot)

    assert not page._gfx_controls.isHidden()
    assert page._gfx_unavailable.isHidden()
    assert not page.graphics_apply_button.isEnabled()
    assert "Pending:" in page.graphics_status.text()


def test_diagnostics_save_failure_shows_warning(qapp, monkeypatch) -> None:
    controller = MagicMock()
    page = DiagnosticsPage(controller, SettingsData())
    assert not page._copy_btn.isEnabled()
    assert not page._save_btn.isEnabled()

    page.apply_snapshot(_make_snapshot())
    assert page._copy_btn.isEnabled()
    assert page._save_btn.isEnabled()

    monkeypatch.setattr(
        "asus_linux_control_center.ui.pages.diagnostics.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("/tmp/report.txt", "Text files (*.txt)"),
    )
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")))
    warnings: list[tuple[object, ...]] = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    page._save()

    assert warnings
    assert "Could not save" in warnings[0][2]


def test_settings_open_path_failure_shows_warning(qapp, monkeypatch) -> None:
    page = SettingsPage(MagicMock(), SettingsData())
    warnings: list[tuple[object, ...]] = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    page._open_path(Path("/tmp/missing"))

    assert warnings
    assert "/tmp/missing" in warnings[0][2]
