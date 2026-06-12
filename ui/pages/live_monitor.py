"""
Live Monitor Page - fixed widget updates
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTextEdit,
)
from PyQt6.QtCore import Qt


class MonitorCard(QFrame):
    """Small status card for live monitor."""

    def __init__(self, title, value="", color="#00b4ff", parent=None):
        super().__init__(parent)
        self._color = color
        self.setStyleSheet("""
            QFrame {{
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 10px;
                border-top: 2px solid {c};
            }}
        """.format(c=color))

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #4a5c78; "
            "background: transparent; text-transform: uppercase; "
            "letter-spacing: 1px;")
        v.addWidget(t)

        self.value_label = QLabel(value)
        self._set_value_style(color)
        v.addWidget(self.value_label)
        v.addStretch()

    def set_value(self, text, color=None):
        self.value_label.setText(str(text))
        if color:
            self._set_value_style(color)

    def _set_value_style(self, color):
        self._color = color
        self.value_label.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 22px; font-weight: 700; "
            "color: {c}; background: transparent;".format(c=color))
        self.setStyleSheet("""
            QFrame {{
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 10px;
                border-top: 2px solid {c};
            }}
        """.format(c=color))


class LiveMonitorPage(QWidget):

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._log_max = 200
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        title = QLabel("\u5b9e\u65f6\u76d1\u63a7")
        title.setObjectName("heading")
        layout.addWidget(title)

        sub = QLabel(
            "\u901a\u8fc7 Game State Integration \u76d1\u542c CS2 \u5b9e\u65f6\u6570\u636e")
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        # ── Monitor cards grid ──
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        self.card_map = MonitorCard("\u5730\u56fe", "\u2014", "#00b4ff")
        self.card_score = MonitorCard("\u6bd4\u5206", "0 : 0", "#ff9f43")
        self.card_round = MonitorCard("\u56de\u5408", "\u2014", "#8b5cf6")

        row1.addWidget(self.card_map)
        row1.addWidget(self.card_score)
        row1.addWidget(self.card_round)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(14)

        self.card_health = MonitorCard("\u8840\u91cf", "\u2014", "#ff3b5c")
        self.card_kda = MonitorCard("K/D/A", "0 / 0 / 0", "#00e68a")
        self.card_phase = MonitorCard("\u9636\u6bb5", "\u2014", "#8b99b0")

        row2.addWidget(self.card_health)
        row2.addWidget(self.card_kda)
        row2.addWidget(self.card_phase)
        layout.addLayout(row2)

        # ── Event log ──
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(16, 12, 16, 12)

        log_title = QLabel("\u4e8b\u4ef6\u65e5\u5fd7")
        log_title.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 13px; font-weight: 600; "
            "color: #8b99b0; background: transparent;")
        log_layout.addWidget(log_title)

        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMinimumHeight(200)
        self.event_log.setStyleSheet("""
            QTextEdit {
                background: #0b1120;
                border: 1px solid #1a2744;
                border-radius: 8px;
                padding: 8px;
                font-family: "Consolas", monospace;
                font-size: 12px;
                color: #8b99b0;
            }
        """)
        log_layout.addWidget(self.event_log)

        layout.addWidget(log_frame)
        layout.addStretch()

    def update_game_state(self, state):
        """Update all cards with current game state."""
        # Map
        self.card_map.set_value(
            state.map_name or "\u2014", "#00b4ff")

        # Score
        self.card_score.set_value(
            "{} : {}".format(state.score_ct, state.score_t), "#ff9f43")

        # Round
        rn = str(state.round_num) if state.round_num > 0 else "\u2014"
        self.card_round.set_value(rn, "#8b5cf6")

        # Health
        hp = state.player_health if state.player_health > 0 else "\u2014"
        hp_color = "#ff3b5c"
        if isinstance(hp, int):
            if hp <= 20:
                hp_color = "#ff3b5c"
            elif hp <= 50:
                hp_color = "#ff9f43"
            else:
                hp_color = "#00e68a"
        self.card_health.set_value(hp, hp_color)

        # KDA
        self.card_kda.set_value(
            "{} / {} / {}".format(
                state.kills, state.deaths, state.assists),
            "#00e68a")

        # Phase
        phase = state.round_phase or state.map_phase or "\u2014"
        self.card_phase.set_value(phase, "#8b99b0")

        # Log last event
        if state.last_event:
            phase_text = state.round_phase or "unknown"
            msg = "[R{}] {} | HP:{} K/D/A:{}/{}/{}".format(
                state.round_num, phase_text,
                state.player_health,
                state.kills, state.deaths, state.assists)
            self._log(msg)

    def _log(self, message):
        self.event_log.append(message)
        sb = self.event_log.verticalScrollBar()
        sb.setValue(sb.maximum())
        # Trim old entries
        doc = self.event_log.document()
        if doc.blockCount() > self._log_max:
            cursor = self.event_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(
                cursor.MoveOperation.Down,
                cursor.MoveMode.KeepAnchor,
                doc.blockCount() - self._log_max)
            cursor.removeSelectedText()
