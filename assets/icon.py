"""
App icon loader - uses assets/icon.png
"""
import os
from PyQt6.QtGui import QIcon

_dir = os.path.dirname(os.path.abspath(__file__))
_ICON_PATH = os.path.join(_dir, "icon.png")
_cached_app = None
_cached_tray = None


def get_app_icon():
    global _cached_app
    if _cached_app is None:
        if os.path.isfile(_ICON_PATH):
            _cached_app = QIcon(_ICON_PATH)
        else:
            _cached_app = QIcon()
    return _cached_app


def get_tray_icon():
    global _cached_tray
    if _cached_tray is None:
        if os.path.isfile(_ICON_PATH):
            _cached_tray = QIcon(_ICON_PATH)
        else:
            _cached_tray = QIcon()
    return _cached_tray
