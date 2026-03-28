"""Diagnostics page — full report viewer with copy and save."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...models import SystemSnapshot
from ...services import format_diagnostics_report
from ..components import page_header, panel, primary_button, secondary_button


class DiagnosticsPage(QWidget):
    """Formatted diagnostics report with copy/save actions."""

    def __init__(self, controller, settings):
        super().__init__()
        self.controller = controller
        self.settings = settings
        self._has_report = False
        self._busy = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(page_header(
            "Diagnostics",
            "Copy this report when opening issues or reporting unsupported hardware",
        ))

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._refresh_btn = primary_button("Refresh", self._request_refresh)
        self._copy_btn = secondary_button("Copy to clipboard", self._copy)
        self._save_btn = secondary_button("Save to file", self._save)
        self._copy_btn.setEnabled(False)
        self._save_btn.setEnabled(False)
        toolbar.addWidget(self._refresh_btn)
        toolbar.addWidget(self._copy_btn)
        toolbar.addWidget(self._save_btn)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        # Report panel
        report_panel, report_layout = panel("SYSTEM REPORT")
        self.report_text = QPlainTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setPlaceholderText("No diagnostics report loaded yet. Click Refresh.")
        report_layout.addWidget(self.report_text, 1)
        layout.addWidget(report_panel, 1)

    # -- Public interface --------------------------------------------------

    def apply_snapshot(self, snapshot: SystemSnapshot) -> None:
        self.report_text.setPlainText(format_diagnostics_report(snapshot))
        self._has_report = True
        self._copy_btn.setEnabled(not self._busy)
        self._save_btn.setEnabled(not self._busy)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._refresh_btn.setEnabled(not busy)
        self._copy_btn.setEnabled(self._has_report and not busy)
        self._save_btn.setEnabled(self._has_report and not busy)

    def save_state(self, settings) -> None:
        pass

    # -- Slots -------------------------------------------------------------

    def _request_refresh(self) -> None:
        self.controller.refresh()

    def _copy(self) -> None:
        if not self._has_report:
            return
        QApplication.clipboard().setText(self.report_text.toPlainText())

    def _save(self) -> None:
        if not self._has_report:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save diagnostics report",
            str(Path.home() / "asus-linux-control-center-diagnostics.txt"),
            "Text files (*.txt);;All files (*)",
        )
        if path:
            try:
                Path(path).write_text(self.report_text.toPlainText(), encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    "Save diagnostics report",
                    f"Could not save the diagnostics report:\n{exc}",
                )
