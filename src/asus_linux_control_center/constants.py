from __future__ import annotations

APP_NAME = "ASUS Linux Control Center"
APP_ID = "asus-linux-control-center"
APP_VERSION = "0.1.0"

DEFAULT_FAN_TEMPS = [40, 63, 67, 71, 75, 79, 83, 87]
RECOMMENDED_CURVES = {
    "Quiet": {
        "cpu": [18, 24, 30, 38, 48, 58, 68, 78],
        "gpu": [18, 24, 30, 38, 48, 58, 68, 78],
        "mid": [15, 20, 26, 34, 42, 52, 62, 72],
    },
    "Balanced": {
        "cpu": [24, 36, 46, 58, 68, 78, 90, 100],
        "gpu": [24, 36, 46, 58, 68, 78, 90, 100],
        "mid": [20, 32, 42, 52, 62, 72, 84, 94],
    },
    "Performance": {
        "cpu": [35, 50, 60, 72, 84, 94, 100, 100],
        "gpu": [35, 50, 60, 72, 84, 94, 100, 100],
        "mid": [30, 44, 54, 66, 78, 88, 96, 100],
    },
}

KEYBOARD_LEVELS = ["off", "low", "med", "high"]

AURA_EFFECTS = [
    ("Static", "static"),
    ("Breathe", "breathe"),
    ("Pulse", "pulse"),
    ("Rainbow Cycle", "rainbow-cycle"),
    ("Rainbow Wave", "rainbow-wave"),
]

AURA_SPEEDS = ["low", "med", "high"]
AURA_DIRECTIONS = ["left", "right", "up", "down"]

FIRMWARE_ATTRIBUTE_LABELS = {
    "boot_sound": "Boot sound",
    "charge_mode": "Charge mode",
    "dgpu_disable": "dGPU disabled",
    "gpu_mux_mode": "GPU MUX mode",
    "nv_dynamic_boost": "NVIDIA dynamic boost",
    "nv_temp_target": "NVIDIA temperature target",
    "panel_od": "Panel overdrive",
    "ppt_pl1_spl": "PPT PL1 SPL",
    "ppt_pl2_sppt": "PPT PL2 SPPT",
    "throttle_thermal_policy": "Thermal policy",
}
