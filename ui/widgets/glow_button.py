"""
发光效果按钮
"""
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QEnterEvent


class GlowButton(QPushButton):
    """带有发光脉冲效果的按钮"""

    def __init__(self, text: str, color: str = "#00b4ff", parent=None):
        super().__init__(text, parent)
        self._color = color
        self._glow_opacity = 0.0

        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        self.setStyleSheet("""
            GlowButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c},
                    stop:1 {c}dd
                );
                color: #060a10;
                border: none;
                border-radius: 8px;
                font-family: "Exo 2";
                font-size: 14px;
                font-weight: 700;
                padding: 0 28px;
            }}
            GlowButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c}ee,
                    stop:1 {c}
                );
            }}
            GlowButton:pressed {{
                background: {c}cc;
            }}
            GlowButton:disabled {{
                background: #1c2a4a;
                color: #4a5c78;
            }}
        """.format(c=self._color))

    def enterEvent(self, event: QEnterEvent):
        self.setFixedHeight(46)

    def leaveEvent(self, event):
        self.setFixedHeight(44)
