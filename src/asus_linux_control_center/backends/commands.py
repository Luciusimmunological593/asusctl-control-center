from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
from collections.abc import Sequence

from ..models import CommandResult


def format_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


class CommandRunner:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def which(self, binary: str) -> str | None:
        return shutil.which(binary)

    def run(self, args: Sequence[str], timeout: int = 12) -> CommandResult:
        command = tuple(str(part) for part in args)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            message = f"command not found: {exc}"
            self.logger.error("%s | %s", message, format_command(command))
            return CommandResult(command, False, error=message)
        except subprocess.TimeoutExpired as exc:
            message = f"command timed out after {timeout}s"
            self.logger.error("%s | %s", message, format_command(command))
            return CommandResult(
                command,
                False,
                error=message,
                stdout=(exc.stdout or "").strip(),
                stderr=(exc.stderr or "").strip(),
            )
        except Exception as exc:  # pragma: no cover - defensive
            message = f"unexpected command failure: {exc}"
            self.logger.exception(message)
            return CommandResult(command, False, error=message)

        result = CommandResult(
            command=command,
            ok=completed.returncode == 0,
            returncode=completed.returncode,
            stdout=(completed.stdout or "").strip(),
            stderr=(completed.stderr or "").strip(),
        )
        if result.ok:
            self.logger.info("OK: %s", format_command(command))
        else:
            self.logger.warning(
                "FAIL: %s | rc=%s | stderr=%s",
                format_command(command),
                result.returncode,
                result.stderr,
            )
        return result

    def systemctl_state(self, unit: str) -> str:
        return self._systemctl_query("is-active", unit, ok_default="active", fail_default="inactive")

    def systemctl_enabled_state(self, unit: str) -> str:
        return self._systemctl_query("is-enabled", unit, ok_default="enabled", fail_default="disabled")

    def _systemctl_query(self, action: str, unit: str, ok_default: str, fail_default: str) -> str:
        if not self.which("systemctl"):
            return "missing"
        result = self.run(["systemctl", action, unit], timeout=6)
        if result.ok:
            return result.stdout.strip() or ok_default
        text = (result.stdout or result.stderr or "").strip()
        lowered = text.lower()
        if "no such file" in lowered or "could not be found" in lowered or "not-found" in lowered:
            return "missing"
        return text or fail_default

    def bus_name_exists(self, name: str) -> bool:
        if not self.which("busctl"):
            return False
        result = self.run(["busctl", "--system", "list"], timeout=8)
        if not result.ok:
            return False
        for line in result.stdout.splitlines():
            parts = line.split()
            if parts and parts[0] == name:
                return True
        return False
