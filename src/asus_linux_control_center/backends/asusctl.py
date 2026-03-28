from __future__ import annotations

import re
from collections.abc import Sequence

from ..constants import AURA_EFFECTS, KEYBOARD_LEVELS
from ..models import (
    ActionOutcome,
    AuraState,
    BatteryState,
    CommandResult,
    DeviceInfo,
    FanCurveSnapshot,
    FanCurveState,
    KeyboardState,
    ProfileState,
)
from ..utils import make_non_decreasing_curve, normalize_curve_values, unique_lines
from .commands import CommandRunner

PROFILE_ACTIVE_RE = re.compile(r"Active profile:\s*([A-Za-z0-9_-]+)")
PROFILE_AC_RE = re.compile(r"AC profile\s+([A-Za-z0-9_-]+)")
PROFILE_BATTERY_RE = re.compile(r"Battery profile\s+([A-Za-z0-9_-]+)")
VERSION_RE = re.compile(r"(?:asusctl v|Software version:\s*)([A-Za-z0-9_.-]+)")
FAMILY_RE = re.compile(r"Product family:\s*(.+)")
BOARD_RE = re.compile(r"Board name:\s*(.+)")
BATTERY_LIMIT_RE = re.compile(r"Current battery charge limit:\s*(\d+)%")
KEYBOARD_RE = re.compile(r"Current keyboard led brightness:\s*([A-Za-z]+)")


def parse_info_output(stdout: str) -> DeviceInfo:
    version = VERSION_RE.search(stdout)
    family = FAMILY_RE.search(stdout)
    board = BOARD_RE.search(stdout)
    return DeviceInfo(
        asusctl_version=version.group(1) if version else "Unknown",
        product_family=family.group(1).strip() if family else "Unknown",
        board_name=board.group(1).strip() if board else "Unknown",
    )


def parse_profile_list_output(stdout: str) -> list[str]:
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def parse_profile_get_output(stdout: str) -> tuple[str | None, str | None, str | None]:
    active = PROFILE_ACTIVE_RE.search(stdout)
    ac_profile = PROFILE_AC_RE.search(stdout)
    battery_profile = PROFILE_BATTERY_RE.search(stdout)
    return (
        active.group(1) if active else None,
        ac_profile.group(1) if ac_profile else None,
        battery_profile.group(1) if battery_profile else None,
    )


def parse_help_commands(stdout: str) -> list[str]:
    commands: list[str] = []
    in_commands = False
    for line in stdout.splitlines():
        if line.strip() == "Commands:":
            in_commands = True
            continue
        if not in_commands or not line.strip():
            continue
        match = re.match(r"\s*([a-z0-9-]+)\s{2,}", line)
        if match:
            commands.append(match.group(1))
    return commands


def parse_fan_curve_output(stdout: str) -> FanCurveSnapshot | None:
    pattern = re.compile(
        r"fan:\s*(CPU|GPU|MID),\s*"
        r"pwm:\s*\(([^)]*)\),\s*"
        r"temp:\s*\(([^)]*)\),\s*"
        r"enabled:\s*(true|false)",
        re.IGNORECASE | re.DOTALL,
    )

    fans: dict[str, list[int]] = {}
    enabled: dict[str, bool] = {}
    temps: list[int] | None = None
    for match in pattern.finditer(stdout):
        fan_name = match.group(1).lower()
        pwm_values = [int(value) for value in re.findall(r"\d+", match.group(2))]
        temp_values = [int(value) for value in re.findall(r"\d+", match.group(3))]
        if not pwm_values or not temp_values:
            continue
        if temps is None:
            temps = temp_values
        fans[fan_name] = [round((value / 255) * 100) for value in pwm_values]
        enabled[fan_name] = match.group(4).lower() == "true"
    if not temps or not fans:
        return None
    return FanCurveSnapshot(temps=temps, fans=fans, enabled=enabled)


class AsusCtlBackend:
    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.binary = runner.which("asusctl")

    @property
    def available(self) -> bool:
        return bool(self.binary)

    def _run(self, args: Sequence[str], timeout: int = 12) -> CommandResult:
        command = [self.binary or "asusctl", *args]
        return self.runner.run(command, timeout=timeout)

    def inspect_device(self) -> DeviceInfo:
        if not self.available:
            return DeviceInfo()
        result = self._run(["info"])
        return parse_info_output(result.stdout) if result.ok else DeviceInfo()

    def inspect_profiles(self) -> ProfileState:
        if not self.available:
            return ProfileState(message="asusctl is not installed.")

        profiles_result = self._run(["profile", "list"])
        active_result = self._run(["profile", "get"])
        available = parse_profile_list_output(profiles_result.stdout) if profiles_result.ok else []
        active, ac_profile, battery_profile = (
            parse_profile_get_output(active_result.stdout) if active_result.ok else (None, None, None)
        )
        supported = bool(available)
        message = "" if supported else "No ASUS performance profiles were reported."
        return ProfileState(
            supported=supported,
            available=available,
            active=active,
            ac_profile=ac_profile,
            battery_profile=battery_profile,
            message=message,
        )

    def inspect_fan_curve(
        self,
        requested_profile: str | None,
        profiles: ProfileState,
    ) -> FanCurveState:
        if not self.available:
            return FanCurveState(message="asusctl is not installed.")

        probe_profile = (
            requested_profile
            or profiles.active
            or (profiles.available[0] if profiles.available else None)
        )
        if not probe_profile:
            return FanCurveState(message="No profile is available to probe fan curves.")

        result = self._run(["fan-curve", "--mod-profile", probe_profile], timeout=20)
        snapshot = parse_fan_curve_output(result.stdout) if result.ok else None
        if snapshot:
            return FanCurveState(
                supported=True,
                message=f"Fan curves are available for {probe_profile}.",
                probe_profile=probe_profile,
                snapshot=snapshot,
            )
        message = result.details or "Fan curve editing is not available on this device."
        return FanCurveState(
            supported=False,
            message=message,
            probe_profile=probe_profile,
        )

    def inspect_battery(self) -> BatteryState:
        if not self.available:
            return BatteryState(message="asusctl is not installed.")
        result = self._run(["battery", "info"])
        if not result.ok:
            return BatteryState(message=result.details or "Battery charge limit is unavailable.")
        match = BATTERY_LIMIT_RE.search(result.stdout)
        if not match:
            return BatteryState(message="Unable to parse battery charge limit.")
        return BatteryState(supported=True, limit=int(match.group(1)))

    def inspect_keyboard(self) -> KeyboardState:
        if not self.available:
            return KeyboardState(levels=KEYBOARD_LEVELS, message="asusctl is not installed.")
        result = self._run(["leds", "get"])
        if not result.ok:
            return KeyboardState(
                levels=KEYBOARD_LEVELS,
                message=result.details or "Keyboard brightness is unavailable.",
            )
        match = KEYBOARD_RE.search(result.stdout)
        if not match:
            return KeyboardState(
                levels=KEYBOARD_LEVELS,
                message="Unable to parse keyboard brightness.",
            )
        return KeyboardState(
            supported=True,
            brightness=match.group(1).lower(),
            levels=KEYBOARD_LEVELS,
        )

    def inspect_aura(self) -> AuraState:
        if not self.available:
            return AuraState(message="asusctl is not installed.")
        effect_result = self._run(["aura", "effect", "--help"])
        power_result = self._run(["aura", "power", "--help"])
        effects = parse_help_commands(effect_result.stdout) if effect_result.ok else []
        zones = parse_help_commands(power_result.stdout) if power_result.ok else []
        validated = [command for _, command in AURA_EFFECTS if command in effects]
        supported = bool(validated or zones)
        message = ""
        if not supported:
            message = (
                effect_result.details
                or power_result.details
                or "Aura controls are unavailable."
            )
        return AuraState(supported=supported, effects=validated, zones=zones, message=message)

    def set_profile(self, profile: str) -> ActionOutcome:
        result = self._run(["profile", "set", profile])
        message = (
            f"Active profile set to {profile}."
            if result.ok
            else result.details or "Profile change failed."
        )
        return ActionOutcome("Profile", result.ok, message, result.details)

    def set_fan_curve(
        self,
        profile: str,
        curves: dict[str, list[int]],
        temps: list[int],
    ) -> ActionOutcome:
        # Only write fans that are present in the provided curves dict.
        # This avoids sending commands for fans the device may not have.
        fan_names = [fan for fan in ["cpu", "gpu", "mid"] if fan in curves]
        if not fan_names:
            return ActionOutcome("Fan curves", False, "No fan channels provided.")

        errors: list[str] = []
        any_write_failed = False
        for fan in fan_names:
            values = make_non_decreasing_curve(
                normalize_curve_values(curves.get(fan, []), len(temps))
            )
            curve_data = ",".join(
                f"{temp}c:{speed}%"
                for temp, speed in zip(temps, values, strict=False)
            )
            write_result = self._run(
                ["fan-curve", "--mod-profile", profile, "--fan", fan, "--data", curve_data],
                timeout=20,
            )
            if not write_result.ok:
                errors.append(write_result.details or f"Failed to write the {fan.upper()} curve.")
                any_write_failed = True
                continue
            enable_result = self._run(
                [
                    "fan-curve",
                    "--mod-profile",
                    profile,
                    "--enable-fan-curve",
                    "true",
                    "--fan",
                    fan,
                ],
                timeout=20,
            )
            if not enable_result.ok:
                errors.append(enable_result.details or f"Failed to enable the {fan.upper()} curve.")

        # Only enable all curves globally if every per-fan write succeeded.
        # Partial writes with global enable can leave the fan controller in a
        # broken state where some fans run unconfigured curves.
        if not any_write_failed:
            enable_all = self._run(
                ["fan-curve", "--mod-profile", profile, "--enable-fan-curves", "true"],
                timeout=20,
            )
            if not enable_all.ok:
                errors.append(enable_all.details or f"Failed to enable fan curves for {profile}.")
        else:
            errors.append(
                "Global fan curve enable was skipped because one or more per-fan "
                "writes failed. Fix the failing fan(s) and try again."
            )

        if errors:
            message = "\n".join(unique_lines(errors))
            return ActionOutcome("Fan curves", False, message, message)
        return ActionOutcome("Fan curves", True, f"Fan curves applied to {profile}.")

    def set_battery_limit(self, limit: int) -> ActionOutcome:
        if not isinstance(limit, int) or limit < 20 or limit > 100:
            return ActionOutcome(
                "Battery", False,
                f"Battery charge limit must be between 20 and 100 (got {limit}).",
            )
        result = self._run(["battery", "limit", str(limit)])
        message = (
            f"Battery charge limit set to {limit}%."
            if result.ok
            else result.details or "Battery limit update failed."
        )
        return ActionOutcome("Battery", result.ok, message, result.details)

    def oneshot_charge(self, target_percent: int) -> ActionOutcome:
        if not isinstance(target_percent, int) or target_percent < 20 or target_percent > 100:
            return ActionOutcome(
                "Battery", False,
                f"One-shot target must be between 20 and 100 (got {target_percent}).",
            )
        result = self._run(["battery", "oneshot", str(target_percent)])
        message = (
            f"One-shot charge requested up to {target_percent}%."
            if result.ok
            else result.details or "One-shot charge request failed."
        )
        return ActionOutcome("Battery", result.ok, message, result.details)

    def set_keyboard_brightness(self, level: str) -> ActionOutcome:
        if level not in KEYBOARD_LEVELS:
            return ActionOutcome(
                "Lighting", False,
                f"Invalid brightness level '{level}'. Must be one of: {', '.join(KEYBOARD_LEVELS)}.",
            )
        result = self._run(["leds", "set", level])
        message = (
            f"Keyboard brightness set to {level}."
            if result.ok
            else result.details or "Keyboard brightness update failed."
        )
        return ActionOutcome("Lighting", result.ok, message, result.details)

    def set_aura_power(self, zone: str, enabled: bool) -> ActionOutcome:
        # asusctl aura power requires explicit state flags for each power state.
        # With --boot/--awake/--sleep/--shutdown the zone is enabled for all states.
        # Without any flags, asusctl clears all power states for the zone (disable).
        # This is the documented asusctl behaviour as of v6.x.
        args = ["aura", "power", zone]
        if enabled:
            args.extend(["--boot", "--awake", "--sleep", "--shutdown"])
        result = self._run(args)
        state = "enabled" if enabled else "disabled"
        message = (
            f"{zone.replace('-', ' ').title()} power states {state}."
            if result.ok
            else result.details or "Aura power update failed."
        )
        return ActionOutcome("Lighting", result.ok, message, result.details)

    def apply_aura_effect(
        self,
        effect: str,
        color_1: str,
        color_2: str,
        speed: str,
        direction: str,
        zone: str,
    ) -> ActionOutcome:
        effect_name = effect.lower()
        # Note: --zone in `aura effect` expects numeric/named LED zones (0, 1, one, logo),
        # NOT the power-zone names from `aura power` (keyboard, lightbar, etc.).
        # We omit --zone entirely; effects apply to all powered-on zones by default.
        if effect_name == "static":
            args = ["aura", "effect", "static", "--colour", color_1.lstrip("#")]
        elif effect_name == "breathe":
            args = [
                "aura",
                "effect",
                "breathe",
                "--colour",
                color_1.lstrip("#"),
                "--colour2",
                color_2.lstrip("#"),
                "--speed",
                speed,
            ]
        elif effect_name == "pulse":
            args = [
                "aura",
                "effect",
                "pulse",
                "--colour",
                color_1.lstrip("#"),
            ]
        elif effect_name == "rainbow-cycle":
            args = ["aura", "effect", "rainbow-cycle", "--speed", speed]
        elif effect_name == "rainbow-wave":
            args = [
                "aura",
                "effect",
                "rainbow-wave",
                "--direction",
                direction,
                "--speed",
                speed,
            ]
        else:
            return ActionOutcome("Lighting", False, f"Unsupported aura effect: {effect}")

        result = self._run(args)
        message = (
            f"Aura effect {effect} applied."
            if result.ok
            else result.details or "Aura effect update failed."
        )
        return ActionOutcome("Lighting", result.ok, message, result.details)
