"""Slide-in toast notification overlay.

Positioned at the top-right of its parent widget. Supports success,
warning, error, and info levels with auto-dismiss.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..styles import get_active_theme, get_palette

_LEVEL_OBJECT_NAME = {
    "success": "ToastSuccess",
    "warning": "ToastWarning",
    "error": "ToastError",
    "info": "ToastInfo",
}

_LEVEL_PREFIX = {
    "success": "\u2713",  # ✓
    "warning": "\u26a0",  # ⚠
    "error": "\u2717",    # ✗
    "info": "\u2139",     # ℹ
}


def _level_color(level: str) -> str:
    p = get_palette(get_active_theme())
    return {"success": p.success, "warning": p.warning, "error": p.error, "info": p.accent}.get(
        level, p.accent
    )


class _ToastItem(QFrame):
    """Single toast notification."""

    def __init__(self, message: str, level: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName(_LEVEL_OBJECT_NAME.get(level, "ToastInfo"))
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        icon_text = _LEVEL_PREFIX.get(level, "")
        if icon_text:
            icon = QLabel(icon_text)
            icon.setStyleSheet(f"color: {_level_color(level)}; font-size: 14px; font-weight: 700;")
            icon.setFixedWidth(18)
            layout.addWidget(icon)

        p = get_palette(get_active_theme())
        text = QLabel(message)
        text.setWordWrap(True)
        text.setStyleSheet(f"color: {p.text}; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(text, 1)

        close_btn = QPushButton("\u00d7")  # ×
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            f"border: none; background: transparent; font-size: 14px; "
            f"font-weight: 700; color: {p.text_muted}; padding: 0px;"
        )
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._dismiss)
        layout.addWidget(close_btn)

        self.setFixedWidth(360)
        self.adjustSize()

    def _dismiss(self) -> None:
        self.hide()
        self.deleteLater()


class ToastOverlay(QWidget):
    """Overlay container that manages a stack of toast items."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 8, 0)
        self._layout.setSpacing(6)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._items: list[_ToastItem] = []
        self.raise_()

    def show_toast(self, message: str, level: str = "info", duration: int = 4000) -> None:
        """Show a toast notification.

        Args:
            message: Text to display.
            level: 'success', 'warning', 'error', or 'info'.
            duration: Auto-dismiss time in ms (0 = manual close only).
        """
        item = _ToastItem(message, level, self)
        self._layout.addWidget(item)
        self._items.append(item)
        item.show()

        if duration > 0:
            QTimer.singleShot(duration, lambda: self._remove_item(item))

        # Limit visible toasts
        while len(self._items) > 5:
            old = self._items.pop(0)
            old.hide()
            old.deleteLater()

    def _remove_item(self, item: _ToastItem) -> None:
        if item in self._items:
            self._items.remove(item)
        item.hide()
        item.deleteLater()

    def reposition(self, parent_size) -> None:
        """Reposition overlay to fill the parent area."""
        self.setGeometry(0, 0, parent_size.width(), parent_size.height())
        self.raise_()
