from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from ...constants import DEFAULT_FAN_TEMPS
from ...utils import clamp, make_non_decreasing_curve, normalize_curve_values
from ..styles import get_active_theme, get_palette


class CurveEditor(QWidget):
    curveChanged = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._temps = DEFAULT_FAN_TEMPS[:]
        self._values = [24, 36, 46, 58, 68, 78, 90, 100]
        self._drag_index: int | None = None
        self._readonly = False
        self.setMinimumHeight(340)
        self.setMouseTracking(True)

    def set_curve(self, temps: list[int], values: list[int]) -> None:
        self._temps = list(temps) if temps else DEFAULT_FAN_TEMPS[:]
        self._values = make_non_decreasing_curve(normalize_curve_values(values, len(self._temps)))
        self.update()

    def curve(self) -> list[int]:
        return list(self._values)

    def set_read_only(self, enabled: bool) -> None:
        self._readonly = enabled
        self.update()

    def _plot_rect(self) -> QRectF:
        margin_left = 60
        margin_top = 34
        margin_right = 28
        margin_bottom = 70
        return QRectF(
            margin_left,
            margin_top,
            max(10.0, self.width() - margin_left - margin_right),
            max(10.0, self.height() - margin_top - margin_bottom),
        )

    def _point_for_index(self, index: int) -> QPointF:
        rect = self._plot_rect()
        if len(self._temps) == 1:
            x = rect.left()
        else:
            x = rect.left() + rect.width() * (index / (len(self._temps) - 1))
        y = rect.bottom() - rect.height() * (self._values[index] / 100.0)
        return QPointF(x, y)

    def _index_at_position(self, pos: QPointF) -> int | None:
        for index in range(len(self._temps)):
            point = self._point_for_index(index)
            if abs(point.x() - pos.x()) + abs(point.y() - pos.y()) <= 16:
                return index
        return None

    def _update_dragged_point(self, index: int, y_pos: float) -> None:
        rect = self._plot_rect()
        ratio = 1.0 - ((y_pos - rect.top()) / max(1.0, rect.height()))
        proposed = clamp(round(ratio * 100), 0, 100)
        if index > 0:
            proposed = max(proposed, self._values[index - 1])
        if index < len(self._values) - 1:
            proposed = min(proposed, self._values[index + 1])
        self._values[index] = proposed
        self.curveChanged.emit(self.curve())
        self.update()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if self._readonly or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        index = self._index_at_position(event.position())
        if index is not None:
            self._drag_index = index
            self._update_dragged_point(index, event.position().y())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_index is not None and not self._readonly:
            self._update_dragged_point(self._drag_index, event.position().y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_index = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        p = get_palette(get_active_theme())
        bg_color = QColor(p.panel_bg)
        border_color = QColor(p.panel_border)
        grid_color = QColor(p.border_light)
        label_color = QColor(p.text_muted)
        line_color = QColor(p.accent)
        dot_outline = QColor(p.bg)
        dot_fill = QColor(p.accent) if not self._readonly else QColor(p.text_muted)
        footer_color = QColor(p.text_sec)
        # Subtle fill under the curve
        fill_color = QColor(p.accent)
        fill_color.setAlpha(25)

        # Dark background for the entire widget area
        painter.fillRect(self.rect(), QColor(p.bg))

        rect = self._plot_rect()

        # Plot area background
        painter.fillRect(rect.toRect(), bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 8, 8)

        for percent in range(0, 101, 25):
            y = rect.bottom() - rect.height() * (percent / 100.0)
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(QPen(label_color, 1))
            painter.drawText(8, int(y + 5), f"{percent}%")

        for index, temp in enumerate(self._temps):
            point = self._point_for_index(index)
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(QPointF(point.x(), rect.top()), QPointF(point.x(), rect.bottom()))
            painter.setPen(QPen(label_color, 1))
            painter.drawText(int(point.x() - 12), int(rect.bottom() + 28), f"{temp}°C")

        points = [self._point_for_index(index) for index in range(len(self._temps))]

        # Fill under curve
        if points:
            fill_path = QPainterPath()
            fill_path.moveTo(QPointF(points[0].x(), rect.bottom()))
            for pt in points:
                fill_path.lineTo(pt)
            fill_path.lineTo(QPointF(points[-1].x(), rect.bottom()))
            fill_path.closeSubpath()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill_color)
            painter.drawPath(fill_path)

        # Curve line
        if points:
            path = QPainterPath()
            path.moveTo(points[0])
            for point in points[1:]:
                path.lineTo(point)
            painter.setPen(QPen(line_color, 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # Dots with glow effect
        for i, point in enumerate(points):
            # Outer glow
            glow = QColor(p.accent) if not self._readonly else QColor(p.text_muted)
            glow.setAlpha(40)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(point, 11, 11)
            # Main dot
            painter.setPen(QPen(dot_outline, 2))
            painter.setBrush(dot_fill)
            painter.drawEllipse(point, 6, 6)
            # Value label above
            painter.setPen(QPen(label_color, 1))
            painter.drawText(int(point.x() - 10), int(point.y() - 18), f"{self._values[i]}%")

        painter.setPen(QPen(footer_color, 1))
        footer = "Read-only preview" if self._readonly else "Drag points to adjust the curve"
        painter.drawText(int(rect.left()), int(self.height() - 18), footer)
