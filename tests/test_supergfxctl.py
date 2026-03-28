from unittest.mock import MagicMock

from asus_linux_control_center.backends.commands import CommandRunner
from asus_linux_control_center.backends.supergfxctl import (
    SupergfxCtlBackend,
    explain_supergfx_failure,
    has_pending_transition,
    normalize_pending_action,
    normalize_pending_mode,
    parse_supergfx_modes,
)
from asus_linux_control_center.models import CommandResult


def test_parse_supergfx_modes() -> None:
    assert parse_supergfx_modes("Supported modes: Hybrid Integrated Vfio") == [
        "Hybrid",
        "Integrated",
        "Vfio",
    ]
    assert parse_supergfx_modes("Hybrid, Integrated, AsusMuxDgpu") == [
        "Hybrid",
        "Integrated",
        "AsusMuxDgpu",
    ]
    assert parse_supergfx_modes("[Hybrid, Integrated, NvidiaNoModeset, Vfio]") == [
        "Hybrid",
        "Integrated",
        "NvidiaNoModeset",
        "Vfio",
    ]


def test_explain_supergfx_failure() -> None:
    unavailable = explain_supergfx_failure(
        "Graphics mode change error.\nsupergfxd is not enabled, enable it with `systemctl enable supergfxd`"
    )
    assert "supergfxctl is installed, but supergfxd is unavailable." in unavailable

    access_denied = explain_supergfx_failure(
        'Error: Zbus(MethodError(OwnedErrorName("org.freedesktop.DBus.Error.AccessDenied"), '
        'Some("Connection is not allowed to own the service \\"org.supergfxctl.Daemon\\"")))'
    )
    assert "root-level install" in access_denied


def test_has_pending_transition() -> None:
    assert has_pending_transition(
        "Logout required to complete mode change",
        "Integrated",
        "Hybrid",
    )
    assert not has_pending_transition("No action required", "Hybrid", "Hybrid")
    assert not has_pending_transition("No action required", "Unknown", "Hybrid")


def test_parse_modes_empty() -> None:
    assert parse_supergfx_modes("") == []
    assert parse_supergfx_modes("No modes here") == []


def test_explain_empty_string() -> None:
    result = explain_supergfx_failure("")
    assert "unavailable" in result.lower()


def test_explain_unknown_error_passthrough() -> None:
    result = explain_supergfx_failure("Some completely new error message")
    assert result == "Some completely new error message"


def test_explain_switch_to_integrated() -> None:
    result = explain_supergfx_failure("switch to Integrated first")
    assert "Integrated" in result


def test_has_pending_none_values() -> None:
    assert not has_pending_transition(None, None, None)
    assert not has_pending_transition("", "", "")


def test_has_pending_action_only() -> None:
    assert has_pending_transition("Reboot needed", None, None)


def test_normalize_pending_values() -> None:
    assert normalize_pending_action("No action required") is None
    assert normalize_pending_action("Logout required") == "Logout required"
    assert normalize_pending_mode("Unknown", "Integrated") is None
    assert normalize_pending_mode("Integrated", "Integrated") is None
    assert normalize_pending_mode("Hybrid", "Integrated") == "Hybrid"


# ─── SupergfxCtlBackend integration ──────────────────────────────────────────

def _make_runner(ok: bool = True, stdout: str = "") -> MagicMock:
    runner = MagicMock(spec=CommandRunner)
    runner.which.return_value = "/usr/bin/supergfxctl"
    runner.run.return_value = CommandResult(
        command=("supergfxctl",), ok=ok, returncode=0 if ok else 1, stdout=stdout,
    )
    return runner


def test_backend_not_installed() -> None:
    runner = MagicMock(spec=CommandRunner)
    runner.which.return_value = None
    backend = SupergfxCtlBackend(runner)
    state = backend.inspect()
    assert not state.installed
    runner.run.assert_not_called()


def test_set_mode_success() -> None:
    runner = _make_runner(ok=True, stdout="Switched to Hybrid")
    backend = SupergfxCtlBackend(runner)
    outcome = backend.set_mode("Hybrid")
    assert outcome.success
    assert "Hybrid" in outcome.message


def test_set_mode_failure() -> None:
    runner = MagicMock(spec=CommandRunner)
    runner.which.return_value = "/usr/bin/supergfxctl"
    runner.run.return_value = CommandResult(
        command=("supergfxctl",), ok=False, returncode=1,
        stderr="supergfxd is not running",
        error=None,
    )
    backend = SupergfxCtlBackend(runner)
    outcome = backend.set_mode("Integrated")
    assert not outcome.success
    assert "supergfxd" in outcome.message.lower()


def test_set_mode_timeout() -> None:
    runner = MagicMock(spec=CommandRunner)
    runner.which.return_value = "/usr/bin/supergfxctl"
    runner.run.return_value = CommandResult(
        command=("supergfxctl",), ok=False, returncode=0,
        error="command timed out after 75s",
    )
    backend = SupergfxCtlBackend(runner)
    outcome = backend.set_mode("Integrated")
    assert not outcome.success
    assert "timed out" in outcome.message.lower()
    # Should mention logout/reboot
    assert "logout" in outcome.message.lower() or "reboot" in outcome.message.lower()
