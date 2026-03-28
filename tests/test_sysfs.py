"""Tests for AsusFirmwareBackend (sysfs.py) reading firmware attributes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from asus_linux_control_center.backends.sysfs import AsusFirmwareBackend, _interpret_value

# ─── _interpret_value ─────────────────────────────────────────────────────────


def test_interpret_boot_sound() -> None:
    assert _interpret_value("boot_sound", "1") == ("On", "Kernel firmware attribute")
    assert _interpret_value("boot_sound", "0") == ("Off", "Kernel firmware attribute")


def test_interpret_dgpu_disable() -> None:
    val, _ = _interpret_value("dgpu_disable", "1")
    assert val == "Yes"
    val, _ = _interpret_value("dgpu_disable", "0")
    assert val == "No"


def test_interpret_gpu_mux_mode() -> None:
    val, _ = _interpret_value("gpu_mux_mode", "0")
    assert "dGPU" in val
    val, _ = _interpret_value("gpu_mux_mode", "1")
    assert val == "Hybrid"
    val, _ = _interpret_value("gpu_mux_mode", "99")
    assert val == "99"


def test_interpret_panel_od() -> None:
    val, _ = _interpret_value("panel_od", "1")
    assert val == "On"
    val, _ = _interpret_value("panel_od", "0")
    assert val == "Off"


def test_interpret_numeric_attrs() -> None:
    for name in ("ppt_pl1_spl", "ppt_pl2_sppt", "nv_dynamic_boost", "nv_temp_target"):
        val, note = _interpret_value(name, "42")
        assert val == "42"
        assert "Numeric" in note


def test_interpret_thermal_policy() -> None:
    val, note = _interpret_value("throttle_thermal_policy", "0")
    assert val == "0"
    assert "thermal" in note.lower()


def test_interpret_charge_mode() -> None:
    val, note = _interpret_value("charge_mode", "2")
    assert val == "2"
    assert "charge" in note.lower()


def test_interpret_unknown_attr() -> None:
    val, note = _interpret_value("something_new", "hello")
    assert val == "hello"
    assert "Low-level" in note


# ─── AsusFirmwareBackend.inspect ──────────────────────────────────────────────


def test_inspect_missing_sysfs_dir() -> None:
    backend = AsusFirmwareBackend()
    with patch("asus_linux_control_center.backends.sysfs.ASUS_NB_WMI", Path("/nonexistent/path")):
        result = backend.inspect()
    assert result == []


def test_inspect_reads_available_attrs(tmp_path: Path) -> None:
    # Create a fake sysfs tree
    (tmp_path / "boot_sound").write_text("1\n", encoding="utf-8")
    (tmp_path / "panel_od").write_text("0\n", encoding="utf-8")

    backend = AsusFirmwareBackend()
    with patch("asus_linux_control_center.backends.sysfs.ASUS_NB_WMI", tmp_path):
        result = backend.inspect()

    names = {attr.name for attr in result}
    assert "boot_sound" in names
    assert "panel_od" in names

    boot_sound = next(a for a in result if a.name == "boot_sound")
    assert boot_sound.value == "On"
    assert boot_sound.raw_value == "1"


def test_inspect_skips_missing_attrs(tmp_path: Path) -> None:
    # Only create one of the expected attributes
    (tmp_path / "boot_sound").write_text("0\n", encoding="utf-8")

    backend = AsusFirmwareBackend()
    with patch("asus_linux_control_center.backends.sysfs.ASUS_NB_WMI", tmp_path):
        result = backend.inspect()

    names = {attr.name for attr in result}
    assert "boot_sound" in names
    assert "gpu_mux_mode" not in names


def test_inspect_handles_read_error(tmp_path: Path) -> None:
    # Create an unreadable file
    path = tmp_path / "boot_sound"
    path.write_text("1\n", encoding="utf-8")
    path.chmod(0o000)

    backend = AsusFirmwareBackend()
    with patch("asus_linux_control_center.backends.sysfs.ASUS_NB_WMI", tmp_path):
        result = backend.inspect()

    # Should skip the unreadable file without crashing
    names = {attr.name for attr in result}
    assert "boot_sound" not in names

    # Restore permissions for cleanup
    path.chmod(0o644)


def test_inspect_writable_detection(tmp_path: Path) -> None:
    path = tmp_path / "boot_sound"
    path.write_text("1\n", encoding="utf-8")
    path.chmod(0o644)  # read-write for owner

    backend = AsusFirmwareBackend()
    with patch("asus_linux_control_center.backends.sysfs.ASUS_NB_WMI", tmp_path):
        result = backend.inspect()

    boot_sound = next(a for a in result if a.name == "boot_sound")
    # In test environment, tmp_path is owned by current user so should be writable
    assert boot_sound.writable is True
