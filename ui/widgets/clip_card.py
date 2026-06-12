"""
集锦片段卡片组件 - 显示单个检测到的高光片段
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt


class ClipCard(QFrame):
    """高光片段卡片"""

    toggled = pyqtSignal(int, bool)  # highlight_id, checked

    TYPE_COLORS = {
        "ace":    ("#ff3b5c", "ACE"),
        "4k":     ("#ff9f43", "4K"),
        "3k":     ("#8b5cf6", "3K"),
        "2k":     ("#00b4ff", "2K"),
        "clutch": ("#00e68a", "CLUTCH"),
        "highlight": ("#8b99b0", "HIGH"),
    }

    def __init__(self, highlight, parent=None):
        super().__init__(parent)
        self.highlight = highlight
        self._checked = True

        color, tag = self.TYPE_COLORS.get(
            highlight.highlight_type, ("#8b99b0", "??")
        )

        self.setMinimumWidth(280)
        self.setMaximumHeight(140)
        self.setStyleSheet(f"""
            ClipCard {{
                background-color: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 10px;
                border-left: 3px solid {color};
            }}
            ClipCard:hover {{
                border-color: {color};
                background-color: #162038;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # 左侧: 选中框 + 类型标签
        left = QVBoxLayout()
        left.setSpacing(6)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self._on_toggle)
        self.checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                border: 2px solid {color};
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {color};
                border-color: {color};
            }}
        """)
        left.addWidget(self.checkbox)

        tag_label = QLabel(tag)
        tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_label.setFixedWidth(52)
        tag_label.setStyleSheet(f"""
            font-family: "Exo 2";
            font-size: 13px;
            font-weight: 800;
            color: {color};
            background: rgba({self._hex_to_rgb(color)}, 0.12);
            border-radius: 4px;
            padding: 4px;
        """)
        left.addWidget(tag_label)
        left.addStretch()
        layout.addLayout(left)

        # 中间: 信息
        info = QVBoxLayout()
        info.setSpacing(4)

        # 玩家名
        player_label = QLabel(highlight.player)
        player_label.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 15px;
            font-weight: 600;
            color: #e8edf5;
            background: transparent;
        """)
        info.addWidget(player_label)

        # 描述
        desc_label = QLabel(highlight.description)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #8b99b0;
            background: transparent;
        """)
        info.addWidget(desc_label)

        # 时间信息
        time_text = (
            f"{highlight.start_seconds:.1f}s - {highlight.end_seconds:.1f}s "
            f"({highlight.duration_seconds:.1f}s)"
        )
        time_label = QLabel(time_text)
        time_label.setStyleSheet("""
            font-family: "JetBrains Mono", "Consolas", monospace;
            font-size: 11px;
            color: #4a5c78;
            background: transparent;
        """)
        info.addWidget(time_label)

        info.addStretch()
        layout.addLayout(info)

        # 右侧: 分数
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        score_label = QLabel(str(int(highlight.score)))
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_label.setStyleSheet(f"""
            font-family: "Exo 2";
            font-size: 22px;
            font-weight: 700;
            color: {color};
            background: transparent;
        """)
        right.addWidget(score_label)

        pts_label = QLabel("SCORE")
        pts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pts_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
            color: #4a5c78;
            background: transparent;
        """)
        right.addWidget(pts_label)
        right.addStretch()
        layout.addLayout(right)

    def _on_toggle(self, state):
        self._checked = state == 2
        self.toggled.emit(self.highlight.highlight_id, self._checked)

    @property
    def is_checked(self):
        return self._checked

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
