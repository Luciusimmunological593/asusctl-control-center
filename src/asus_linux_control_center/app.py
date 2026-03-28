from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .cli import build_parser
from .constants import APP_NAME
from .logging_utils import configure_logging
from .services import (
    ControlCenterController,
    ControlService,
    format_diagnostics_report,
    snapshot_as_json,
)
from .settings import SettingsStore
from .ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.diagnostics or args.diagnostics_json:
        logger = configure_logging(console=True)
        service = ControlService(logger)
        snapshot = service.build_snapshot()
        if args.diagnostics_json:
            print(snapshot_as_json(snapshot))
        else:
            print(format_diagnostics_report(snapshot))
        return 0

    logger = configure_logging(console=False)
    service = ControlService(logger)

    app = QApplication([sys.argv[0], *(argv or [])])
    app.setApplicationName(APP_NAME)

    settings = SettingsStore()
    controller = ControlCenterController(service)
    window = MainWindow(controller, settings)
    window.show()
    controller.refresh(settings.load().last_curve_profile)
    return app.exec()
