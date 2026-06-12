"""
状态信息卡片组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QEnterEvent


class StatusCard(QFrame):
    """带动态光晕效果的状态卡片"""

    def __init__(
        self,
        title: str = "",
        value: str = "—",
        subtitle: str = "",
        accent_color: str = "#00b4ff",
        icon: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.accent = accent_color
        self._hovered = False

        self.setMinimumHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        # 顶部: 图标 + 标题
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"""
                font-size: 18px;
                color: {accent_color};
                background: transparent;
            """)
            top_row.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: #8b99b0;
            background: transparent;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        top_row.addWidget(title_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        # 数值
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-family: "Exo 2";
            font-size: 28px;
            font-weight: 700;
            color: {accent_color};
            background: transparent;
        """)
        layout.addWidget(self.value_label)

        # 副标题
        if subtitle:
            self.sub_label = QLabel(subtitle)
            self.sub_label.setStyleSheet("""
                font-size: 12px;
                color: #4a5c78;
                background: transparent;
            """)
            layout.addWidget(self.sub_label)

        layout.addStretch()

    def set_value(self, value: str, color: str = None):
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"""
                font-family: "Exo 2";
                font-size: 28px;
                font-weight: 700;
                color: {color};
                background: transparent;
            """)

    def _update_style(self):
        self.setStyleSheet(f"""
            StatusCard {{
                background-color: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
                border-top: 2px solid {self.accent};
            }}
            StatusCard:hover {{
                border-color: {self.accent};
                background-color: #162038;
            }}
        """)

    def enterEvent(self, event: QEnterEvent):
        self._hovered = True
        self.setStyleSheet(f"""
            StatusCard {{
                background-color: #162038;
                border: 1px solid {self.accent};
                border-radius: 12px;
                border-top: 2px solid {self.accent};
            }}
        """)

    def leaveEvent(self, event):
        self._hovered = False
        self._update_style()
