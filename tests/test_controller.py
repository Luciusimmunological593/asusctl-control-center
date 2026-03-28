"""Tests for ControlCenterController (controller.py) including debounce."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from asus_linux_control_center.models import ActionOutcome, SystemSnapshot
from asus_linux_control_center.services.controller import ControlCenterController, _Task

# We need a QApplication for signal/slot tests; use offscreen platform.
_qt_available = True
try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])
except Exception:
    _qt_available = False


pytestmark = pytest.mark.skipif(not _qt_available, reason="PyQt6 not available")


def _make_controller() -> tuple[ControlCenterController, MagicMock]:
    service = MagicMock()
    controller = ControlCenterController(service)
    return controller, service


# ─── basic wiring ─────────────────────────────────────────────────────────────


def test_controller_initialises() -> None:
    controller, service = _make_controller()
    assert controller._busy_count == 0
    assert controller._active_tasks == set()
    assert controller._fan_profile is None
    assert controller._refresh_pending is False
    assert controller._refresh_running is False


def test_set_profile_calls_service() -> None:
    controller, service = _make_controller()
    outcome = ActionOutcome("Profile", True, "ok")
    service.set_profile.return_value = outcome

    # Block the thread pool so we can inspect the lambda setup
    controller._run_action = MagicMock()
    controller.set_profile("Performance")
    controller._run_action.assert_called_once()


def test_set_battery_limit_calls_service() -> None:
    controller, service = _make_controller()
    controller._run_action = MagicMock()
    controller.set_battery_limit(80)
    controller._run_action.assert_called_once()


def test_set_fan_curve_stores_profile() -> None:
    controller, service = _make_controller()
    controller._run_action = MagicMock()
    controller.set_fan_curve("Performance", {"cpu": [10] * 8}, [40] * 8)
    assert controller._fan_profile == "Performance"
    controller._run_action.assert_called_once()


def test_set_graphics_mode_calls_service() -> None:
    controller, service = _make_controller()
    controller._run_action = MagicMock()
    controller.set_graphics_mode("Hybrid")
    controller._run_action.assert_called_once()


# ─── busy state ───────────────────────────────────────────────────────────────


def test_mark_busy_and_idle() -> None:
    controller, _ = _make_controller()
    signals: list[bool] = []
    controller.busy_changed.connect(signals.append)

    controller._mark_busy()
    assert controller._busy_count == 1
    assert signals == [True]

    controller._mark_busy()
    assert controller._busy_count == 2
    # busy_changed only emits on transition to busy (count == 1)
    assert signals == [True]

    controller._mark_idle()
    assert controller._busy_count == 1
    assert signals == [True]  # not idle yet

    controller._mark_idle()
    assert controller._busy_count == 0
    assert signals == [True, False]


def test_mark_idle_does_not_go_negative() -> None:
    controller, _ = _make_controller()
    controller._mark_idle()
    assert controller._busy_count == 0


# ─── debounce ─────────────────────────────────────────────────────────────────


def test_refresh_debounce_queues_when_running() -> None:
    controller, service = _make_controller()

    # Patch _run_task to avoid actual thread pool usage
    controller._run_task = MagicMock()

    # First refresh starts normally
    controller.refresh(fan_profile="Balanced")
    assert controller._refresh_running is True
    assert controller._run_task.call_count == 1

    # Second refresh while first is running gets queued
    controller.refresh(fan_profile="Performance")
    assert controller._refresh_pending is True
    # _run_task not called again
    assert controller._run_task.call_count == 1

    # Fan profile updated to latest value
    assert controller._fan_profile == "Performance"


def test_handle_snapshot_drains_pending() -> None:
    controller, _ = _make_controller()

    refresh_calls: list[str | None] = []

    def tracking_refresh(fan_profile=None):
        refresh_calls.append(fan_profile)
        # Don't actually run — just track
        controller._fan_profile = fan_profile or controller._fan_profile

    # Setup: simulate a running refresh that completed
    controller._refresh_running = True
    controller._refresh_pending = True
    controller._fan_profile = "Performance"

    # Replace refresh to track calls
    controller.refresh = tracking_refresh

    # Create a minimal fake snapshot
    snapshot = MagicMock(spec=SystemSnapshot)

    # Capture snapshot_ready emissions
    emitted: list[object] = []
    controller.snapshot_ready.connect(emitted.append)

    controller._handle_snapshot(snapshot)

    assert controller._refresh_running is False
    assert emitted == [snapshot]
    # Should have called refresh to drain the pending request
    assert len(refresh_calls) == 1
    assert refresh_calls[0] == "Performance"


def test_handle_snapshot_no_pending() -> None:
    controller, service = _make_controller()
    controller._refresh_running = True
    controller._refresh_pending = False

    snapshot = MagicMock(spec=SystemSnapshot)
    emitted: list[object] = []
    controller.snapshot_ready.connect(emitted.append)

    controller._handle_snapshot(snapshot)
    assert controller._refresh_running is False
    assert emitted == [snapshot]


def test_handle_snapshot_non_snapshot_emits_error() -> None:
    controller, _ = _make_controller()
    controller._refresh_running = True

    errors: list[str] = []
    controller.error.connect(errors.append)

    controller._handle_snapshot("not a snapshot")
    assert len(errors) == 1
    assert "Unexpected" in errors[0]


# ─── _Task ────────────────────────────────────────────────────────────────────


def test_task_emits_result() -> None:
    results: list[object] = []
    finished: list[bool] = []

    task = _Task(lambda: 42)
    task.signals.result.connect(results.append)
    task.signals.finished.connect(lambda: finished.append(True))
    task.run()

    assert results == [42]
    assert finished == [True]


def test_task_emits_error_on_exception() -> None:
    errors: list[str] = []
    finished: list[bool] = []

    def bad_fn():
        raise ValueError("boom")

    task = _Task(bad_fn)
    task.signals.error.connect(errors.append)
    task.signals.finished.connect(lambda: finished.append(True))
    task.run()

    assert len(errors) == 1
    assert "boom" in errors[0]
    assert finished == [True]


def test_run_task_keeps_reference_until_finished() -> None:
    controller, _ = _make_controller()
    controller.thread_pool = MagicMock()

    results: list[object] = []
    controller._run_task(lambda: 7, results.append)

    assert len(controller._active_tasks) == 1
    task = next(iter(controller._active_tasks))
    assert task.autoDelete() is False

    task.run()

    assert results == [7]
    assert controller._active_tasks == set()
