"""Unavailable feature notice — centered placeholder with reason."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class UnavailableNotice(QWidget):
    """Placeholder shown when a feature is not available on the current device.

    Displays a dashed-border box with a title and explanation text.
    Designed to be swapped in place of the normal control section.
    """

    def __init__(
        self,
        title: str = "Not available",
        description: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        frame = QFrame(self)
        frame.setObjectName("UnavailableNotice")

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(24, 20, 24, 20)
        inner.setSpacing(6)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("BodyLabel")
        title_label.setStyleSheet("font-weight: 600; color: #999999;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title_label)

        if description:
            desc = QLabel(description)
            desc.setObjectName("MutedLabel")
            desc.setWordWrap(True)
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inner.addWidget(desc)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

    def set_text(self, title: str, description: str = "") -> None:
        """Update the notice text dynamically."""
        labels = self.findChildren(QLabel)
        if labels:
            labels[0].setText(title)
        if len(labels) > 1:
            labels[1].setText(description)
