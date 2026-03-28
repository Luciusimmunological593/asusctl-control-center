from __future__ import annotations

import logging
import os
from pathlib import Path

from ..constants import FIRMWARE_ATTRIBUTE_LABELS
from ..models import FirmwareAttributeState

ASUS_NB_WMI = Path("/sys/devices/platform/asus-nb-wmi")

logger = logging.getLogger(__name__)


def _interpret_value(name: str, raw: str) -> tuple[str, str]:
    value = raw.strip()
    if name == "boot_sound":
        return ("On" if value == "1" else "Off", "Kernel firmware attribute")
    if name == "dgpu_disable":
        return ("Yes" if value == "1" else "No", "Read-only snapshot from the kernel interface")
    if name == "gpu_mux_mode":
        mapping = {"0": "Ultimate / dGPU primary", "1": "Hybrid"}
        return (mapping.get(value, value), "Read-only snapshot from the kernel interface")
    if name == "panel_od":
        return ("On" if value == "1" else "Off", "Read-only snapshot from the kernel interface")
    if name in {"ppt_pl1_spl", "ppt_pl2_sppt", "nv_dynamic_boost", "nv_temp_target"}:
        return (
            value,
            "Numeric firmware value exposed by the kernel; interpretation varies by model.",
        )
    if name == "throttle_thermal_policy":
        return (value, "Platform thermal policy index; meaning varies by firmware.")
    if name == "charge_mode":
        return (value, "Read-only charge mode value exposed by the kernel.")
    return (value, "Low-level firmware attribute")


class AsusFirmwareBackend:
    def inspect(self) -> list[FirmwareAttributeState]:
        if not ASUS_NB_WMI.exists():
            return []

        attrs: list[FirmwareAttributeState] = []
        for name, label in FIRMWARE_ATTRIBUTE_LABELS.items():
            path = ASUS_NB_WMI / name
            if not path.exists():
                continue
            try:
                raw_value = path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                logger.warning("Could not read sysfs attribute %s: %s", path, exc)
                continue
            value, note = _interpret_value(name, raw_value)
            attrs.append(
                FirmwareAttributeState(
                    name=name,
                    label=label,
                    value=value,
                    raw_value=raw_value,
                    writable=os.access(path, os.W_OK),
                    note=note,
                )
            )
        return attrs
