"""
Splash Screen - with dependency checking
"""
import os
import subprocess
import sys

from PyQt6.QtWidgets import (
    QSplashScreen, QLabel, QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPen,
)


def _create_splash_pixmap():
    w, h = 500, 300
    px = QPixmap(w, h)
    px.fill(QColor("#080c14"))

    p = QPainter()
    p.begin(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    p.setPen(QPen(QColor("#1a2744"), 1))
    p.drawRect(0, 0, w - 1, h - 1)

    p.setPen(Qt.PenStyle.NoPen)
    p.fillRect(0, 0, w, 3, QColor("#00b4ff"))

    p.setBrush(QColor(0, 180, 255, 15))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(150, 30, 200, 200)

    p.setPen(QColor("#00b4ff"))
    p.setFont(QFont("Exo 2", 40,
                     QFont.Weight.ExtraBold))
    p.drawText(0, 60, w, 60,
               Qt.AlignmentFlag.AlignCenter, "CS2")

    p.setPen(QColor("#8b99b0"))
    p.setFont(QFont("Exo 2", 16,
                     QFont.Weight.DemiBold))
    p.drawText(0, 115, w, 40,
               Qt.AlignmentFlag.AlignCenter,
               "Highlight Studio")

    p.setPen(QColor("#4a5c78"))
    p.setFont(QFont("Consolas", 10))
    p.drawText(0, 145, w, 30,
               Qt.AlignmentFlag.AlignCenter,
               "v1.0.260612")

    p.setPen(QPen(QColor("#00e68a"), 2))
    p.drawArc(180, 50, 140, 140, 30 * 16, 60 * 16)

    p.end()
    return px


class _DependencyChecker(QThread):
    progress = pyqtSignal(int, str, str)
    finished = pyqtSignal(list)

    def run(self):
        _FLAGS = 0
        if sys.platform == "win32":
            _FLAGS = getattr(
                subprocess, "CREATE_NO_WINDOW", 0)

        missing = self._check()
        if not missing:
            self.finished.emit([])
            return

        self.progress.emit(
            10,
            "\u5b89\u88c5\u7f3a\u5931\u4f9d\u8d56...",
            "{} \u4e2a\u5305\u9700\u8981\u5b89\u88c5".format(
                len(missing)))

        total = len(missing)
        for i, pkg in enumerate(missing):
            pct = int(10 + (i / total) * 80)
            self.progress.emit(
                pct,
                "\u5b89\u88c5 {}...".format(pkg),
                "{}/{}".format(i + 1, total))
            ok = self._pip(pkg, _FLAGS)
            if not ok:
                self.progress.emit(
                    pct,
                    "\u5b89\u88c5 {} (\u955c\u50cf)...".format(pkg),
                    "{}/{}".format(i + 1, total))
                self._pip_mirror(pkg, _FLAGS)

        self.progress.emit(
            100, "\u5b89\u88c5\u5b8c\u6210!", "")
        self.finished.emit(missing)

    def _check(self):
        reqs = [
            ("pandas", "pandas"),
            ("numpy", "numpy"),
            ("polars", "polars"),
            ("pyarrow", "pyarrow"),
            ("demoparser2", "demoparser2"),
            ("obsws_python", "obsws_python"),
            ("websocket", "websocket_client"),
            ("tqdm", "tqdm"),
        ]
        missing = []
        for mod, pkg in reqs:
            try:
                __import__(mod)
            except ImportError:
                missing.append(pkg)
        return missing

    def _pip(self, pkg, flags):
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip",
                 "install", "-q",
                 "--disable-pip-version-check",
                 pkg],
                capture_output=True,
                timeout=300,
                creationflags=flags)
            return r.returncode == 0
        except Exception:
            return False

    def _pip_mirror(self, pkg, flags):
        for mirror in [
            "https://mirrors.aliyun.com/pypi/simple/",
            "https://pypi.tuna.tsinghua.edu.cn/simple/",
        ]:
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pip",
                     "install", "-q",
                     "--disable-pip-version-check",
                     "-i", mirror, pkg],
                    capture_output=True,
                    timeout=300,
                    creationflags=flags)
                if r.returncode == 0:
                    return True
            except Exception:
                continue
        return False


class AppSplash:

    def __init__(self):
        pixmap = _create_splash_pixmap()
        self._splash = QSplashScreen(pixmap)
        self._splash.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen)
        self._splash.setStyleSheet(
            "QSplashScreen { background: #080c14; }")

        self._status = QLabel(
            "\u68c0\u67e5\u4f9d\u8d56...",
            self._splash)
        self._status.setStyleSheet(
            "font-family: 'Exo 2'; "
            "font-size: 12px; "
            "color: #8b99b0; "
            "background: transparent;")
        self._status.setGeometry(0, 210, 500, 20)
        self._status.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

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

        self._phase = QLabel("", self._splash)
        self._phase.setStyleSheet(
            "font-size: 11px; color: #4a5c78; "
            "background: transparent;")
        self._phase.setGeometry(0, 250, 500, 20)
        self._phase.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

        self._checker = None

    def show(self):
        self._splash.show()

    def update(self, progress, status, phase=""):
        self._bar.setValue(progress)
        self._status.setText(status)
        if phase:
            self._phase.setText(phase)
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def check_dependencies(self):
        self._checker = _DependencyChecker()
        self._checker.progress.connect(
            self._on_dep_progress)
        self._checker.start()
        while self._checker.isRunning():
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            import time
            time.sleep(0.1)

    def _on_dep_progress(self, pct, msg, detail):
        self._bar.setValue(pct)
        self._status.setText(msg)
        if detail:
            self._phase.setText(detail)

    def finish(self, main_window):
        self._splash.finish(main_window)
