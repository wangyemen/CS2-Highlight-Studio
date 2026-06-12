"""
Splash Screen - shown during startup initialization
"""
from PyQt6.QtWidgets import (
    QSplashScreen, QProgressBar, QLabel, QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen


def _create_splash_pixmap():
    """Generate splash image programmatically."""
    w, h = 500, 300
    px = QPixmap(w, h)
    px.fill(QColor("#080c14"))

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Border
    p.setPen(QPen(QColor("#1a2744"), 1))
    p.drawRect(0, 0, w - 1, h - 1)

    # Accent line top
    p.setPen(Qt.PenStyle.NoPen)
    p.fillRect(0, 0, w, 3, QColor("#00b4ff"))

    # Background glow
    p.setBrush(QColor(0, 180, 255, 15))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(150, 30, 200, 200)

    # CS2 text
    p.setPen(QColor("#00b4ff"))
    p.setFont(QFont("Exo 2", 40,
                     QFont.Weight.ExtraBold))
    p.drawText(
        0, 60, w, 60,
        Qt.AlignmentFlag.AlignCenter, "CS2")

    # Highlight Studio
    p.setPen(QColor("#8b99b0"))
    p.setFont(QFont("Exo 2", 16,
                     QFont.Weight.DemiBold))
    p.drawText(
        0, 115, w, 40,
        Qt.AlignmentFlag.AlignCenter,
        "Highlight Studio")

    # Version
    p.setPen(QColor("#4a5c78"))
    p.setFont(QFont("Consolas", 10))
    p.drawText(
        0, 145, w, 30,
        Qt.AlignmentFlag.AlignCenter,
        "v1.0.260612")

    # Green accent arc
    p.setPen(QPen(QColor("#00e68a"), 2))
    p.drawArc(180, 50, 140, 140, 30 * 16, 60 * 16)

    p.end()
    return px


class AppSplash:

    def __init__(self):
        pixmap = _create_splash_pixmap()
        self._splash = QSplashScreen(pixmap)
        self._splash.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen)
        self._splash.setStyleSheet(
            "QSplashScreen { background: #080c14; }")

        # Status text
        self._status = QLabel(
            "\u521d\u59cb\u5316\u4e2d...",
            self._splash)
        self._status.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 12px; "
            "color: #8b99b0; background: transparent;")
        self._status.setGeometry(
            0, 210, 500, 20)
        self._status.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self._bar = QProgressBar(self._splash)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setFixedWidth(300)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: #1a2744;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #00b4ff;
                border-radius: 2px;
            }
        """)
        self._bar.setGeometry(100, 235, 300, 4)

        # Phase label
        self._phase = QLabel("", self._splash)
        self._phase.setStyleSheet(
            "font-size: 11px; color: #4a5c78; "
            "background: transparent;")
        self._phase.setGeometry(
            0, 250, 500, 20)
        self._phase.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

    def show(self):
        self._splash.show()

    def update(self, progress, status, phase=""):
        """Update splash screen."""
        self._bar.setValue(progress)
        self._status.setText(status)
        if phase:
            self._phase.setText(phase)
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def finish(self, main_window):
        self._splash.finish(main_window)
