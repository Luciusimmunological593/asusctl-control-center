from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .constants import APP_ID
from .paths import log_file


def configure_logging(*, console: bool = False) -> logging.Logger:
    logger = logging.getLogger(APP_ID)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = RotatingFileHandler(
        log_file(),
        maxBytes=512 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.info("Logging initialized")
    return logger
