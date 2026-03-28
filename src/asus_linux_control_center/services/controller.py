from __future__ import annotations

import traceback
from collections.abc import Callable

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from ..models import ActionOutcome, SystemSnapshot
from .detection import ControlService


class _TaskSignals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class _Task(QRunnable):
    def __init__(self, fn: Callable[[], object]):
        super().__init__()
        self.fn = fn
        self.signals = _TaskSignals()

    def run(self) -> None:
        try:
            result = self.fn()
        except Exception:  # pragma: no cover - UI path
            self.signals.error.emit(traceback.format_exc())
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class ControlCenterController(QObject):
    snapshot_ready = pyqtSignal(object)
    action_finished = pyqtSignal(object)
    error = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)

    def __init__(self, service: ControlService):
        super().__init__()
        self.service = service
        self.thread_pool = QThreadPool.globalInstance()
        self._busy_count = 0
        self._active_tasks: set[_Task] = set()
        self._fan_profile: str | None = None
        self._refresh_pending = False
        self._refresh_running = False

    def refresh(self, fan_profile: str | None = None) -> None:
        self._fan_profile = fan_profile or self._fan_profile
        if self._refresh_running:
            self._refresh_pending = True
            return
        self._refresh_running = True
        self._run_task(
            lambda: self.service.build_snapshot(self._fan_profile),
            self._handle_snapshot,
        )

    def set_profile(self, profile: str) -> None:
        self._fan_profile = profile
        self._run_action(lambda: self.service.set_profile(profile), refresh_profile=profile)

    def set_fan_curve(self, profile: str, curves: dict[str, list[int]], temps: list[int]) -> None:
        self._fan_profile = profile
        self._run_action(
            lambda: self.service.set_fan_curve(profile, curves, temps),
            refresh_profile=profile,
        )

    def apply_profile_and_curves(
        self, profile: str, curves: dict[str, list[int]], temps: list[int]
    ) -> None:
        self._fan_profile = profile
        self._run_action(
            lambda: self.service.apply_profile_and_curves(profile, curves, temps),
            refresh_profile=profile,
        )

    def set_battery_limit(self, limit: int) -> None:
        self._run_action(lambda: self.service.set_battery_limit(limit), refresh_profile=self._fan_profile)

    def oneshot_charge(self, target_percent: int) -> None:
        self._run_action(lambda: self.service.oneshot_charge(target_percent), refresh_profile=self._fan_profile)

    def set_keyboard_brightness(self, level: str) -> None:
        self._run_action(lambda: self.service.set_keyboard_brightness(level), refresh_profile=self._fan_profile)

    def set_aura_power(self, zone: str, enabled: bool) -> None:
        self._run_action(lambda: self.service.set_aura_power(zone, enabled), refresh_profile=self._fan_profile)

    def apply_aura_effect(
        self,
        effect: str,
        color_1: str,
        color_2: str,
        speed: str,
        direction: str,
        zone: str,
    ) -> None:
        self._run_action(
            lambda: self.service.apply_aura_effect(effect, color_1, color_2, speed, direction, zone),
            refresh_profile=self._fan_profile,
        )

    def set_graphics_mode(self, mode: str) -> None:
        self._run_action(lambda: self.service.set_graphics_mode(mode), refresh_profile=self._fan_profile)

    def _run_action(self, fn: Callable[[], ActionOutcome], refresh_profile: str | None) -> None:
        def on_result(result: object) -> None:
            self.action_finished.emit(result)
            self.refresh(refresh_profile)

        self._run_task(fn, on_result)

    def _handle_snapshot(self, result: object) -> None:
        self._refresh_running = False
        if isinstance(result, SystemSnapshot):
            self.snapshot_ready.emit(result)
        else:
            self.error.emit("Unexpected snapshot payload received.")
        if self._refresh_pending:
            self._refresh_pending = False
            self.refresh(self._fan_profile)

    def _run_task(self, fn: Callable[[], object], on_result: Callable[[object], None]) -> None:
        task = _Task(fn)
        task.setAutoDelete(False)
        self._active_tasks.add(task)
        task.signals.result.connect(on_result)
        task.signals.error.connect(self.error.emit)

        def _finish_task() -> None:
            self._active_tasks.discard(task)
            self._mark_idle()

        task.signals.finished.connect(_finish_task)
        self._mark_busy()
        self.thread_pool.start(task)

    def _mark_busy(self) -> None:
        self._busy_count += 1
        if self._busy_count == 1:
            self.busy_changed.emit(True)

    def _mark_idle(self) -> None:
        self._busy_count = max(0, self._busy_count - 1)
        if self._busy_count == 0:
            self.busy_changed.emit(False)
