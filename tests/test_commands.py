"""Tests for CommandRunner including bus_name_exists edge cases."""

from __future__ import annotations

import logging
from unittest.mock import patch

from asus_linux_control_center.backends.commands import CommandRunner


def test_bus_name_exists_found() -> None:
    runner = CommandRunner(logging.getLogger("test"))
    with patch.object(runner, "which", return_value="/usr/bin/busctl"), \
         patch.object(runner, "run") as mock_run:
        from asus_linux_control_center.models import CommandResult
        mock_run.return_value = CommandResult(
            command=("busctl", "--system", "list"),
            ok=True,
            stdout="org.freedesktop.DBus           - -          (activatable) -                        -\n"
                   "xyz.ljones.Asusd               12345          - -                        -\n",
        )
        assert runner.bus_name_exists("xyz.ljones.Asusd")


def test_bus_name_exists_not_found() -> None:
    runner = CommandRunner(logging.getLogger("test"))
    with patch.object(runner, "which", return_value="/usr/bin/busctl"), \
         patch.object(runner, "run") as mock_run:
        from asus_linux_control_center.models import CommandResult
        mock_run.return_value = CommandResult(
            command=("busctl", "--system", "list"),
            ok=True,
            stdout="org.freedesktop.DBus           - -          (activatable) -                        -\n",
        )
        assert not runner.bus_name_exists("xyz.ljones.Asusd")


def test_bus_name_exists_blank_lines() -> None:
    """Blank lines in busctl output must not cause IndexError."""
    runner = CommandRunner(logging.getLogger("test"))
    with patch.object(runner, "which", return_value="/usr/bin/busctl"), \
         patch.object(runner, "run") as mock_run:
        from asus_linux_control_center.models import CommandResult
        mock_run.return_value = CommandResult(
            command=("busctl", "--system", "list"),
            ok=True,
            stdout="\n\n   \n\nxyz.ljones.Asusd  12345  - - - -\n\n  \n",
        )
        assert runner.bus_name_exists("xyz.ljones.Asusd")


def test_bus_name_exists_empty_output() -> None:
    runner = CommandRunner(logging.getLogger("test"))
    with patch.object(runner, "which", return_value="/usr/bin/busctl"), \
         patch.object(runner, "run") as mock_run:
        from asus_linux_control_center.models import CommandResult
        mock_run.return_value = CommandResult(
            command=("busctl", "--system", "list"),
            ok=True,
            stdout="",
        )
        assert not runner.bus_name_exists("xyz.ljones.Asusd")


def test_bus_name_exists_no_busctl() -> None:
    runner = CommandRunner(logging.getLogger("test"))
    with patch.object(runner, "which", return_value=None):
        assert not runner.bus_name_exists("xyz.ljones.Asusd")


def test_bus_name_exists_busctl_fails() -> None:
    runner = CommandRunner(logging.getLogger("test"))
    with patch.object(runner, "which", return_value="/usr/bin/busctl"), \
         patch.object(runner, "run") as mock_run:
        from asus_linux_control_center.models import CommandResult
        mock_run.return_value = CommandResult(
            command=("busctl", "--system", "list"),
            ok=False,
            returncode=1,
        )
        assert not runner.bus_name_exists("xyz.ljones.Asusd")
