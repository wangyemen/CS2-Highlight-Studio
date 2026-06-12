"""
通知提示 (Toast)
"""
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer
from PyQt6.QtGui import QEnterEvent


class Toast(QLabel):
    """浮动通知提示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(40)
        self.hide()

        self.setStyleSheet("""
            QLabel {
                background: #162038;
                border: 1px solid #243456;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                color: #e8edf5;
            }
        """)

    def show_message(self, text: str, duration: int = 3000):
        self.setText(text)
        self.adjustSize()

        if self.parent():
            pw = self.parent().width()
            self.setFixedWidth(min(pw - 40, 400))
            self.move(
                (pw - self.width()) // 2,
                20,
            )

        self.show()
        self.raise_()

        QTimer.singleShot(duration, self.hide)
