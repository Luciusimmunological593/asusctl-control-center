"""Main application window — thin shell with sidebar, page stack, and toast overlay.

All page-specific logic lives in ui/pages/. This module only handles
window chrome, navigation, signal routing, and session persistence.
"""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..constants import APP_NAME, APP_VERSION
from ..models import ActionOutcome, SystemSnapshot
from ..settings import SettingsStore
from .pages.diagnostics import DiagnosticsPage
from .pages.hardware import HardwarePage
from .pages.overview import OverviewPage
from .pages.performance import PerformancePage
from .pages.settings import SettingsPage
from .styles import get_stylesheet, set_active_theme
from .widgets.toast_overlay import ToastOverlay

_SCROLL_STEALING_TYPES = (QComboBox, QAbstractSpinBox, QSlider)


class _WheelGuard(QObject):
    """Prevent unfocused combo boxes, spin boxes, and sliders from eating
    mouse-wheel events so the parent QScrollArea can scroll instead."""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(obj, _SCROLL_STEALING_TYPES)
            and not obj.hasFocus()
        ):
            # Forward the event to the parent (scroll area will pick it up)
            event.ignore()
            return True
        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    """Application shell — sidebar navigation, page stack, toast overlay."""

    def __init__(self, controller, settings_store: SettingsStore):
        super().__init__()
        self.controller = controller
        self.settings_store = settings_store
        self.settings = settings_store.load()
        self._busy = False

        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(self.settings.window_width, self.settings.window_height)
        self._apply_theme(self.settings.theme)

        self._pages: dict[str, QWidget] = {}
        self._page_wrappers: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}

        self._build_ui()
        self._connect_signals()
        self.switch_page(self.settings.last_page)

    # -----------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sidebar — flush left, full height
        self.sidebar = self._build_sidebar()
        outer.addWidget(self.sidebar, 0)

        # Content area — explicit background to block system dark-theme bleed
        content = QWidget()
        content.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 16)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self._register_pages()
        content_layout.addWidget(self.stack, 1)

        outer.addWidget(content, 1)
        self.setCentralWidget(root)

        # Status bar
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

        # Toast overlay — floats over the content area
        self.toast = ToastOverlay(content)

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        frame.setFixedWidth(180)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(0)

        # Brand header
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setObjectName("SidebarTitle")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(title)

        caption = QLabel(f"v{APP_VERSION}")
        caption.setObjectName("SidebarCaption")
        header_layout.addWidget(caption)
        layout.addWidget(header_widget)
        layout.addSpacing(16)

        # Section: Dashboard
        section1 = QLabel("DASHBOARD")
        section1.setObjectName("SidebarSectionHeader")
        layout.addWidget(section1)

        for key, icon, label in [
            ("overview", "\U0001f3e0", "Home"),
        ]:
            button = QPushButton(f"  {icon}   {label}")
            button.setCheckable(True)
            button.setObjectName("NavButton")
            button.clicked.connect(
                lambda checked=False, page=key: self.switch_page(page),
            )
            self.nav_buttons[key] = button
            layout.addWidget(button)

        # Section: System
        section2 = QLabel("SYSTEM")
        section2.setObjectName("SidebarSectionHeader")
        layout.addWidget(section2)

        for key, icon, label in [
            ("performance", "\u26a1", "Performance"),
            ("hardware", "\U0001f527", "Hardware"),
        ]:
            button = QPushButton(f"  {icon}   {label}")
            button.setCheckable(True)
            button.setObjectName("NavButton")
            button.clicked.connect(
                lambda checked=False, page=key: self.switch_page(page),
            )
            self.nav_buttons[key] = button
            layout.addWidget(button)

        # Section: Tools
        section3 = QLabel("TOOLS")
        section3.setObjectName("SidebarSectionHeader")
        layout.addWidget(section3)

        for key, icon, label in [
            ("diagnostics", "\U0001f50d", "Diagnostics"),
            ("settings", "\u2699", "Settings"),
        ]:
            button = QPushButton(f"  {icon}   {label}")
            button.setCheckable(True)
            button.setObjectName("NavButton")
            button.clicked.connect(
                lambda checked=False, page=key: self.switch_page(page),
            )
            self.nav_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)

        footer = QLabel("  Open-source utility\n  Unofficial and not affiliated with ASUS")
        footer.setObjectName("SidebarCaption")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return frame

    def _register_pages(self) -> None:
        self._pages["overview"] = OverviewPage(self.controller, self.settings)
        self._pages["performance"] = PerformancePage(self.controller, self.settings)
        self._pages["hardware"] = HardwarePage(self.controller, self.settings)
        self._pages["diagnostics"] = DiagnosticsPage(self.controller, self.settings)
        self._pages["settings"] = SettingsPage(self.controller, self.settings)

        self._wheel_guard = _WheelGuard(self)

        for key, page in self._pages.items():
            wrapper = QScrollArea()
            wrapper.setWidgetResizable(True)
            wrapper.setFrameShape(QFrame.Shape.NoFrame)
            wrapper.setWidget(page)
            self._page_wrappers[key] = wrapper
            self.stack.addWidget(wrapper)

            # Prevent combo boxes, spinners, sliders from eating wheel
            for child in page.findChildren(QWidget):
                if isinstance(child, _SCROLL_STEALING_TYPES):
                    child.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                    child.installEventFilter(self._wheel_guard)

    # -----------------------------------------------------------------
    # Signals
    # -----------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.controller.snapshot_ready.connect(self._apply_snapshot)
        self.controller.action_finished.connect(self._handle_action_finished)
        self.controller.error.connect(self._handle_error)
        self.controller.busy_changed.connect(self._set_busy)
        settings_page = self._pages.get("settings")
        if settings_page is not None:
            settings_page.theme_changed.connect(self._apply_theme)

    # -----------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------

    def switch_page(self, key: str) -> None:
        if key not in self._page_wrappers:
            key = "overview"
        self.stack.setCurrentWidget(self._page_wrappers[key])
        for name, button in self.nav_buttons.items():
            button.setChecked(name == key)
        self.settings.last_page = key

    # -----------------------------------------------------------------
    # Controller signal handlers
    # -----------------------------------------------------------------

    def _apply_snapshot(self, snapshot: object) -> None:
        if not isinstance(snapshot, SystemSnapshot):
            return
        for page in self._pages.values():
            page.apply_snapshot(snapshot)

    def _set_busy(self, busy: bool) -> None:
        if busy and not self._busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        if not busy and self._busy:
            QApplication.restoreOverrideCursor()
        self._busy = busy
        for page in self._pages.values():
            page.set_busy(busy)
        self.statusBar().showMessage("Working\u2026" if busy else "Ready")

    def _handle_action_finished(self, outcome: object) -> None:
        if not isinstance(outcome, ActionOutcome):
            return
        level = "success" if outcome.success else "warning"
        self.toast.show_toast(outcome.message, level=level, duration=5000)
        self.statusBar().showMessage(outcome.message, 6000)
        if not outcome.success:
            QMessageBox.warning(self, outcome.title, outcome.message)

    def _handle_error(self, message: str) -> None:
        self.toast.show_toast("An operation failed. See details.", level="error", duration=6000)
        QMessageBox.critical(self, APP_NAME, message)
        self.statusBar().showMessage("Operation failed")

    # -----------------------------------------------------------------
    # Theme
    # -----------------------------------------------------------------

    def _apply_theme(self, theme: str) -> None:
        set_active_theme(theme)
        self.setStyleSheet(get_stylesheet(theme))
        # Force curve editor repaint so it picks up new palette
        for page in getattr(self, "_pages", {}).values():
            page.update()

    # -----------------------------------------------------------------
    # Window lifecycle
    # -----------------------------------------------------------------

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        for page in self._pages.values():
            page.save_state(self.settings)
        self.settings_store.save(self.settings)
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        # Keep the toast overlay covering the content area
        if hasattr(self, "toast"):
            content = self.centralWidget()
            if content:
                # Map content geometry to reposition overlay
                self.toast.reposition(content.size())
