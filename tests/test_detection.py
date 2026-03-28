"""Tests for ControlService (detection.py) — snapshot building and warnings."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from asus_linux_control_center.models import (
    AuraState,
    BatteryState,
    DeviceInfo,
    FanCurveState,
    GraphicsState,
    IntegrationState,
    KeyboardState,
    ProfileState,
)
from asus_linux_control_center.services.detection import ControlService


def _make_service() -> ControlService:
    return ControlService(logging.getLogger("test"))


# ─── build_snapshot ───────────────────────────────────────────────────────────


@patch("asus_linux_control_center.services.detection.read_os_release", return_value=("Arch Linux", "arch"))
@patch("asus_linux_control_center.services.detection.platform")
def test_build_snapshot_asusctl_not_installed(mock_platform: MagicMock, _mock_os: MagicMock) -> None:
    mock_platform.release.return_value = "6.12.8"
    mock_platform.node.return_value = "testhost"

    service = _make_service()

    # Simulate asusctl not installed
    service.asusctl = MagicMock()
    service.asusctl.available = False
    service.supergfxctl = MagicMock()
    service.supergfxctl.inspect.return_value = GraphicsState(installed=False)
    service.firmware = MagicMock()
    service.firmware.inspect.return_value = []
    service.runner = MagicMock()
    service.runner.systemctl_state.return_value = "inactive"
    service.runner.systemctl_enabled_state.return_value = "disabled"
    service.runner.bus_name_exists.return_value = False

    snapshot = service.build_snapshot()
    assert snapshot.profiles.message == "asusctl is not installed."
    assert snapshot.battery.message == "asusctl is not installed."
    assert snapshot.device.kernel == "6.12.8"
    assert snapshot.device.hostname == "testhost"


@patch("asus_linux_control_center.services.detection.read_os_release", return_value=("Arch Linux", "arch"))
@patch("asus_linux_control_center.services.detection.platform")
def test_build_snapshot_asusctl_available(mock_platform: MagicMock, _mock_os: MagicMock) -> None:
    mock_platform.release.return_value = "6.12.8"
    mock_platform.node.return_value = "testhost"

    service = _make_service()
    service.runner = MagicMock()
    service.runner.systemctl_state.return_value = "active"
    service.runner.systemctl_enabled_state.return_value = "enabled"
    service.runner.bus_name_exists.return_value = True

    service.asusctl = MagicMock()
    service.asusctl.available = True
    service.asusctl.inspect_device.return_value = DeviceInfo(
        product_family="ROG Strix", board_name="G614JV", asusctl_version="6.3.5",
    )
    service.asusctl.inspect_profiles.return_value = ProfileState(
        supported=True, available=["Quiet", "Balanced", "Performance"], active="Performance",
    )
    service.asusctl.inspect_fan_curve.return_value = FanCurveState(supported=True)
    service.asusctl.inspect_battery.return_value = BatteryState(supported=True, limit=80)
    service.asusctl.inspect_keyboard.return_value = KeyboardState(supported=True, brightness="high")
    service.asusctl.inspect_aura.return_value = AuraState(supported=True)

    service.supergfxctl = MagicMock()
    service.supergfxctl.inspect.return_value = GraphicsState(installed=True, supported_modes=["Hybrid"])
    service.firmware = MagicMock()
    service.firmware.inspect.return_value = []

    snapshot = service.build_snapshot(fan_profile="Performance")
    assert snapshot.device.product_family == "ROG Strix"
    assert snapshot.profiles.active == "Performance"
    assert snapshot.battery.limit == 80
    assert snapshot.timestamp


# ─── _build_warnings ─────────────────────────────────────────────────────────


def test_warnings_debian_family() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="ubuntu",
        integration=IntegrationState(asusd_service="active", asusd_bus_name=True),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert any("Debian" in w for w in warnings)


def test_warnings_asusd_inactive() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(asusd_service="inactive", asusd_bus_name=True),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert any("asusd.service" in w for w in warnings)


def test_warnings_dbus_missing() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(asusd_service="active", asusd_bus_name=False),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert any("D-Bus" in w for w in warnings)


def test_warnings_profiles_yes_fan_no() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(asusd_service="active", asusd_bus_name=True),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=False),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert any("fan curve" in w.lower() for w in warnings)


def test_warnings_battery_unsupported() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(asusd_service="active", asusd_bus_name=True),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=False),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert any("battery" in w.lower() for w in warnings)


def test_warnings_supergfxctl_not_installed() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(asusd_service="active", asusd_bus_name=True),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=False),
    )
    assert any("Graphics switching is optional" in w for w in warnings)


def test_warnings_supergfxd_not_ready() -> None:
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(
            asusd_service="active", asusd_bus_name=True,
            supergfxd_service="inactive", supergfxd_bus_name=False,
        ),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert any("supergfxd" in w.lower() for w in warnings)


def test_warnings_clean_system() -> None:
    """No warnings on a fully healthy Arch system."""
    service = _make_service()
    warnings = service._build_warnings(
        distro_id="arch",
        integration=IntegrationState(
            asusd_service="active", asusd_bus_name=True,
            supergfxd_service="active", supergfxd_bus_name=True,
        ),
        profiles=ProfileState(supported=True),
        fan_curve=FanCurveState(supported=True),
        battery=BatteryState(supported=True),
        graphics=GraphicsState(installed=True, supported_modes=["Hybrid"]),
    )
    assert warnings == []


# ─── action passthrough ──────────────────────────────────────────────────────


def test_service_set_profile_delegates() -> None:
    service = _make_service()
    service.asusctl = MagicMock()
    from asus_linux_control_center.models import ActionOutcome
    service.asusctl.set_profile.return_value = ActionOutcome("Profile", True, "ok")
    result = service.set_profile("Performance")
    service.asusctl.set_profile.assert_called_once_with("Performance")
    assert result.success


def test_service_set_graphics_mode_delegates() -> None:
    service = _make_service()
    service.supergfxctl = MagicMock()
    from asus_linux_control_center.models import ActionOutcome
    service.supergfxctl.set_mode.return_value = ActionOutcome("Graphics", True, "switched")
    result = service.set_graphics_mode("Hybrid")
    service.supergfxctl.set_mode.assert_called_once_with("Hybrid")
    assert result.success
