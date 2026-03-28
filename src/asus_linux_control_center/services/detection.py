from __future__ import annotations

import logging
import platform
from datetime import datetime

from ..backends import AsusCtlBackend, AsusFirmwareBackend, CommandRunner, SupergfxCtlBackend
from ..models import (
    ActionOutcome,
    AuraState,
    BatteryState,
    DeviceInfo,
    FanCurveState,
    GraphicsState,
    IntegrationState,
    KeyboardState,
    ProfileState,
    SystemSnapshot,
)
from ..utils import read_os_release


class ControlService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.runner = CommandRunner(logger)
        self.asusctl = AsusCtlBackend(self.runner)
        self.supergfxctl = SupergfxCtlBackend(self.runner)
        self.firmware = AsusFirmwareBackend()

    def build_snapshot(self, fan_profile: str | None = None) -> SystemSnapshot:
        distro_name, distro_id = read_os_release()
        device = DeviceInfo(
            kernel=platform.release(),
            distro=distro_name,
            hostname=platform.node(),
        )
        integration = IntegrationState(
            asusctl_path=self.asusctl.binary,
            asusd_service=self.runner.systemctl_state("asusd.service"),
            asusd_bus_name=self.runner.bus_name_exists("xyz.ljones.Asusd"),
            supergfxctl_path=self.supergfxctl.binary,
            supergfxd_service=self.runner.systemctl_state("supergfxd.service"),
            supergfxd_enabled=self.runner.systemctl_enabled_state("supergfxd.service"),
            supergfxd_bus_name=self.runner.bus_name_exists("org.supergfxctl.Daemon"),
        )

        profiles = ProfileState(message="asusctl is not installed.")
        fan_curve = FanCurveState(message="asusctl is not installed.")
        battery = BatteryState(message="asusctl is not installed.")
        keyboard = KeyboardState(message="asusctl is not installed.")
        aura = AuraState(message="asusctl is not installed.")
        graphics = self.supergfxctl.inspect()

        if self.asusctl.available:
            detected = self.asusctl.inspect_device()
            device.product_family = detected.product_family
            device.board_name = detected.board_name
            device.asusctl_version = detected.asusctl_version
            profiles = self.asusctl.inspect_profiles()
            fan_curve = self.asusctl.inspect_fan_curve(fan_profile, profiles)
            battery = self.asusctl.inspect_battery()
            keyboard = self.asusctl.inspect_keyboard()
            aura = self.asusctl.inspect_aura()

        warnings = self._build_warnings(
            distro_id=distro_id,
            integration=integration,
            profiles=profiles,
            fan_curve=fan_curve,
            battery=battery,
            graphics=graphics,
        )
        return SystemSnapshot(
            device=device,
            integration=integration,
            profiles=profiles,
            fan_curve=fan_curve,
            battery=battery,
            keyboard=keyboard,
            aura=aura,
            graphics=graphics,
            firmware_attributes=self.firmware.inspect(),
            warnings=warnings,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def _build_warnings(
        self,
        distro_id: str,
        integration: IntegrationState,
        profiles: ProfileState,
        fan_curve: FanCurveState,
        battery: BatteryState,
        graphics: GraphicsState,
    ) -> list[str]:
        warnings: list[str] = []
        if distro_id in {"ubuntu", "debian", "pop"}:
            warnings.append(
                "Debian and Ubuntu families are still described by the ASUS Linux project "
                "as not officially supported; newer kernels generally behave better."
            )
        if integration.asusd_service != "active":
            warnings.append("`asusd.service` is not active, so write operations may fail.")
        if not integration.asusd_bus_name:
            warnings.append("The `xyz.ljones.Asusd` system D-Bus name was not detected.")
        if profiles.supported and not fan_curve.supported:
            warnings.append(
                "Performance profiles are available, but fan curve editing is "
                "model-dependent and is not available on every ASUS device."
            )
        if not battery.supported:
            warnings.append(
                "Battery charge limits require kernel and firmware support; some "
                "devices expose the control, some do not."
            )
        if not graphics.installed:
            warnings.append(
                "Graphics switching is optional. `supergfxctl` should not be installed "
                "blindly; it is mainly useful for VFIO, explicit mode switching, or "
                "dGPU power issues."
            )
        elif integration.supergfxd_service != "active" or not integration.supergfxd_bus_name:
            warnings.append(
                "`supergfxctl` is installed, but `supergfxd` is not ready. "
                "Graphics mode switching requires the system daemon, system D-Bus policy, "
                "and a root-level installation."
            )
        return warnings

    def set_profile(self, profile: str) -> ActionOutcome:
        return self.asusctl.set_profile(profile)

    def set_fan_curve(
        self,
        profile: str,
        curves: dict[str, list[int]],
        temps: list[int],
    ) -> ActionOutcome:
        return self.asusctl.set_fan_curve(profile, curves, temps)

    def apply_profile_and_curves(
        self,
        profile: str,
        curves: dict[str, list[int]],
        temps: list[int],
    ) -> ActionOutcome:
        """Set profile then apply fan curves in a single atomic operation."""
        profile_result = self.asusctl.set_profile(profile)
        if not profile_result.success:
            return profile_result
        curve_result = self.asusctl.set_fan_curve(profile, curves, temps)
        if not curve_result.success:
            return ActionOutcome(
                "Profile & Curves",
                False,
                f"Profile set to {profile}, but fan curves failed: {curve_result.message}",
                curve_result.details,
            )
        return ActionOutcome(
            "Profile & Curves",
            True,
            f"Profile set to {profile} with custom fan curves applied.",
        )

    def set_battery_limit(self, limit: int) -> ActionOutcome:
        return self.asusctl.set_battery_limit(limit)

    def oneshot_charge(self, target_percent: int) -> ActionOutcome:
        return self.asusctl.oneshot_charge(target_percent)

    def set_keyboard_brightness(self, level: str) -> ActionOutcome:
        return self.asusctl.set_keyboard_brightness(level)

    def set_aura_power(self, zone: str, enabled: bool) -> ActionOutcome:
        return self.asusctl.set_aura_power(zone, enabled)

    def apply_aura_effect(
        self,
        effect: str,
        color_1: str,
        color_2: str,
        speed: str,
        direction: str,
        zone: str,
    ) -> ActionOutcome:
        return self.asusctl.apply_aura_effect(effect, color_1, color_2, speed, direction, zone)

    def set_graphics_mode(self, mode: str) -> ActionOutcome:
        return self.supergfxctl.set_mode(mode)
