from __future__ import annotations

import json

from ..models import SystemSnapshot


def snapshot_as_json(snapshot: SystemSnapshot) -> str:
    return json.dumps(snapshot.to_dict(), indent=2)


def format_diagnostics_report(snapshot: SystemSnapshot) -> str:
    firmware_lines = [
        f"- {item.label}: {item.value} (raw={item.raw_value}, writable={item.writable})"
        for item in snapshot.firmware_attributes
    ] or ["- No low-level ASUS firmware attributes were detected."]

    warning_lines = [f"- {warning}" for warning in snapshot.warnings] or ["- No warnings."]
    profile_lines = [
        f"- Available profiles: {', '.join(snapshot.profiles.available) or 'none'}",
        f"- Active profile: {snapshot.profiles.active or 'unknown'}",
        f"- AC profile: {snapshot.profiles.ac_profile or 'unknown'}",
        f"- Battery profile: {snapshot.profiles.battery_profile or 'unknown'}",
    ]
    fan_curve_line = (
        f"- Fan curves: supported for {snapshot.fan_curve.probe_profile}"
        if snapshot.fan_curve.supported and snapshot.fan_curve.probe_profile
        else f"- Fan curves: {snapshot.fan_curve.message}"
    )
    aura_effects = ", ".join(snapshot.aura.effects) or "none"
    aura_zones = ", ".join(snapshot.aura.zones) or "none"
    graphics_modes = ", ".join(snapshot.graphics.supported_modes) or "none"

    return "\n".join(
        [
            f"{snapshot.timestamp} {snapshot.device.hostname}",
            "",
            "[Device]",
            f"- Product family: {snapshot.device.product_family}",
            f"- Board name: {snapshot.device.board_name}",
            f"- asusctl version: {snapshot.device.asusctl_version}",
            f"- Kernel: {snapshot.device.kernel}",
            f"- Distro: {snapshot.device.distro}",
            "",
            "[Integrations]",
            f"- asusctl path: {snapshot.integration.asusctl_path or 'missing'}",
            f"- asusd service: {snapshot.integration.asusd_service}",
            "- asusd D-Bus name: "
            + ("present" if snapshot.integration.asusd_bus_name else "missing"),
            f"- supergfxctl path: {snapshot.integration.supergfxctl_path or 'missing'}",
            f"- supergfxd service: {snapshot.integration.supergfxd_service}",
            f"- supergfxd enabled: {snapshot.integration.supergfxd_enabled}",
            "- supergfxd D-Bus name: "
            + ("present" if snapshot.integration.supergfxd_bus_name else "missing"),
            "",
            "[Profiles]",
            *profile_lines,
            fan_curve_line,
            "",
            "[Battery and Lighting]",
            "- Battery charge limit: "
            + (
                str(snapshot.battery.limit)
                if snapshot.battery.limit is not None
                else snapshot.battery.message
            ),
            f"- Keyboard brightness: {snapshot.keyboard.brightness or snapshot.keyboard.message}",
            f"- Aura effects: {aura_effects}",
            f"- Aura zones: {aura_zones}",
            "",
            "[Graphics]",
            f"- Installed: {snapshot.graphics.installed}",
            f"- Current mode: {snapshot.graphics.current_mode or 'unknown'}",
            f"- Supported modes: {graphics_modes}",
            f"- Vendor: {snapshot.graphics.vendor or 'unknown'}",
            f"- Power status: {snapshot.graphics.power_status or 'unknown'}",
            f"- Pending action: {snapshot.graphics.pending_action or 'none'}",
            f"- Pending mode: {snapshot.graphics.pending_mode or 'none'}",
            f"- Notes: {snapshot.graphics.message or 'none'}",
            "",
            "[Firmware Attributes]",
            *firmware_lines,
            "",
            "[Warnings]",
            *warning_lines,
        ]
    )
