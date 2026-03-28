from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class CommandResult:
    command: tuple[str, ...]
    ok: bool
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    error: str | None = None

    @property
    def details(self) -> str:
        return " | ".join(
            part for part in [self.error, self.stderr.strip(), self.stdout.strip()] if part
        )


@dataclass(slots=True)
class DeviceInfo:
    product_family: str = "Unknown"
    board_name: str = "Unknown"
    asusctl_version: str = "Unknown"
    kernel: str = ""
    distro: str = ""
    hostname: str = ""


@dataclass(slots=True)
class IntegrationState:
    asusctl_path: str | None = None
    asusd_service: str = "unknown"
    asusd_bus_name: bool = False
    supergfxctl_path: str | None = None
    supergfxd_service: str = "unknown"
    supergfxd_enabled: str = "unknown"
    supergfxd_bus_name: bool = False


@dataclass(slots=True)
class ProfileState:
    supported: bool = False
    available: list[str] = field(default_factory=list)
    active: str | None = None
    ac_profile: str | None = None
    battery_profile: str | None = None
    message: str = ""


@dataclass(slots=True)
class FanCurveSnapshot:
    temps: list[int]
    fans: dict[str, list[int]]
    enabled: dict[str, bool]


@dataclass(slots=True)
class FanCurveState:
    supported: bool = False
    message: str = ""
    probe_profile: str | None = None
    snapshot: FanCurveSnapshot | None = None


@dataclass(slots=True)
class BatteryState:
    supported: bool = False
    limit: int | None = None
    message: str = ""


@dataclass(slots=True)
class KeyboardState:
    supported: bool = False
    brightness: str | None = None
    levels: list[str] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class AuraState:
    supported: bool = False
    effects: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class GraphicsState:
    installed: bool = False
    current_mode: str | None = None
    supported_modes: list[str] = field(default_factory=list)
    vendor: str | None = None
    power_status: str | None = None
    pending_action: str | None = None
    pending_mode: str | None = None
    message: str = ""


@dataclass(slots=True)
class FirmwareAttributeState:
    name: str
    label: str
    value: str
    raw_value: str
    writable: bool
    note: str = ""


@dataclass(slots=True)
class SystemSnapshot:
    device: DeviceInfo
    integration: IntegrationState
    profiles: ProfileState
    fan_curve: FanCurveState
    battery: BatteryState
    keyboard: KeyboardState
    aura: AuraState
    graphics: GraphicsState
    firmware_attributes: list[FirmwareAttributeState] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionOutcome:
    title: str
    success: bool
    message: str
    details: str = ""


@dataclass(slots=True)
class SettingsData:
    last_page: str = "overview"
    last_curve_profile: str = ""
    selected_fan: str = "cpu"
    custom_curves: dict[str, list[int]] = field(default_factory=dict)
    saved_presets: dict[str, dict[str, list[int]]] = field(default_factory=dict)
    aura_effect: str = "Static"
    aura_zone: str = ""
    aura_color_1: str = "#2563eb"
    aura_color_2: str = "#93c5fd"
    window_width: int = 1440
    window_height: int = 920
    theme: str = "dark"
