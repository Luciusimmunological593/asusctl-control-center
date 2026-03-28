"""Tests for AsusCtlBackend action methods with mocked CommandRunner."""

from __future__ import annotations

from unittest.mock import MagicMock

from asus_linux_control_center.backends.asusctl import AsusCtlBackend
from asus_linux_control_center.backends.commands import CommandRunner
from asus_linux_control_center.models import CommandResult


def _make_runner(ok: bool = True, stdout: str = "", stderr: str = "") -> MagicMock:
    runner = MagicMock(spec=CommandRunner)
    runner.which.return_value = "/usr/bin/asusctl"
    runner.run.return_value = CommandResult(
        command=("asusctl",),
        ok=ok,
        returncode=0 if ok else 1,
        stdout=stdout,
        stderr=stderr,
    )
    return runner


# ─── set_profile ──────────────────────────────────────────────────────────────

def test_set_profile_success() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_profile("Performance")
    assert outcome.success
    assert "Performance" in outcome.message
    runner.run.assert_called_once()
    args = runner.run.call_args[0][0]
    assert args == ["/usr/bin/asusctl", "profile", "set", "Performance"]


def test_set_profile_failure() -> None:
    runner = _make_runner(ok=False, stderr="Unknown profile")
    backend = AsusCtlBackend(runner)
    outcome = backend.set_profile("Turbo")
    assert not outcome.success


# ─── set_battery_limit ────────────────────────────────────────────────────────

def test_set_battery_limit_success() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_battery_limit(80)
    assert outcome.success
    assert "80%" in outcome.message


def test_set_battery_limit_out_of_range_low() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_battery_limit(5)
    assert not outcome.success
    assert "between 20 and 100" in outcome.message
    runner.run.assert_not_called()


def test_set_battery_limit_out_of_range_high() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_battery_limit(150)
    assert not outcome.success
    runner.run.assert_not_called()


def test_set_battery_limit_boundary_min() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_battery_limit(20)
    assert outcome.success


def test_set_battery_limit_boundary_max() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_battery_limit(100)
    assert outcome.success


# ─── oneshot_charge ───────────────────────────────────────────────────────────

def test_oneshot_charge_success() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.oneshot_charge(100)
    assert outcome.success
    assert "100%" in outcome.message


def test_oneshot_charge_out_of_range() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.oneshot_charge(10)
    assert not outcome.success
    runner.run.assert_not_called()


# ─── set_keyboard_brightness ─────────────────────────────────────────────────

def test_set_keyboard_brightness_success() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_keyboard_brightness("high")
    assert outcome.success
    args = runner.run.call_args[0][0]
    assert "high" in args


def test_set_keyboard_brightness_failure() -> None:
    runner = _make_runner(ok=False, stderr="Permission denied")
    backend = AsusCtlBackend(runner)
    outcome = backend.set_keyboard_brightness("med")
    assert not outcome.success


def test_set_keyboard_brightness_invalid_level() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_keyboard_brightness("ultra")
    assert not outcome.success
    assert "Invalid" in outcome.message
    runner.run.assert_not_called()


# ─── set_fan_curve ────────────────────────────────────────────────────────────

def test_set_fan_curve_success() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    curves = {"cpu": [20, 30, 40, 50, 60, 70, 80, 90], "gpu": [20, 30, 40, 50, 60, 70, 80, 90]}
    temps = [40, 63, 67, 71, 75, 79, 83, 87]
    outcome = backend.set_fan_curve("Performance", curves, temps)
    assert outcome.success
    # Per fan: write + enable = 2 calls per fan. Plus enable-all = 1.
    # 2 fans * 2 + 1 = 5
    assert runner.run.call_count == 5


def test_set_fan_curve_partial_failure_skips_enable_all() -> None:
    """When one fan write fails, enable-all must be skipped."""
    call_count = 0

    def side_effect(args, timeout=12):
        nonlocal call_count
        call_count += 1
        # Fail the first write (cpu fan data write)
        if call_count == 1:
            return CommandResult(command=tuple(args), ok=False, returncode=1, stderr="write failed")
        return CommandResult(command=tuple(args), ok=True, returncode=0)

    runner = _make_runner(ok=True)
    runner.run.side_effect = side_effect
    backend = AsusCtlBackend(runner)
    curves = {"cpu": [20, 30, 40, 50, 60, 70, 80, 90], "gpu": [20, 30, 40, 50, 60, 70, 80, 90]}
    temps = [40, 63, 67, 71, 75, 79, 83, 87]
    outcome = backend.set_fan_curve("Performance", curves, temps)
    assert not outcome.success
    assert "skipped" in outcome.message.lower()


def test_set_fan_curve_empty_curves_dict() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_fan_curve("Performance", {}, [40, 50, 60])
    assert not outcome.success
    assert "No fan channels" in outcome.message
    runner.run.assert_not_called()


def test_set_fan_curve_filters_to_provided_fans() -> None:
    """Only fans present in the curves dict should be written."""
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    curves = {"cpu": [20, 30, 40, 50, 60, 70, 80, 90]}
    temps = [40, 63, 67, 71, 75, 79, 83, 87]
    outcome = backend.set_fan_curve("Performance", curves, temps)
    assert outcome.success
    # 1 fan * (write + enable) + enable_all = 3 calls
    assert runner.run.call_count == 3


# ─── set_aura_power ──────────────────────────────────────────────────────────

def test_set_aura_power_enable() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_aura_power("keyboard", True)
    assert outcome.success
    args = runner.run.call_args[0][0]
    assert "--boot" in args
    assert "--awake" in args


def test_set_aura_power_disable() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.set_aura_power("keyboard", False)
    assert outcome.success
    args = runner.run.call_args[0][0]
    # Disable sends bare command without state flags
    assert "--boot" not in args
    assert "--awake" not in args


# ─── apply_aura_effect ────────────────────────────────────────────────────────

def test_apply_aura_static() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.apply_aura_effect("static", "#ff0000", "#000000", "low", "left", "")
    assert outcome.success
    args = runner.run.call_args[0][0]
    assert "static" in args
    assert "ff0000" in args
    assert "--zone" not in args


def test_apply_aura_breathe_with_zone() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.apply_aura_effect("breathe", "#ff0000", "#0000ff", "med", "left", "keyboard")
    assert outcome.success
    args = runner.run.call_args[0][0]
    assert "breathe" in args
    assert "--colour2" in args
    assert "--speed" in args
    # --zone is intentionally NOT passed to `aura effect` because power-zone
    # names (keyboard, logo, …) are invalid for effect --zone which expects
    # numeric/named LED zones (0, 1, one).  Effects apply to all powered zones.
    assert "--zone" not in args


def test_apply_aura_rainbow_wave() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.apply_aura_effect("rainbow-wave", "#000", "#000", "high", "right", "")
    assert outcome.success
    args = runner.run.call_args[0][0]
    assert "--direction" in args
    assert "right" in args


def test_apply_aura_unsupported_effect() -> None:
    runner = _make_runner(ok=True)
    backend = AsusCtlBackend(runner)
    outcome = backend.apply_aura_effect("sparkle", "#fff", "#fff", "low", "left", "")
    assert not outcome.success
    assert "Unsupported" in outcome.message
    runner.run.assert_not_called()
