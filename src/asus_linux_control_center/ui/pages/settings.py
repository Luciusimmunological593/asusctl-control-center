"""Settings page — runtime paths, about text, and build info."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ...constants import APP_NAME, APP_VERSION
from ...models import SystemSnapshot
from ...paths import config_dir, log_file, state_dir
from ..components import page_header, panel, secondary_button


class SettingsPage(QWidget):
    """Runtime paths and about information."""

    theme_changed = pyqtSignal(str)

    def __init__(self, controller, settings):
        super().__init__()
        self.controller = controller
        self.settings = settings
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header("Settings", "Application paths and project information"))

        # -- Paths panel --
        paths_card, paths_layout = panel("RUNTIME PATHS")

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnMinimumWidth(0, 120)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        entries = [
            ("Config", str(config_dir())),
            ("State", str(state_dir())),
            ("Log file", str(log_file())),
        ]
        for row, (label, path) in enumerate(entries):
            lbl = QLabel(label)
            lbl.setObjectName("MutedLabel")
            val = QLabel(path)
            val.setObjectName("BodyLabel")
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)

        self._timestamp_label = QLabel("—")
        self._timestamp_label.setObjectName("BodyLabel")
        ts_lbl = QLabel("Last snapshot")
        ts_lbl.setObjectName("MutedLabel")
        grid.addWidget(ts_lbl, len(entries), 0)
        grid.addWidget(self._timestamp_label, len(entries), 1)

        paths_layout.addLayout(grid)

        # Open buttons

        btn_row = QGridLayout()
        btn_row.setSpacing(8)
        btn_row.addWidget(
            secondary_button("Open config directory", lambda: self._open_path(config_dir())), 0, 0,
        )
        btn_row.addWidget(
            secondary_button("Open state directory", lambda: self._open_path(state_dir())), 0, 1,
        )
        btn_row.addWidget(
            secondary_button("Open log file", lambda: self._open_path(log_file())), 0, 2,
        )
        paths_layout.addLayout(btn_row)
        layout.addWidget(paths_card)

        # -- Appearance panel --
        appear_card, appear_layout = panel("APPEARANCE")

        theme_row = QHBoxLayout()
        theme_row.setSpacing(10)
        theme_lbl = QLabel("Theme")
        theme_lbl.setObjectName("MutedLabel")
        theme_lbl.setFixedWidth(120)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        self._theme_combo.setCurrentText(self.settings.theme.capitalize())
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(theme_lbl)
        theme_row.addWidget(self._theme_combo, 1)
        appear_layout.addLayout(theme_row)

        layout.addWidget(appear_card)

        # -- About panel --
        about_card, about_layout = panel("ABOUT")
        version_label = QLabel(f"{APP_NAME}  v{APP_VERSION}")
        version_label.setObjectName("SectionTitle")
        about_layout.addWidget(version_label)

        about_text = QLabel(
            "This application is an independent open-source, community-maintained desktop frontend "
            "for the Linux ASUS tool stack. "
            "It is unofficial and is not affiliated with, endorsed by, or sponsored by ASUS.\n\n"
            "It does not replace asusd or supergfxd, and it does not claim universal ASUS support. "
            "Capabilities depend on model, firmware, kernel support, installed services, and permissions."
        )
        about_text.setObjectName("BodyLabel")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        maintainer_label = QLabel("Project support")
        maintainer_label.setObjectName("SectionTitle")
        maintainer_label.setStyleSheet("font-size: 13px;")
        about_layout.addWidget(maintainer_label)

        contact = QLabel(
            'Maintainer: Osama Alhasanat<br>'
            'Project: <a href="https://github.com/OsamaAlhasanat/asusctl-control-center">github.com/OsamaAlhasanat/asusctl-control-center</a><br>'
            'Issues: <a href="https://github.com/OsamaAlhasanat/asusctl-control-center/issues">github.com/OsamaAlhasanat/asusctl-control-center/issues</a>'
        )
        contact.setObjectName("BodyLabel")
        contact.setWordWrap(True)
        contact.setOpenExternalLinks(True)
        contact.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        about_layout.addWidget(contact)
        layout.addWidget(about_card)

        layout.addStretch(1)

    # -- Public interface --------------------------------------------------

    def apply_snapshot(self, snapshot: SystemSnapshot) -> None:
        self._timestamp_label.setText(snapshot.timestamp or "—")

    def set_busy(self, busy: bool) -> None:
        pass

    def save_state(self, settings) -> None:
        settings.theme = self._theme_combo.currentText().lower()

    # -- Internal slots ----------------------------------------------------

    def _on_theme_changed(self, text: str) -> None:
        theme = text.lower()
        self.settings.theme = theme
        self.theme_changed.emit(theme)

    # -- Helpers -----------------------------------------------------------

    def _open_path(self, path) -> None:
        url = QUrl.fromLocalFile(str(path))
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self,
                "Open path",
                f"Could not open:\n{path}",
            )
