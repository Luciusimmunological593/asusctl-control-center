"""
Design system stylesheet for ASUS Linux Control Center.

Armoury Crate-inspired dark gaming aesthetic with ROG red accents.
Color tokens, spacing, typography, and component styles.
Supports light and dark themes via ``get_stylesheet(theme)``.
"""

from __future__ import annotations

from dataclasses import dataclass

# -- Spacing tokens (theme-independent) ----------------------------------
SP_XS = 4
SP_SM = 8
SP_MD = 12
SP_LG = 16
SP_XL = 24
SP_2XL = 32


# -- Color palette dataclass ---------------------------------------------
@dataclass(frozen=True, slots=True)
class _Palette:
    bg: str
    surface: str
    surface_elevated: str
    border: str
    border_light: str
    text: str
    text_sec: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_light: str
    success: str
    success_bg: str
    warning: str
    warning_bg: str
    error: str
    error_bg: str
    sidebar_bg: str
    sidebar_text: str
    sidebar_active_text: str
    # Extra derived tokens
    btn_secondary_hover_bg: str
    btn_secondary_hover_border: str
    btn_channel_bg: str
    btn_channel_hover_bg: str
    disabled_bg: str
    disabled_border: str
    disabled_text: str
    grove_bg: str
    header_bg: str
    scrollbar_handle: str
    scrollbar_handle_hover: str
    unavailable_bg: str
    unavailable_border: str
    warning_banner_border: str
    # Armoury Crate extras
    tile_bg: str
    tile_hover_bg: str
    tile_active_bg: str
    tile_active_border: str
    cyan: str
    # Panel / telemetry tokens
    panel_accent: str
    panel_bg: str
    panel_border: str
    bar_bg: str
    bar_fill: str
    section_header_text: str


# -- Armoury Crate Dark palette (ROG-inspired) --
_DARK = _Palette(
    bg="#0a0a12",
    surface="#151520",
    surface_elevated="#1a1a2e",
    border="#252535",
    border_light="#1e1e30",
    text="#e8e8f0",
    text_sec="#a0a0b8",
    text_muted="#606078",
    accent="#ff0040",
    accent_hover="#cc0033",
    accent_light="#2e0a18",
    success="#00e676",
    success_bg="#0a2e1a",
    warning="#ffab00",
    warning_bg="#2e2000",
    error="#ff1744",
    error_bg="#2e0a10",
    sidebar_bg="#07070e",
    sidebar_text="#606078",
    sidebar_active_text="#ffffff",
    btn_secondary_hover_bg="#1e1e34",
    btn_secondary_hover_border="#3a3a50",
    btn_channel_bg="#151520",
    btn_channel_hover_bg="#1e1e34",
    disabled_bg="#12121e",
    disabled_border="#252535",
    disabled_text="#404058",
    grove_bg="#1e1e30",
    header_bg="#12121e",
    scrollbar_handle="#252535",
    scrollbar_handle_hover="#3a3a50",
    unavailable_bg="#0e0e18",
    unavailable_border="#252535",
    warning_banner_border="#665200",
    tile_bg="#12121e",
    tile_hover_bg="#1a1a2e",
    tile_active_bg="#2e0a18",
    tile_active_border="#ff0040",
    cyan="#00d4aa",
    # Panel / telemetry
    panel_accent="#00d4aa",
    panel_bg="#0e0e18",
    panel_border="#1a1a2e",
    bar_bg="#1a1a2e",
    bar_fill="#ff0040",
    section_header_text="#505068",
)

# -- Light palette (softer Armoury Crate adaptation) --
_LIGHT = _Palette(
    bg="#f0f0f4",
    surface="#ffffff",
    surface_elevated="#f8f8fc",
    border="#d8d8e0",
    border_light="#e8e8ee",
    text="#1a1a24",
    text_sec="#505060",
    text_muted="#909098",
    accent="#cc0033",
    accent_hover="#aa002a",
    accent_light="#ffe0e8",
    success="#2e7d32",
    success_bg="#e8f5e9",
    warning="#e65100",
    warning_bg="#fff3e0",
    error="#c62828",
    error_bg="#ffebee",
    sidebar_bg="#f8f8fc",
    sidebar_text="#606070",
    sidebar_active_text="#1a1a24",
    btn_secondary_hover_bg="#f4f4f8",
    btn_secondary_hover_border="#c0c0cc",
    btn_channel_bg="#f4f4f8",
    btn_channel_hover_bg="#eaeaf0",
    disabled_bg="#f4f4f8",
    disabled_border="#a0a0a8",
    disabled_text="#d0d0d8",
    grove_bg="#e0e0e8",
    header_bg="#f4f4f8",
    scrollbar_handle="#c0c0cc",
    scrollbar_handle_hover="#a0a0b0",
    unavailable_bg="#f4f4f8",
    unavailable_border="#d0d0d8",
    warning_banner_border="#ffcc80",
    tile_bg="#f4f4f8",
    tile_hover_bg="#eaeaf0",
    tile_active_bg="#ffe0e8",
    tile_active_border="#cc0033",
    cyan="#0090b0",
    # Panel / telemetry
    panel_accent="#0090b0",
    panel_bg="#f8f8fc",
    panel_border="#d8d8e0",
    bar_bg="#e0e0e8",
    bar_fill="#cc0033",
    section_header_text="#909098",
)

_PALETTES: dict[str, _Palette] = {"light": _LIGHT, "dark": _DARK}

# -- Module-level color aliases (always reflect the *active* palette) -----
# These are imported by toast_overlay.py and status_indicator.py.
# They default to dark at import time and are updated by set_active_theme().
ACCENT = _DARK.accent
ERROR = _DARK.error
SUCCESS = _DARK.success
WARNING = _DARK.warning
TEXT_MUTED = _DARK.text_muted

# Legacy alias kept for main_window.py import
APP_STYLESHEET = ""

# Current theme name — readable by any module
_active_theme = "dark"


def get_active_theme() -> str:
    """Return the name of the currently active theme."""
    return _active_theme


def get_palette(theme: str = "dark") -> _Palette:
    """Return the palette dataclass for *theme*."""
    return _PALETTES.get(theme, _DARK)


def set_active_theme(theme: str) -> None:
    """Set module-level color constants to match *theme* and rebuild APP_STYLESHEET."""
    global ACCENT, ERROR, SUCCESS, WARNING, TEXT_MUTED, APP_STYLESHEET, _active_theme  # noqa: PLW0603
    p = get_palette(theme)
    ACCENT = p.accent
    ERROR = p.error
    SUCCESS = p.success
    WARNING = p.warning
    TEXT_MUTED = p.text_muted
    APP_STYLESHEET = _build_stylesheet(p)
    _active_theme = theme


def get_stylesheet(theme: str = "dark") -> str:
    """Build and return the full QSS stylesheet for *theme*."""
    return _build_stylesheet(get_palette(theme))


# -- Stylesheet builder ---------------------------------------------------
def _build_stylesheet(p: _Palette) -> str:  # noqa: C901
    return f"""
/* ---- Base ---- */
QMainWindow {{
    background: {p.bg};
}}
QWidget {{
    color: {p.text};
    font-family: "Inter", "IBM Plex Sans", "Noto Sans", "Ubuntu", sans-serif;
    font-size: 13px;
}}
QWidget#ContentArea {{
    background: {p.bg};
}}
QStackedWidget {{
    background: {p.bg};
}}

/* ---- Sidebar ---- */
QFrame#Sidebar {{
    background: {p.sidebar_bg};
    border: none;
    border-right: 1px solid {p.border};
}}
QLabel#SidebarTitle {{
    color: {p.accent};
    font-size: 15px;
    font-weight: 800;
    padding: 0px;
    letter-spacing: 1px;
}}
QLabel#SidebarCaption {{
    color: {p.sidebar_text};
    font-size: 11px;
}}
QPushButton#NavButton {{
    background: transparent;
    color: {p.sidebar_text};
    border: none;
    border-left: 4px solid transparent;
    border-radius: 0px;
    padding: 10px 14px 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#NavButton:hover {{
    color: {p.text};
    background: {p.tile_hover_bg};
}}
QPushButton#NavButton:checked {{
    color: {p.sidebar_active_text};
    border-left: 4px solid {p.accent};
    background: {p.accent_light};
    font-weight: 600;
}}

/* ---- Page titles ---- */
QLabel#PageTitle {{
    font-size: 22px;
    font-weight: 700;
    color: {p.text};
    padding: 0px;
}}
QLabel#PageSubtitle {{
    font-size: 13px;
    color: {p.text_muted};
    padding: 0px;
}}

/* ---- Cards ---- */
QFrame#Card {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: 10px;
}}

/* ---- Section headers ---- */
QLabel#SectionTitle {{
    font-size: 13px;
    font-weight: 700;
    color: {p.text};
    padding: 0px;
    letter-spacing: 0.5px;
}}
QLabel#SectionSubtitle {{
    font-size: 12px;
    color: {p.text_muted};
    padding: 0px;
}}
QLabel#ExperimentalNotice {{
    color: {p.warning};
    background: {p.warning_bg};
    border: 1px solid {p.warning_banner_border};
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 600;
}}

/* ---- Text variants ---- */
QLabel#CardTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {p.text};
}}
QLabel#ValueLabel {{
    font-size: 18px;
    font-weight: 700;
    color: {p.accent};
}}
QLabel#BodyLabel {{
    color: {p.text_sec};
    font-size: 13px;
}}
QLabel#MutedLabel {{
    color: {p.text_muted};
    font-size: 12px;
}}
QLabel#CaptionLabel {{
    color: {p.text_muted};
    font-size: 11px;
}}

/* ---- Buttons ---- */
QPushButton#PrimaryButton {{
    background: {p.accent};
    color: #ffffff;
    border: 1px solid {p.accent_hover};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton#PrimaryButton:hover {{
    background: {p.accent_hover};
}}
QPushButton#PrimaryButton:disabled {{
    background: {p.disabled_bg};
    border-color: {p.disabled_border};
    color: {p.disabled_text};
}}
QPushButton#SecondaryButton {{
    background: {p.surface};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#SecondaryButton:hover {{
    border-color: {p.btn_secondary_hover_border};
    background: {p.btn_secondary_hover_bg};
}}
QPushButton#SecondaryButton:disabled {{
    color: {p.text_muted};
    border-color: {p.border_light};
    background: {p.disabled_bg};
}}
QPushButton#DestructiveButton {{
    background: {p.error};
    color: #ffffff;
    border: 1px solid {p.error};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton#DestructiveButton:hover {{
    background: {p.error_bg};
    color: {p.error};
}}
QPushButton#ChannelButton {{
    background: {p.btn_channel_bg};
    color: {p.text_sec};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#ChannelButton:hover {{
    background: {p.btn_channel_hover_bg};
}}
QPushButton#ChannelButton:checked {{
    background: {p.accent_light};
    color: {p.accent};
    border-color: {p.accent};
}}
QPushButton#ChannelButton:disabled {{
    color: {p.text_muted};
    border-color: {p.border_light};
    background: {p.disabled_bg};
}}

/* ---- Profile tile buttons ---- */
QPushButton#ProfileTile {{
    background: {p.tile_bg};
    color: {p.text_sec};
    border: 1px solid {p.border};
    border-radius: 8px;
    padding: 14px 12px;
    font-size: 13px;
    font-weight: 600;
    text-align: center;
}}
QPushButton#ProfileTile:hover {{
    background: {p.tile_hover_bg};
    border-color: {p.btn_secondary_hover_border};
}}
QPushButton#ProfileTile:checked {{
    background: {p.tile_active_bg};
    color: {p.accent};
    border-color: {p.tile_active_border};
    border-width: 2px;
}}
QPushButton#ProfileTile:disabled {{
    color: {p.disabled_text};
    background: {p.disabled_bg};
    border-color: {p.disabled_border};
}}

/* ---- Form controls ---- */
QComboBox, QSpinBox {{
    background: {p.surface};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 20px;
}}
QComboBox:disabled, QSpinBox:disabled {{
    background: {p.disabled_bg};
    color: {p.text_muted};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {p.surface};
    color: {p.text};
    border: 1px solid {p.border};
    selection-background-color: {p.accent_light};
    selection-color: {p.text};
    padding: 4px;
    outline: none;
}}
QSlider::groove:horizontal {{
    border: 1px solid {p.border};
    background: {p.grove_bg};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {p.accent};
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:disabled {{
    background: {p.disabled_text};
}}
QSlider {{
    background: transparent;
}}

/* ---- Table ---- */
QTableWidget {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: 6px;
    gridline-color: {p.border_light};
    selection-background-color: {p.accent_light};
    selection-color: {p.text};
    font-size: 12px;
}}
QHeaderView::section {{
    background: {p.header_bg};
    color: {p.text_sec};
    border: none;
    border-bottom: 1px solid {p.border};
    padding: 6px 8px;
    font-size: 12px;
    font-weight: 600;
}}

/* ---- Text area ---- */
QPlainTextEdit {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 10px;
    font-family: "JetBrains Mono", "Fira Code", "Ubuntu Mono", monospace;
    font-size: 12px;
    color: {p.text};
}}

/* ---- Scroll area ---- */
QScrollArea {{
    border: none;
    background: {p.bg};
}}
QScrollArea > QWidget > QWidget {{
    background: {p.bg};
}}
QScrollBar:vertical {{
    background: {p.bg};
    width: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {p.scrollbar_handle};
    min-height: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p.scrollbar_handle_hover};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ---- Status bar ---- */
QStatusBar {{
    background: {p.sidebar_bg};
    border-top: 1px solid {p.border};
    font-size: 12px;
    color: {p.text_muted};
    padding: 2px 8px;
}}

/* ---- Toast notifications ---- */
QFrame#ToastSuccess {{
    background: {p.success_bg};
    border: 1px solid {p.success};
    border-radius: 6px;
}}
QFrame#ToastWarning {{
    background: {p.warning_bg};
    border: 1px solid {p.warning};
    border-radius: 6px;
}}
QFrame#ToastError {{
    background: {p.error_bg};
    border: 1px solid {p.error};
    border-radius: 6px;
}}
QFrame#ToastInfo {{
    background: {p.accent_light};
    border: 1px solid {p.accent};
    border-radius: 6px;
}}

/* ---- Unavailable notice ---- */
QFrame#UnavailableNotice {{
    background: {p.unavailable_bg};
    border: 1px solid {p.unavailable_border};
    border-radius: 8px;
}}

/* ---- Separator ---- */
QFrame#Separator {{
    background: {p.border_light};
    max-height: 1px;
    min-height: 1px;
}}

/* ---- Panel (decorative telemetry container) ---- */
QFrame#Panel {{
    background: {p.panel_bg};
    border: 1px solid {p.panel_border};
    border-radius: 10px;
}}
QLabel#PanelTitle {{
    font-size: 11px;
    font-weight: 700;
    color: {p.section_header_text};
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 0px;
}}

/* ---- Mode bar ---- */
QFrame#ModeBar {{
    background: {p.panel_bg};
    border: 1px solid {p.panel_border};
    border-radius: 8px;
}}
QPushButton#ModeButton {{
    background: transparent;
    color: {p.text_sec};
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#ModeButton:hover {{
    color: {p.text};
    background: rgba(255, 255, 255, 0.03);
}}
QPushButton#ModeButton:checked {{
    color: {p.accent};
    border-bottom: 2px solid {p.accent};
}}
QPushButton#ModeButton:disabled {{
    color: {p.disabled_text};
}}

/* ---- Stat bar (progress bar) ---- */
QFrame#StatBar {{
    background: {p.bar_bg};
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}
QFrame#StatBarFill {{
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}

/* ---- Stat row ---- */
QLabel#StatLabel {{
    color: {p.text_sec};
    font-size: 12px;
}}
QLabel#StatValue {{
    color: {p.text};
    font-size: 12px;
    font-weight: 600;
}}

/* ---- Sidebar section headers ---- */
QLabel#SidebarSectionHeader {{
    color: {p.section_header_text};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 12px 16px 4px 16px;
}}

/* ---- Warning banner ---- */
QFrame#WarningBanner {{
    background: {p.warning_bg};
    border: 1px solid {p.warning_banner_border};
    border-radius: 6px;
}}

/* ---- Input dialog (dark) ---- */
QInputDialog {{
    background: {p.surface};
}}
QLineEdit {{
    background: {p.bg};
    color: {p.text};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 6px 10px;
}}

/* ---- Message box (dark) ---- */
QMessageBox {{
    background: {p.surface};
}}

/* ---- File dialog ---- */
QFileDialog {{
    background: {p.surface};
}}
"""


# Initialise module-level constants and APP_STYLESHEET for dark theme
set_active_theme("dark")

# Keep legacy top-level aliases that other modules read at import time.
# The actual values are updated by set_active_theme().
BG = _DARK.bg
SURFACE = _DARK.surface
BORDER = _DARK.border
BORDER_LIGHT = _DARK.border_light
TEXT = _DARK.text
TEXT_SEC = _DARK.text_sec
