"""
CS2 Highlight Studio v1.0.260612
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

VERSION = "1.0.260612"


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont

    os.environ.setdefault(
        "QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationVersion(VERSION)
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Outfit", 10)
    font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # Set app icon
    try:
        from assets.icon import get_app_icon
        app.setWindowIcon(get_app_icon())
    except Exception:
        pass

    from ui.theme import get_stylesheet
    app.setStyleSheet(get_stylesheet())

    from config.settings import AppSettings
    from core.translations import set_lang, t
    from core.obs_controller import OBSController
    from core.gsi_server import GSIServer
    from core.match_watcher import MatchWatcher

    settings = AppSettings()
    set_lang(settings.get("language", "zh"))
    app.setApplicationName(t("app_name"))

    obs = OBSController(settings)
    gsi = GSIServer(settings)
    watcher = MatchWatcher(settings)

    from ui.main_window import MainWindow
    window = MainWindow(settings, obs, gsi, watcher)
    window.show()

    if settings.get("gsi_auto_start", True):
        gsi.start()
    if settings.get("obs_auto_connect", True):
        obs.connect()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
