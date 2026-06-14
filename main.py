"""
CS2 Highlight Studio v1.0.260612
"""
import sys
import os
import ctypes

if sys.platform == "win32":
    kernel32 = ctypes.windll.kernel32
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

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

    try:
        from assets.icon import get_app_icon
        app.setWindowIcon(get_app_icon())
    except Exception:
        pass

    from ui.theme import get_stylesheet
    app.setStyleSheet(get_stylesheet())

    # ── Splash ──
    from ui.splash import AppSplash
    splash = AppSplash()
    splash.show()

    # ── Check dependencies ──
    splash.update(5, "\u68c0\u67e5\u4f9d\u8d56...")
    splash.check_dependencies()

    # ── Settings ──
    from config.settings import AppSettings
    from core.translations import set_lang, t

    settings = AppSettings()
    set_lang(settings.get("language", "zh"))
    app.setApplicationName(t("app_name"))

    splash.update(25, "\u52a0\u8f7d\u8bbe\u7f6e...")

    # ── Services ──
    from core.obs_controller import OBSController
    from core.gsi_server import GSIServer
    from core.match_watcher import MatchWatcher

    splash.update(40, "\u521d\u59cb\u5316 OBS...")
    obs = OBSController(settings)

    splash.update(55, "\u521d\u59cb\u5316 GSI...")
    gsi = GSIServer(settings)

    splash.update(65, "\u521d\u59cb\u5316 Watcher...")
    watcher = MatchWatcher(settings)

    # ── Window ──
    from ui.main_window import MainWindow

    splash.update(75, "\u52a0\u8f7d\u754c\u9762...")
    window = MainWindow(settings, obs, gsi, watcher)

    splash.update(85, "\u8fde\u63a5 GSI...")
    if settings.get("gsi_auto_start", True):
        try:
            gsi.start()
        except Exception:
            pass

    splash.update(92, "\u8fde\u63a5 OBS...")
    if settings.get("obs_auto_connect", True):
        try:
            obs.connect()
        except Exception:
            pass

    splash.update(100, "\u52a0\u8f7d\u5b8c\u6210!",
                  "\u51c6\u5907\u5c31\u7eea")
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
