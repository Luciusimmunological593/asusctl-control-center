"""Shared UI builder functions — cards, panels, sections, form helpers, buttons."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .styles import get_active_theme, get_palette

# -- Card container -------------------------------------------------------

def card(title: str | None = None, subtitle: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """White card container with optional title/subtitle header."""
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(10)
    if title:
        t = QLabel(title)
        t.setObjectName("CardTitle")
        layout.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("MutedLabel")
        s.setWordWrap(True)
        layout.addWidget(s)
    return frame, layout


# -- Section header --------------------------------------------------------

def section_header(title: str, description: str | None = None) -> QWidget:
    """Inline section heading with optional description. Not in a card."""
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("SectionTitle")
    layout.addWidget(t)
    if description:
        d = QLabel(description)
        d.setObjectName("SectionSubtitle")
        d.setWordWrap(True)
        layout.addWidget(d)
    return w


# -- Page header -----------------------------------------------------------

def page_header(title: str, subtitle: str | None = None) -> QWidget:
    """Page-level title block placed at the top of every page."""
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 4)
    layout.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    layout.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        s.setWordWrap(True)
        layout.addWidget(s)
    return w


def experimental_notice(text: str) -> QLabel:
    """Small warning-style label for limited-validation features."""
    label = QLabel(text)
    label.setObjectName("ExperimentalNotice")
    label.setWordWrap(True)
    return label


# -- Info row --------------------------------------------------------------

def info_row(label: str, value: str = "") -> tuple[QLabel, QLabel]:
    """Create a label + value pair for key-value display.

    Returns (label_widget, value_widget) so the caller can update the value later.
    """
    lbl = QLabel(label)
    lbl.setObjectName("BodyLabel")
    val = QLabel(value)
    val.setObjectName("BodyLabel")
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl, val


# -- Separator -------------------------------------------------------------

def separator() -> QFrame:
    """Thin horizontal line separator."""
    line = QFrame()
    line.setObjectName("Separator")
    line.setFrameShape(QFrame.Shape.HLine)
    return line


# -- Buttons ---------------------------------------------------------------

def primary_button(text: str, callback=None) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("PrimaryButton")
    if callback:
        button.clicked.connect(callback)
    return button


def secondary_button(text: str, callback=None) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("SecondaryButton")
    if callback:
        button.clicked.connect(callback)
    return button


def destructive_button(text: str, callback=None) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("DestructiveButton")
    if callback:
        button.clicked.connect(callback)
    return button


def channel_button(text: str, callback=None) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("ChannelButton")
    button.setCheckable(True)
    if callback:
        button.clicked.connect(callback)
    return button


def profile_tile(text: str, icon: str = "", callback=None) -> QPushButton:
    """Large tile button for profile selection (Armoury Crate style)."""
    label = f"{icon}  {text}" if icon else text
    button = QPushButton(label)
    button.setObjectName("ProfileTile")
    button.setCheckable(True)
    if callback:
        button.clicked.connect(callback)
    return button


# -- Action bar ------------------------------------------------------------

def action_bar(*buttons: QPushButton, align_left: bool = False) -> QHBoxLayout:
    """Horizontal row of buttons. Right-aligned by default."""
    row = QHBoxLayout()
    row.setSpacing(8)
    if not align_left:
        row.addStretch(1)
    for btn in buttons:
        row.addWidget(btn)
    if align_left:
        row.addStretch(1)
    return row


# -- Form row helper -------------------------------------------------------

def form_row(label: str, *widgets: QWidget, stretch_last: bool = True) -> QHBoxLayout:
    """Label on the left, controls on the right."""
    row = QHBoxLayout()
    row.setSpacing(10)
    lbl = QLabel(label)
    lbl.setObjectName("BodyLabel")
    lbl.setFixedWidth(160)
    row.addWidget(lbl)
    for i, w in enumerate(widgets):
        if stretch_last and i == len(widgets) - 1:
            row.addWidget(w, 1)
        else:
            row.addWidget(w)
    return row


# -- Decorative panel (Armoury Crate-style telemetry container) -----------

class _PanelFrame(QFrame):
    """QFrame that paints small L-shaped corner accents in the panel accent color."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._accent_len = 14
        self._accent_inset = 6

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        p = get_palette(get_active_theme())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(p.panel_accent), 1.5)
        painter.setPen(pen)

        r = QRectF(self.rect()).adjusted(
            self._accent_inset, self._accent_inset,
            -self._accent_inset, -self._accent_inset,
        )
        a = self._accent_len

        # Top-left corner
        painter.drawLine(r.topLeft(), r.topLeft() + type(r.topLeft())(a, 0))
        painter.drawLine(r.topLeft(), r.topLeft() + type(r.topLeft())(0, a))
        # Top-right corner
        painter.drawLine(r.topRight(), r.topRight() + type(r.topRight())(-a, 0))
        painter.drawLine(r.topRight(), r.topRight() + type(r.topRight())(0, a))
        # Bottom-left corner
        painter.drawLine(r.bottomLeft(), r.bottomLeft() + type(r.bottomLeft())(a, 0))
        painter.drawLine(r.bottomLeft(), r.bottomLeft() + type(r.bottomLeft())(0, -a))
        # Bottom-right corner
        painter.drawLine(r.bottomRight(), r.bottomRight() + type(r.bottomRight())(-a, 0))
        painter.drawLine(r.bottomRight(), r.bottomRight() + type(r.bottomRight())(0, -a))
        painter.end()


def panel(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Decorative telemetry panel with cyan corner bracket accents."""
    frame = _PanelFrame()
    frame.setObjectName("Panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    if title:
        t = QLabel(title.upper())
        t.setObjectName("PanelTitle")
        layout.addWidget(t)
    return frame, layout


# -- Mode bar (horizontal operating-mode selector) -------------------------

def mode_bar(
    options: list[tuple[str, str]],
    callback=None,
) -> tuple[QFrame, dict[str, QPushButton]]:
    """Horizontal row of mode buttons with active underline accent.

    *options* is a list of (key, display_label) tuples.
    Returns (container_frame, {key: button}).
    """
    frame = QFrame()
    frame.setObjectName("ModeBar")
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(4, 0, 4, 0)
    layout.setSpacing(0)
    buttons: dict[str, QPushButton] = {}
    for key, label in options:
        btn = QPushButton(label)
        btn.setObjectName("ModeButton")
        btn.setCheckable(True)
        if callback:
            btn.clicked.connect(lambda checked=False, k=key: callback(k))
        buttons[key] = btn
        layout.addWidget(btn, 1)
    return frame, buttons


# -- Stat bar (progress bar) -----------------------------------------------

def stat_bar(
    label: str,
    value: str = "",
    percent: int = 0,
    color: str | None = None,
) -> tuple[QWidget, QLabel, QLabel, QFrame]:
    """Progress bar row: label left, value right, bar underneath.

    Returns (container, label_widget, value_widget, fill_frame).
    The fill_frame width is set to *percent*% of its parent.
    """
    container = QWidget()
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(3)

    # Label + value row
    top = QHBoxLayout()
    top.setContentsMargins(0, 0, 0, 0)
    lbl = QLabel(label)
    lbl.setObjectName("StatLabel")
    val = QLabel(value)
    val.setObjectName("StatValue")
    val.setAlignment(Qt.AlignmentFlag.AlignRight)
    top.addWidget(lbl)
    top.addStretch(1)
    top.addWidget(val)
    outer.addLayout(top)

    # Bar track
    track = QFrame()
    track.setObjectName("StatBar")
    track.setFixedHeight(6)

    fill = QFrame(track)
    fill.setObjectName("StatBarFill")
    fill.setFixedHeight(6)
    pct = max(0, min(100, percent))
    # We set the fill width using a style approach
    p = get_palette(get_active_theme())
    fill_color = color or p.bar_fill
    fill.setStyleSheet(f"background: {fill_color}; border-radius: 3px;")

    # Store percent for resizing
    track._fill_widget = fill  # type: ignore[attr-defined]
    track._fill_pct = pct  # type: ignore[attr-defined]

    # Use a resize event to properly size the fill
    original_resize = track.resizeEvent

    def _resize(event):
        if original_resize:
            original_resize(event)
        w = int(track.width() * track._fill_pct / 100)  # type: ignore[attr-defined]
        track._fill_widget.setFixedWidth(max(0, w))  # type: ignore[attr-defined]

    track.resizeEvent = _resize  # type: ignore[assignment]

    outer.addWidget(track)
    return container, lbl, val, fill


def update_stat_bar(track: QFrame, percent: int, color: str | None = None) -> None:
    """Update a stat_bar fill percentage after creation."""
    pct = max(0, min(100, percent))
    track._fill_pct = pct  # type: ignore[attr-defined]
    if color:
        track._fill_widget.setStyleSheet(  # type: ignore[attr-defined]
            f"background: {color}; border-radius: 3px;"
        )
    w = int(track.width() * pct / 100)
    track._fill_widget.setFixedWidth(max(0, w))  # type: ignore[attr-defined]


# -- Stat row (key-value pair) ---------------------------------------------

def stat_row(label: str, value: str = "") -> tuple[QWidget, QLabel, QLabel]:
    """Horizontal key-value row with right-aligned value.

    Returns (container, label_widget, value_widget).
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setSpacing(8)
    lbl = QLabel(label)
    lbl.setObjectName("StatLabel")
    val = QLabel(value)
    val.setObjectName("StatValue")
    val.setAlignment(Qt.AlignmentFlag.AlignRight)
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    layout.addWidget(lbl)
    layout.addStretch(1)
    layout.addWidget(val)
    return container, lbl, val
