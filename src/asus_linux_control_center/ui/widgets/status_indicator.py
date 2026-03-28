"""Status indicator — colored dot with label text."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ..styles import get_active_theme, get_palette


def _status_colors() -> dict[str, str]:
    p = get_palette(get_active_theme())
    return {
        "available": p.success,
        "ready": p.success,
        "active": p.success,
        "unavailable": p.text_muted,
        "missing": p.text_muted,
        "warning": p.warning,
        "error": p.error,
        "info": p.accent,
        "partial": p.warning,
    }


class _Dot(QWidget):
    """Small colored circle."""

    def __init__(self, color: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(10, 10)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(1, 1, 8, 8)


class StatusIndicator(QWidget):
    """Colored dot + text label showing feature/service status."""

    def __init__(
        self,
        text: str = "",
        status: str = "unavailable",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        color = _status_colors().get(status, get_palette(get_active_theme()).text_muted)
        self._dot = _Dot(color, self)
        layout.addWidget(self._dot)

        self._label = QLabel(text)
        self._label.setObjectName("BodyLabel")
        layout.addWidget(self._label, 1)

    def set_status(self, text: str, status: str) -> None:
        color = _status_colors().get(status, get_palette(get_active_theme()).text_muted)
        self._dot.set_color(color)
        self._label.setText(text)
