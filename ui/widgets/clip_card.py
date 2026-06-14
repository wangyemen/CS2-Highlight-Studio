"""
Clip card widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt


class ClipCard(QFrame):

    toggled = pyqtSignal(int, bool)

    TYPE_COLORS = {
        "ace":        ("#ff3b5c", "ACE"),
        "4k":         ("#ff9f43", "4K"),
        "3k":         ("#8b5cf6", "3K"),
        "2k":         ("#00b4ff", "2K"),
        "clutch":     ("#00e68a", "CLUTCH"),
        "highlight":  ("#8b99b0", "HIGH"),
        "kill":       ("#4a5c78", "KILL"),
    }

    def __init__(self, highlight, parent=None):
        super().__init__(parent)
        self.highlight = highlight
        self._checked = True

        color, tag = self.TYPE_COLORS.get(
            highlight.highlight_type,
            ("#8b99b0", "??"))

        self.setMinimumWidth(280)
        self.setMaximumHeight(140)
        self.setStyleSheet(
            "ClipCard {{"
            "background-color: #111a2e;"
            "border: 1px solid #1a2744;"
            "border-radius: 10px;"
            "border-left: 3px solid {c};"
            "}}"
            "ClipCard:hover {{"
            "border-color: {c};"
            "background-color: #162038;"
            "}}".format(c=color))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            14, 12, 14, 12)
        layout.setSpacing(14)

        # Left: checkbox + tag
        left = QVBoxLayout()
        left.setSpacing(6)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(
            self._on_toggle)
        rgb = self._hex_to_rgb(color)
        self.checkbox.setStyleSheet(
            "QCheckBox::indicator {{"
            "width: 18px; height: 18px;"
            "border-radius: 4px;"
            "border: 2px solid {c};"
            "background: transparent;"
            "}}"
            "QCheckBox::indicator:checked {{"
            "background: {c};"
            "border-color: {c};"
            "}}".format(c=color))
        left.addWidget(self.checkbox)

        tag_label = QLabel(tag)
        tag_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        tag_label.setFixedWidth(52)
        tag_label.setStyleSheet(
            'font-family: "Exo 2";'
            "font-size: 13px;"
            "font-weight: 800;"
            "color: {c};"
            "background: rgba({rgb}, 0.12);"
            "border-radius: 4px;"
            "padding: 4px;".format(
                c=color, rgb=rgb))
        left.addWidget(tag_label)
        left.addStretch()
        layout.addLayout(left)

        # Center: info
        info = QVBoxLayout()
        info.setSpacing(4)

        player_label = QLabel(highlight.player)
        player_label.setStyleSheet(
            'font-family: "Exo 2";'
            "font-size: 15px;"
            "font-weight: 600;"
            "color: #e8edf5;"
            "background: transparent;")
        info.addWidget(player_label)

        desc_label = QLabel(
            highlight.description)
        desc_label.setStyleSheet(
            "font-size: 12px;"
            "color: #8b99b0;"
            "background: transparent;")
        info.addWidget(desc_label)

        time_text = (
            "{:.1f}s - {:.1f}s "
            "({:.1f}s)".format(
                highlight.start_seconds,
                highlight.end_seconds,
                highlight.duration_seconds))
        time_label = QLabel(time_text)
        time_label.setStyleSheet(
            'font-family: "JetBrains Mono", '
            '"Consolas", monospace;'
            "font-size: 11px;"
            "color: #4a5c78;"
            "background: transparent;")
        info.addWidget(time_label)

        info.addStretch()
        layout.addLayout(info)

        # Right: score
        right = QVBoxLayout()
        right.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

        score_label = QLabel(
            str(int(highlight.score)))
        score_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        score_label.setStyleSheet(
            'font-family: "Exo 2";'
            "font-size: 22px;"
            "font-weight: 700;"
            "color: {c};"
            "background: transparent;".format(
                c=color))
        right.addWidget(score_label)

        pts_label = QLabel("SCORE")
        pts_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        pts_label.setStyleSheet(
            "font-size: 10px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            "color: #4a5c78;"
            "background: transparent;")
        right.addWidget(pts_label)
        right.addStretch()
        layout.addLayout(right)

    def _on_toggle(self, state):
        self._checked = state == 2
        self.toggled.emit(
            self.highlight.highlight_id,
            self._checked)

    @property
    def is_checked(self):
        return self._checked

    @staticmethod
    def _hex_to_rgb(hex_color):
        h = hex_color.lstrip("#")
        r, g, b = (
            int(h[:2], 16),
            int(h[2:4], 16),
            int(h[4:6], 16))
        return "{}, {}, {}".format(r, g, b)
