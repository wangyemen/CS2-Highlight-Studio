"""
侧边导航栏组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QEnterEvent


class NavButton(QPushButton):

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setText("  {}   {}".format(icon, text))
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False
        self._set_inactive_style()

    def set_active(self, active):
        self._active = active
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 180, 255, 0.12);
                    border: none;
                    border-left: 3px solid #00b4ff;
                    border-radius: 0px 8px 8px 0px;
                    padding: 0 13px 0 16px;
                    text-align: left;
                    font-size: 13px;
                    color: #00b4ff;
                    font-weight: 600;
                }
            """)
        else:
            self._set_inactive_style()

    def _set_inactive_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px 8px 8px 0px;
                padding: 0 13px 0 16px;
                text-align: left;
                font-size: 13px;
                color: #8b99b0;
            }
            QPushButton:hover {
                background: #1c2a4a;
                color: #e8edf5;
            }
        """)


class StatusDot(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self.set_status("offline")

    def set_status(self, status):
        colors = {
            "online": "#00e68a",
            "recording": "#ff3b5c",
            "processing": "#ff9f43",
            "offline": "#4a5c78",
        }
        color = colors.get(status, "#4a5c78")
        self.setStyleSheet(
            "background: {c}; border-radius: 4px; "
            "border: 1px solid {c};".format(c=color)
        )


class Sidebar(QWidget):

    page_changed = pyqtSignal(int)

    PAGE_ICONS = ["◉", "◈", "◇", "◆", "▶", "✂", "◎"]
    PAGE_NAMES = [
        "仪表盘", "Demo 库", "集锦编辑",
        "对局记录", "实时监控", "视频剪辑", "设  置",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QWidget {
                background-color: #0b1120;
                border-right: 1px solid #1a2744;
            }
        """)

        self._buttons = []
        self._current = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(60)
        logo_frame.setStyleSheet("border-bottom: 1px solid #1a2744;")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 0, 16, 0)

        logo_icon = QLabel("CS2")
        logo_icon.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 20px; font-weight: 800; "
            "color: #00b4ff; background: transparent;"
        )
        logo_text = QLabel("Highlight Studio")
        logo_text.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 12px; font-weight: 500; "
            "color: #8b99b0; background: transparent;"
        )

        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        layout.addWidget(logo_frame)

        layout.addSpacing(10)

        # 导航按钮
        for i, (icon, name) in enumerate(
            zip(self.PAGE_ICONS, self.PAGE_NAMES)
        ):
            btn = NavButton(icon, name)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav(idx))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 底部状态
        status_frame = QFrame()
        status_frame.setFixedHeight(66)
        status_frame.setStyleSheet("border-top: 1px solid #1a2744;")
        sl = QVBoxLayout(status_frame)
        sl.setContentsMargins(16, 8, 16, 8)
        sl.setSpacing(5)

        obs_row = QHBoxLayout()
        obs_row.setSpacing(8)
        self.obs_dot = StatusDot()
        obs_lbl = QLabel("OBS")
        obs_lbl.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent;"
        )
        self.obs_status = QLabel("未连接")
        self.obs_status.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent;"
        )
        obs_row.addWidget(self.obs_dot)
        obs_row.addWidget(obs_lbl)
        obs_row.addWidget(self.obs_status)
        obs_row.addStretch()
        sl.addLayout(obs_row)

        gsi_row = QHBoxLayout()
        gsi_row.setSpacing(8)
        self.gsi_dot = StatusDot()
        gsi_lbl = QLabel("GSI")
        gsi_lbl.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent;"
        )
        self.gsi_status = QLabel("未启动")
        self.gsi_status.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent;"
        )
        gsi_row.addWidget(self.gsi_dot)
        gsi_row.addWidget(gsi_lbl)
        gsi_row.addWidget(self.gsi_status)
        gsi_row.addStretch()
        sl.addLayout(gsi_row)

        layout.addWidget(status_frame)

        self._on_nav(0)

    def _on_nav(self, index):
        if index == self._current and self._buttons[index]._active:
            return
        self._current = index
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)
        self.page_changed.emit(index)

    def set_obs_status(self, connected, recording=False):
        if connected:
            self.obs_dot.set_status(
                "recording" if recording else "online"
            )
            text = "录制中" if recording else "已连接"
            color = "#ff3b5c" if recording else "#00e68a"
        else:
            self.obs_dot.set_status("offline")
            text = "未连接"
            color = "#4a5c78"
        self.obs_status.setText(text)
        self.obs_status.setStyleSheet(
            "font-size: 11px; color: {}; background: transparent;".format(
                color
            )
        )

    def set_gsi_status(self, active, info=""):
        if active:
            self.gsi_dot.set_status("online")
            self.gsi_status.setText(info or "监听中")
            self.gsi_status.setStyleSheet(
                "font-size: 11px; color: #00e68a; background: transparent;"
            )
        else:
            self.gsi_dot.set_status("offline")
            self.gsi_status.setText("未启动")
            self.gsi_status.setStyleSheet(
                "font-size: 11px; color: #4a5c78; background: transparent;"
            )
