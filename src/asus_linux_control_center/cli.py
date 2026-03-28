from __future__ import annotations

import argparse

from .constants import APP_NAME, APP_VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Print a text diagnostics report and exit.",
    )
    parser.add_argument(
        "--diagnostics-json",
        action="store_true",
        help="Print a JSON diagnostics report and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}",
    )
    return parser
