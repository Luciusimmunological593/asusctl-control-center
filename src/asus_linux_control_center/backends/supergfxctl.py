from __future__ import annotations

from ..models import ActionOutcome, GraphicsState
from .commands import CommandRunner

KNOWN_SUPERGFX_MODES = (
    "Hybrid",
    "Integrated",
    "NvidiaNoModeset",
    "Vfio",
    "AsusEgpu",
    "AsusMuxDgpu",
)

NO_PENDING_ACTIONS = {"", "No action required", "Nothing", "Unknown"}
NO_PENDING_MODES = {"", "Unknown", "None"}


def parse_supergfx_modes(stdout: str) -> list[str]:
    modes: list[str] = []
    for candidate in KNOWN_SUPERGFX_MODES:
        if candidate in stdout and candidate not in modes:
            modes.append(candidate)
    return modes


def explain_supergfx_failure(details: str) -> str:
    text = details.strip()
    lowered = text.lower()
    if not text:
        return "Graphics mode switching is unavailable."
    if "serviceunknown" in lowered or "supergfxd is not enabled" in lowered or "supergfxd is not running" in lowered:
        return (
            "supergfxctl is installed, but supergfxd is unavailable. "
            "Graphics mode switching requires the system daemon, its D-Bus policy, "
            "and an enabled system service."
        )
    if "accessdenied" in lowered and "org.supergfxctl.daemon" in lowered:
        return (
            "supergfxctl binaries are present, but the daemon cannot own the "
            "`org.supergfxctl.Daemon` system bus name. A root-level install of the "
            "D-Bus policy and systemd service is still required."
        )
    if "switch to integrated first" in lowered:
        return "The requested graphics mode requires switching to Integrated first."
    return text


def has_pending_transition(
    pending_action: str | None,
    pending_mode: str | None,
    current_mode: str | None,
) -> bool:
    action_text = (pending_action or "").strip()
    mode_text = (pending_mode or "").strip()
    current_text = (current_mode or "").strip()
    if action_text and action_text not in NO_PENDING_ACTIONS:
        return True
    if action_text in NO_PENDING_ACTIONS:
        if not mode_text or mode_text in NO_PENDING_MODES:
            return False
        if current_text and mode_text == current_text:
            return False
        return False
    return bool(mode_text and mode_text not in NO_PENDING_MODES)


def normalize_pending_action(value: str | None) -> str | None:
    text = (value or "").strip()
    return None if not text or text in NO_PENDING_ACTIONS else text


def normalize_pending_mode(value: str | None, current_mode: str | None = None) -> str | None:
    text = (value or "").strip()
    current_text = (current_mode or "").strip()
    if not text or text in NO_PENDING_MODES:
        return None
    if current_text and text == current_text:
        return None
    return text


class SupergfxCtlBackend:
    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.binary = runner.which("supergfxctl")

    @property
    def installed(self) -> bool:
        return bool(self.binary)

    def _run(self, *args: str, timeout: int = 12):
        return self.runner.run([self.binary or "supergfxctl", *args], timeout=timeout)

    def inspect(self) -> GraphicsState:
        if not self.installed:
            return GraphicsState(
                installed=False,
                message=(
                    "supergfxctl is optional. Install it only if you need explicit graphics mode "
                    "switching, VFIO workflows, or ASUS eGPU handling."
                ),
            )

        pending_action_result = self._run("--pend-action")
        pending_mode_result = self._run("--pend-mode")
        current_result = self._run("--get")

        pending_action = pending_action_result.stdout.strip() if pending_action_result.ok else None
        pending_mode = pending_mode_result.stdout.strip() if pending_mode_result.ok else None
        current_mode = current_result.stdout.strip() if current_result.ok else None
        transition_pending = has_pending_transition(pending_action, pending_mode, current_mode)
        normalized_action = normalize_pending_action(pending_action)
        normalized_mode = normalize_pending_mode(pending_mode, current_mode)

        if transition_pending:
            return GraphicsState(
                installed=True,
                current_mode=current_mode or None,
                pending_action=normalized_action,
                pending_mode=normalized_mode,
                message=(
                    "Graphics mode change is pending. "
                    f"Action: {normalized_action or 'unknown'}. "
                    f"Pending mode: {normalized_mode or 'unknown'}."
                ),
            )

        supported_result = self._run("--supported")
        vendor_result = self._run("--vendor")
        status_result = self._run("--status")

        supported_modes = parse_supergfx_modes(supported_result.stdout) if supported_result.ok else []
        failure_details = (
            supported_result.details
            or current_result.details
            or vendor_result.details
            or status_result.details
            or pending_action_result.details
            or pending_mode_result.details
        )
        return GraphicsState(
            installed=True,
            current_mode=current_mode or None,
            supported_modes=supported_modes,
            vendor=vendor_result.stdout.strip() or None,
            power_status=status_result.stdout.strip() or None,
            pending_action=normalized_action,
            pending_mode=normalized_mode,
            message="" if supported_modes else explain_supergfx_failure(failure_details),
        )

    def set_mode(self, mode: str) -> ActionOutcome:
        # Mode transitions can legitimately wait for logout/reboot workflows.
        result = self._run("--mode", mode, timeout=75)
        message = (
            result.stdout.strip()
            if result.ok and result.stdout.strip()
            else f"Requested graphics mode change to {mode}."
        )
        if not result.ok:
            if result.error and "timed out" in result.error:
                message = (
                    f"Graphics mode change to {mode} timed out. "
                    "Some mode transitions require a full logout or reboot to complete. "
                    "Check the current mode after re-logging in."
                )
            else:
                message = explain_supergfx_failure(result.details or "Graphics mode change failed.")
        return ActionOutcome("Graphics", result.ok, message, result.details)
